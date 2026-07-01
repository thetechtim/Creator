# 🎭 Discord Rollen-Bot

Ein Discord-Bot für **Reaktions-basierte Rollenvergabe** mit optionalem **Moderator-Genehmigungssystem**.

---

## ✨ Features

| Feature | Beschreibung |
|---|---|
| 🎭 Reaktions-Rollen | Mitglieder reagieren auf eine Nachricht → Rolle wird vergeben |
| ✅ Sofort-Rollen | Bestimmte Rollen werden direkt ohne Genehmigung vergeben |
| ⚠️ Genehmigungs-Rollen | Anfrage geht an Moderatoren → die können genehmigen oder ablehnen |
| 🔔 DM-Benachrichtigungen | Mitglieder werden per DM über den Status informiert |
| 🔄 Rolle abgeben | Reaktion entfernen → Rolle wird abgezogen |
| 📋 Ausstehende Anfragen | Mods können offene Anfragen einsehen (`!pending`) |

---

## ⚙️ Einrichtung

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 2. Bot auf Discord erstellen
1. Gehe zu https://discord.com/developers/applications
2. Erstelle eine neue Application → Bot hinzufügen
3. Aktiviere unter **Privileged Gateway Intents**:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
4. Lade den Bot ein mit diesen Berechtigungen:
   - `Manage Roles`, `Send Messages`, `Add Reactions`,
   - `Read Message History`, `View Channels`

### 3. `config.py` anpassen

```python
# Bot-Token (oder als Umgebungsvariable DISCORD_TOKEN)
TOKEN = "DEIN_TOKEN_HIER"

# ID des Mod-Kanals (Rechtsklick auf Kanal → ID kopieren)
MOD_CHANNEL_ID = 123456789012345678

# Name der Moderator-Rolle auf deinem Server
MOD_ROLE_NAME = "Moderator"
```

### 4. Rollen konfigurieren

In `config.py` unter `ROLES` kannst du beliebige Rollen hinzufügen:

```python
ROLES = {
    "🎮": {
        "name": "Gamer",          # Exakter Name der Discord-Rolle
        "needs_approval": False,   # Sofort vergeben
    },
    "🛡️": {
        "name": "Trusted Member",
        "needs_approval": True,    # Moderator muss genehmigen
    },
}
```

> ⚠️ **Wichtig:** Die Rollen müssen auf dem Discord-Server bereits existieren!

### 5. Bot starten

```bash
python bot.py
# oder mit Umgebungsvariable:
DISCORD_TOKEN=dein_token python bot.py
```

---

## 🚀 Befehle

| Befehl | Berechtigung | Beschreibung |
|---|---|---|
| `!setup_roles` | Administrator | Erstellt die Rollen-Auswahl-Nachricht im aktuellen Kanal |
| `!pending` | Manage Roles | Zeigt alle offenen Genehmigungsanfragen |
| `!role_help` | Jeder | Zeigt Hilfe für das Rollensystem |

---

## 🔄 Ablauf

### Sofort-Rollen
```
Mitglied reagiert → Rolle wird sofort vergeben → DM an Mitglied
```

### Genehmigungs-Rollen
```
Mitglied reagiert
    → DM: "Deine Anfrage wurde eingereicht"
    → Nachricht im Mod-Kanal erscheint (✅ / ❌)
    
Moderator reagiert mit ✅
    → Rolle wird vergeben
    → DM: "Wurde genehmigt"
    
Moderator reagiert mit ❌
    → Reaktion wird vom Mitglied entfernt
    → DM: "Wurde abgelehnt"
```

### Rolle abgeben
```
Mitglied entfernt Reaktion → Rolle wird entfernt → DM an Mitglied
(Offene Anfragen werden dabei automatisch abgebrochen)
```

---

## 📁 Dateistruktur

```
Creator/
├── bot.py           # Hauptlogik des Bots
├── config.py        # Konfiguration (Token, Rollen, Kanal-IDs)
├── requirements.txt # Python-Abhängigkeiten
├── data.json        # Automatisch erstellt – speichert Nachrichten & Anfragen
└── README.md        # Diese Datei
```

---

## 💡 Tipps

- Der Bot braucht eine **höhere Rollenposition** als die Rollen, die er vergeben soll
- `data.json` wird automatisch erstellt – nicht löschen, solange der Bot läuft
- Für mehrere Rollen-Nachrichten einfach `!setup_roles` in verschiedenen Kanälen nutzen