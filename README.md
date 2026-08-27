# 🍓 Raspberry Pi 4B - Minecraft SMP Discord Bot

Ein moderner, performanter Discord Bot in Python (`discord.py` v2), der direkt als systemd-Hintergrunddienst auf dem Raspberry Pi 4B läuft und deinen Discord-Server automatisch für dein **Minecraft SMP-Projekt** einrichtet.

---

## 🔗 Bot zum Discord-Server hinzufügen

Klicke einfach auf den folgenden Link, um den Bot mit Administrator-Rechten zu deinem Discord-Server hinzuzufügen:

👉 **[Hier klicken: Bot zu deinem Discord-Server einladen](https://discord.com/oauth2/authorize?client_id=1542492252373258260&permissions=8&scope=bot%20applications.commands)**

---

## 🛠️ SMP Auto-Setup

Sobald der Bot auf deinem Server ist, führe einfach den folgenden Slash-Befehl aus:
```
/setup-smp server_name:"Mein Minecraft SMP"
```

Der Bot erstellt vollautomatisch:
1. **Rollen mit Farben:**
   - 👑 `Admin`
   - 🛡️ `Moderator`
   - ⛏️ `SMP Member`
   - 🔔 `Ankündigungen`
2. **Kategorien & Textkanäle:**
   - 📌 **WILLKOMMEN & INFO:** `#📜-regeln` (mit fertigen SMP-Regeln), `#📢-ankündigungen`, `#ℹ️-server-info` (mit Server-IP, Version & Whitelist-Info)
   - 💬 **COMMUNITY:** `#💬-allgemein`, `#⛏️-smp-talk`, `#📸-screenshots-clips`, `#🤖-bot-befehle`
   - 🤝 **HANDEL & PROJEKTE:** `#🛒-shops-und-handel`, `#🏗️-bauprojekte`, `#📍-koordinaten`
3. **Sprachkanäle:**
   - `🔊 Talk 1`, `🔊 Talk 2`, `⛏️ Mining & Farmen`, `⚔️ Bossfight / End`, `💤 AFK`

---

## 🎮 Alle verfügbaren Befehle

| Befehl | Berechtigung | Beschreibung |
| :--- | :--- | :--- |
| `/setup-smp [name]` | Admin | Richtet den Discord-Server automatisch für das Minecraft SMP ein. |
| `/smp-info [ip] [version]` | Jeder | Zeigt oder teilt die Server-IP, Version und Dynmap-Link. |
| `/status` | Jeder | Zeigt CPU-Temperatur, RAM, Festplatte und Uptime des Raspberry Pi 4B an. |
| `/ping` | Jeder | Zeigt die aktuelle Websocket-Latenz des Bots an. |
| `/info` | Jeder | Allgemeine Bot- und Systeminformationen. |
| `/say <nachricht>` | Jeder | Lässt den Bot eine Nachricht wiederholen. |
| `/help` | Jeder | Zeigt die Hilfsübersicht im Chat. |

---

## 🔧 Verwaltung auf dem Raspberry Pi (SSH)

| Aktion | Befehl |
| :--- | :--- |
| **Status prüfen** | `ssh admin@192.168.178.94 "systemctl status discord-bot"` |
| **Bot neu starten** | `ssh admin@192.168.178.94 "sudo systemctl restart discord-bot"` |
| **Live-Logs ansehen** | `ssh admin@192.168.178.94 "journalctl -u discord-bot -f"` |
| **Änderungen deployen** | `./deploy.sh` |
