import discord
from discord.ext import commands
import json
import os
import asyncio
from config import Config

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─────────────────────────────────────────────
#  Datenpersistenz
# ─────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"role_messages": {}, "pending_requests": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────
#  Bot Ready
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅  Bot ist online als {bot.user}")
    print(f"📋  Geladene Rollen-Nachrichten: {len(load_data()['role_messages'])}")

# ─────────────────────────────────────────────
#  Setup-Command – Erstellt die Rollen-Nachricht
# ─────────────────────────────────────────────
@bot.command(name="setup_roles")
@commands.has_permissions(administrator=True)
async def setup_roles(ctx):
    """Erstellt die Rollen-Auswahl-Nachricht im aktuellen Kanal."""
    data = load_data()

    embed = discord.Embed(
        title="🎭 Rollen auswählen",
        description="Reagiere mit dem passenden Emoji, um eine Rolle zu erhalten.\n"
                    "**⚠️ Markierte Rollen** benötigen eine Moderator-Genehmigung.\n\n",
        color=discord.Color.blurple()
    )

    role_lines = []
    for emoji, role_cfg in Config.ROLES.items():
        needs_approval = "⚠️ *Genehmigung nötig*" if role_cfg["needs_approval"] else "✅ *Sofort*"
        role_lines.append(f"{emoji}  **{role_cfg['name']}** — {needs_approval}")
    
    embed.description += "\n".join(role_lines)
    embed.set_footer(text="Reaktion entfernen = Rolle abgeben")

    msg = await ctx.send(embed=embed)

    # Emojis zur Nachricht hinzufügen
    for emoji in Config.ROLES:
        await msg.add_reaction(emoji)

    # Nachricht in Daten speichern
    data["role_messages"][str(msg.id)] = {
        "channel_id": ctx.channel.id,
        "guild_id": ctx.guild.id
    }
    save_data(data)
    await ctx.message.delete()

# ─────────────────────────────────────────────
#  Reaktion hinzugefügt
# ─────────────────────────────────────────────
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    data = load_data()
    if str(payload.message_id) not in data["role_messages"]:
        return

    emoji = str(payload.emoji)
    if emoji not in Config.ROLES:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    role_cfg = Config.ROLES[emoji]
    role = discord.utils.get(guild.roles, name=role_cfg["name"])
    if role is None:
        print(f"⚠️  Rolle '{role_cfg['name']}' nicht gefunden! Bitte erstelle sie zuerst.")
        return

    if role_cfg["needs_approval"]:
        await handle_approval_request(guild, member, role, emoji, data, payload.message_id)
    else:
        await member.add_roles(role)
        try:
            await member.send(
                f"✅ Du hast die Rolle **{role.name}** auf **{guild.name}** erhalten!"
            )
        except discord.Forbidden:
            pass

# ─────────────────────────────────────────────
#  Reaktion entfernt
# ─────────────────────────────────────────────
@bot.event
async def on_raw_reaction_remove(payload):
    data = load_data()
    if str(payload.message_id) not in data["role_messages"]:
        return

    emoji = str(payload.emoji)
    if emoji not in Config.ROLES:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    role_cfg = Config.ROLES[emoji]
    role = discord.utils.get(guild.roles, name=role_cfg["name"])
    if role is None:
        return

    # Ausstehende Anfragen löschen, falls vorhanden
    request_key = f"{payload.user_id}_{role_cfg['name']}"
    if request_key in data.get("pending_requests", {}):
        req = data["pending_requests"].pop(request_key)
        save_data(data)
        # Genehmigungsnachricht löschen
        try:
            mod_channel = guild.get_channel(Config.MOD_CHANNEL_ID)
            if mod_channel:
                msg = await mod_channel.fetch_message(req["mod_message_id"])
                await msg.delete()
        except Exception:
            pass
        try:
            await member.send(f"🚫 Deine Anfrage für **{role.name}** wurde zurückgezogen.")
        except discord.Forbidden:
            pass
        return

    if role in member.roles:
        await member.remove_roles(role)
        try:
            await member.send(f"❌ Die Rolle **{role.name}** wurde dir auf **{guild.name}** entfernt.")
        except discord.Forbidden:
            pass

# ─────────────────────────────────────────────
#  Genehmigungsanfrage senden
# ─────────────────────────────────────────────
async def handle_approval_request(guild, member, role, emoji, data, role_message_id):
    request_key = f"{member.id}_{role.name}"

    # Doppelte Anfragen verhindern
    if request_key in data.get("pending_requests", {}):
        try:
            await member.send(
                f"⏳ Deine Anfrage für **{role.name}** ist bereits in Bearbeitung. Bitte warte auf eine Antwort."
            )
        except discord.Forbidden:
            pass
        return

    mod_channel = guild.get_channel(Config.MOD_CHANNEL_ID)
    if mod_channel is None:
        print(f"⚠️  Moderator-Kanal (ID: {Config.MOD_CHANNEL_ID}) nicht gefunden!")
        return

    embed = discord.Embed(
        title="📋 Rollen-Anfrage",
        description=f"**{member.mention}** möchte die Rolle **{role.mention}** erhalten.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Benutzer", value=f"{member} (ID: {member.id})", inline=True)
    embed.add_field(name="Rolle", value=role.name, inline=True)
    embed.add_field(name="Emoji", value=emoji, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"✅ Genehmigen  |  ❌ Ablehnen")

    mod_msg = await mod_channel.send(embed=embed)
    await mod_msg.add_reaction("✅")
    await mod_msg.add_reaction("❌")

    # Anfrage speichern
    if "pending_requests" not in data:
        data["pending_requests"] = {}

    data["pending_requests"][request_key] = {
        "user_id": member.id,
        "role_name": role.name,
        "guild_id": guild.id,
        "mod_message_id": mod_msg.id,
        "role_message_id": role_message_id,
        "emoji": emoji
    }
    save_data(data)

    try:
        await member.send(
            f"⏳ Deine Anfrage für die Rolle **{role.name}** auf **{guild.name}** wurde eingereicht "
            f"und wartet auf Genehmigung durch einen Moderator."
        )
    except discord.Forbidden:
        pass

# ─────────────────────────────────────────────
#  Moderator-Reaktion (Genehmigen / Ablehnen)
# ─────────────────────────────────────────────
@bot.event
async def on_raw_reaction_add_mod(payload):
    pass  # Wird unten durch on_raw_reaction_add mit abgedeckt

@bot.listen("on_raw_reaction_add")
async def mod_reaction_handler(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    mod_channel = guild.get_channel(Config.MOD_CHANNEL_ID)
    if mod_channel is None or payload.channel_id != Config.MOD_CHANNEL_ID:
        return

    # Prüfen ob reagierende Person Moderator-Rolle hat
    moderator = guild.get_member(payload.user_id)
    if moderator is None:
        return

    mod_role = discord.utils.get(guild.roles, name=Config.MOD_ROLE_NAME)
    if mod_role not in moderator.roles and not moderator.guild_permissions.administrator:
        # Reaktion entfernen, falls keine Berechtigung
        try:
            msg = await mod_channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, moderator)
        except Exception:
            pass
        return

    emoji = str(payload.emoji)
    if emoji not in ("✅", "❌"):
        return

    data = load_data()

    # Zugehörige Anfrage finden
    request_key = None
    request_data = None
    for key, req in data.get("pending_requests", {}).items():
        if req["mod_message_id"] == payload.message_id:
            request_key = key
            request_data = req
            break

    if request_key is None:
        return

    member = guild.get_member(request_data["user_id"])
    role = discord.utils.get(guild.roles, name=request_data["role_name"])

    # Anfrage aus den Daten entfernen
    del data["pending_requests"][request_key]
    save_data(data)

    # Mod-Nachricht aktualisieren
    try:
        mod_msg = await mod_channel.fetch_message(payload.message_id)
        await mod_msg.clear_reactions()

        if emoji == "✅":
            # Rolle vergeben
            if member and role:
                await member.add_roles(role)
                new_embed = mod_msg.embeds[0]
                new_embed.color = discord.Color.green()
                new_embed.set_footer(text=f"✅ Genehmigt von {moderator}")
                await mod_msg.edit(embed=new_embed)
                try:
                    await member.send(
                        f"🎉 Deine Anfrage für die Rolle **{role.name}** auf **{guild.name}** wurde genehmigt!"
                    )
                except discord.Forbidden:
                    pass
            await asyncio.sleep(10)
            await mod_msg.delete()

        elif emoji == "❌":
            # Reaktion vom Benutzer entfernen
            try:
                role_channel_id = data["role_messages"].get(
                    str(request_data.get("role_message_id", "")), {}
                ).get("channel_id")
                if role_channel_id:
                    role_channel = guild.get_channel(role_channel_id)
                    if role_channel:
                        role_msg = await role_channel.fetch_message(request_data["role_message_id"])
                        await role_msg.remove_reaction(request_data["emoji"], member)
            except Exception as e:
                print(f"Konnte Reaktion nicht entfernen: {e}")

            new_embed = mod_msg.embeds[0]
            new_embed.color = discord.Color.red()
            new_embed.set_footer(text=f"❌ Abgelehnt von {moderator}")
            await mod_msg.edit(embed=new_embed)
            try:
                await member.send(
                    f"❌ Deine Anfrage für die Rolle **{role.name}** auf **{guild.name}** wurde abgelehnt."
                )
            except discord.Forbidden:
                pass
            await asyncio.sleep(10)
            await mod_msg.delete()

    except Exception as e:
        print(f"Fehler bei Moderator-Reaktion: {e}")

# ─────────────────────────────────────────────
#  Hilfsbefehle
# ─────────────────────────────────────────────
@bot.command(name="pending")
@commands.has_permissions(manage_roles=True)
async def list_pending(ctx):
    """Zeigt alle ausstehenden Anfragen."""
    data = load_data()
    pending = data.get("pending_requests", {})

    if not pending:
        await ctx.send("✅ Keine ausstehenden Anfragen.")
        return

    embed = discord.Embed(title="⏳ Ausstehende Anfragen", color=discord.Color.orange())
    for key, req in pending.items():
        member = ctx.guild.get_member(req["user_id"])
        embed.add_field(
            name=f"{member or 'Unbekannt'} → {req['role_name']}",
            value=f"ID: {req['user_id']}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name="role_help")
async def role_help(ctx):
    """Zeigt die Hilfe für das Rollensystem."""
    embed = discord.Embed(title="❓ Rollensystem – Hilfe", color=discord.Color.blue())
    embed.add_field(
        name="Wie bekomme ich eine Rolle?",
        value="Gehe in den Rollen-Kanal und reagiere auf die Nachricht mit dem gewünschten Emoji.",
        inline=False
    )
    embed.add_field(
        name="Wie gebe ich eine Rolle ab?",
        value="Entferne deine Reaktion von der Nachricht.",
        inline=False
    )
    embed.add_field(
        name="Warum muss ich warten?",
        value="Manche Rollen benötigen die Genehmigung eines Moderators.",
        inline=False
    )
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
#  Bot starten
# ─────────────────────────────────────────────
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN") or Config.TOKEN
    if not token:
        print("❌ Kein Bot-Token gefunden! Setze DISCORD_TOKEN oder trage ihn in config.py ein.")
    else:
        bot.run(token)