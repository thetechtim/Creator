import os

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("CREATOR_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="!ping | /hello")
    )

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} Slash Commands synchronisiert.")
    except Exception as e:
        print(e)

    print(f"Angemeldet als {bot.user}")

# -----------------
# Präfix-Befehl
# !ping
# -----------------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# -----------------
# Slash Command
# /hello
# -----------------
@bot.tree.command(name="hello", description="Sagt Hallo.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("👋 Hallo!")

bot.run(TOKEN)