# ══════════════════════════════════════════════
#  config.py  –  Konfiguration des Rollen-Bots
# ══════════════════════════════════════════════
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

class Config:

    # ── Bot-Token ──────────────────────────────
    # Trage hier deinen Token ein ODER setze die
    # Umgebungsvariable DISCORD_TOKEN (empfohlen).
    TOKEN = TOKEN

    # ── Moderator-Kanal ────────────────────────
    # ID des Kanals, in dem Genehmigungsanfragen erscheinen.
    MOD_CHANNEL_ID = 123456789012345678   # ← ANPASSEN

    # ── Moderator-Rolle ────────────────────────
    # Nur Mitglieder mit dieser Rolle können genehmigen/ablehnen.
    MOD_ROLE_NAME = "Moderator"           # ← ANPASSEN

    # ── Rollen-Konfiguration ───────────────────
    # Emoji → Rollen-Einstellungen
    #
    # name            : Exakter Name der Discord-Rolle
    # needs_approval  : True  = Moderator muss genehmigen
    #                   False = Wird sofort vergeben
    #
    ROLES = {
        # ── Sofort-Rollen ──────────────────────
        "🎮": {
            "name": "Gamer",
            "needs_approval": False,
        },
        "🎵": {
            "name": "Musik",
            "needs_approval": False,
        },
        "📢": {
            "name": "Ankündigungen",
            "needs_approval": False,
        },
        "🎨": {
            "name": "Kreativ",
            "needs_approval": False,
        },

        # ── Genehmigungs-Rollen ────────────────
        "🛡️": {
            "name": "Trusted Member",
            "needs_approval": True,
        },
        "🎤": {
            "name": "Content Creator",
            "needs_approval": True,
        },
        "⚙️": {
            "name": "Beta Tester",
            "needs_approval": True,
        },
    }