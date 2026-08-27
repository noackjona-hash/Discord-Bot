# 🍓 Raspberry Pi 4B - Discord Bot

Ein moderner, performanter Discord Bot in Python (`discord.py` v2), der direkt als systemd-Hintergrunddienst auf dem Raspberry Pi 4B läuft.

---

## 📋 Features

- ⚡ **Slash Commands & Prefix-Befehle** (`/ping`, `/status`, `/info`, `/say`, `/help` sowie `!ping`, `!status`, etc.)
- 🍓 **Raspberry Pi Telemetrie** (`/status` zeigt CPU-Auslastung, CPU-Temperatur, RAM, SD-Karten-Speicher und System-Uptime)
- 🔄 **Autostart via systemd** (Automatischer Start beim Booten des Pi und automatischer Neustart bei Abstürzen)
- 🚀 **1-Klick Deployment** (Mit `./deploy.sh` werden alle Änderungen automatisch auf den Pi übertragen)

---

## 🛠️ Schnellstart-Anleitung

### 1. Discord Bot Token erstellen (falls noch nicht vorhanden)
1. Gehe auf das [Discord Developer Portal](https://discord.com/developers/applications).
2. Klicke oben rechts auf **"New Application"** und gib dem Bot einen Namen.
3. Gehe im linken Menü auf den Reiter **"Bot"**.
4. Klicke auf **"Reset Token"** (bzw. "View Token") und kopiere den Token.
5. Scrolle auf der Bot-Seite nach unten zu **"Privileged Gateway Intents"** und aktiviere:
   - ✅ **Message Content Intent**
   - ✅ **Server Members Intent** (optional)
6. Klicke unten auf **"Save Changes"**.

### 2. Bot auf deinen Discord-Server einladen
1. Gehe im Developer Portal auf den Reiter **"OAuth2"** -> **"URL Generator"**.
2. Wähle unter **Scopes**:
   - `bot`
   - `applications.commands`
3. Wähle unter **Bot Permissions**:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Use Slash Commands`
4. Kopiere die generierte URL ganz unten und öffne sie im Browser, um den Bot deinem Server hinzuzufügen.

### 3. Token eintragen & Bot starten
Trage deinen kopierten Token in die `.env`-Datei ein:
```env
DISCORD_TOKEN=dein_kopierter_token_hier
```

Führe danach einfach das Deployment-Skript aus:
```bash
./deploy.sh
```

Starte den Dienst auf dem Raspberry Pi:
```bash
ssh admin@192.168.178.94 "sudo systemctl restart discord-bot"
```

---

## 🎮 Verfügbare Befehle

| Slash-Command | Prefix-Befehl | Beschreibung |
| :--- | :--- | :--- |
| `/ping` | `!ping` | Zeigt die aktuelle Websocket-Latenz des Bots in Millisekunden an. |
| `/status` | `!status` oder `!pi` | Zeigt CPU-Last, CPU-Temperatur, RAM, Festplatte und Uptime des Raspberry Pi 4B an. |
| `/info` | `!info` | Zeigt allgemeine Bot- und Systeminformationen. |
| `/say <nachricht>` | - | Lässt den Bot eine Nachricht wiederholen. |
| `/help` | `!help` | Zeigt die Hilfsübersicht im Chat. |

---

## 🔧 Verwaltung auf dem Raspberry Pi (SSH)

| Aktion | Befehl |
| :--- | :--- |
| **Status prüfen** | `ssh admin@192.168.178.94 "systemctl status discord-bot"` |
| **Bot starten** | `ssh admin@192.168.178.94 "sudo systemctl start discord-bot"` |
| **Bot stoppen** | `ssh admin@192.168.178.94 "sudo systemctl stop discord-bot"` |
| **Bot neu starten** | `ssh admin@192.168.178.94 "sudo systemctl restart discord-bot"` |
| **Live-Logs ansehen** | `ssh admin@192.168.178.94 "journalctl -u discord-bot -f"` |
| **Letzte Logs prüfen** | `ssh admin@192.168.178.94 "journalctl -u discord-bot -n 50 --no-pager"` |
