# 🍓 Raspberry Pi 4B – Ultimativer Minecraft SMP Discord Bot

Ein hochmoderner, multifunktionaler Discord Bot in Python (`discord.py` v2), der speziell für private und Community **Minecraft SMP-Server** entwickelt wurde und direkt als stabiler `systemd`-Hintergrunddienst auf deinem **Raspberry Pi 4B** läuft.

---

## 🔗 Bot zum Discord-Server einladen

👉 **[Hier klicken: Bot zu deinem Discord-Server einladen](https://discord.com/oauth2/authorize?client_id=1542492252373258260&permissions=8&scope=bot%20applications.commands)**

---

## 🌟 Funktionsübersicht

### 1. ⚙️ Vollautomatisches Discord-Server-Setup
- `/setup-smp [server_name]` – Erstellt in Sekunden die perfekte SMP-Serverstruktur mit sortierten Kategorien, Text- & Voice-Kanälen, Rollen und formatierten Regel- & Info-Embeds.
- `/setup-roles` – Sendet ein interaktives Rollen-Auswahl-Panel mit Buttons (z.B. 🔔 Ankündigungen, ⛏️ Minenarbeiter, 🏗️ Baumeister, ⚔️ Krieger, ⚡ Redstone-Ingenieur).
- `/setup-whitelist-button` – Startet das interaktive Whitelist-Bewerbungssystem (Spieler klicken auf den Button $\rightarrow$ tragen ihren Ingame-Namen im Modal-Formular ein $\rightarrow$ Admins können mit 1 Klick annehmen/ablehnen).

### 2. 🟢 Live Minecraft-Server-Status & Monitoring
- `/mcstatus [ip] [port]` – Live-Statusabfrage für Java & Bedrock (Ping, MOTD, Spieler online/max, Version, Server-Icon).
- `/mcplayers` – Zeigt eine Liste aller aktuell eingeloggten Spieler auf dem SMP an.
- `/set-server-ip <ip> [port]` – Speichert die Standard-IP deines SMP-Servers in der persistenten SQLite-Datenbank.

### 3. 📍 Wegpunkte & Koordinaten-Manager mit Portal-Rechner
- `/coords add <name> <x> <z> [y] [dimension] [info]` – Speichert Basen, Farmen, Festungen & Portale.
- `/coords list [dimension]` – Interaktive Liste mit Dropdown-Menü zur Anzeige von Koordinaten und automatischer Nether-/Overworld-Umrechnung.
- `/coords nether-calc <x> <z> [von]` – Berechnet sofort die exakten Portal-Koordinaten ($X \div 8, Z \div 8$ bzw. $X \times 8, Z \times 8$) für perfekte Nether-Links.

### 4. 💎 SMP Marktplatz & Wirtschaftssystem
- `/shop add <item> <preis> <ort> [menge]` – Erstelle ein Verkaufsangebot im Marktplatz.
- `/shop list` – Durchstöbere alle Angebote der Mitspieler inklusive Verfügbarkeits-Status.
- `/shop search <item>` – Finde heraus, wer z.B. *Mending-Bücher* oder *Elytren* verkauft.
- `/shop delete <id>` – Entferne dein Angebot.

### 5. 🎨 Spieler & Skin Tools (3D Renderings)
- `/skin <name>` – Zeigt das vollständige 3D-Modell, Büste, Kopf und Skin-Download eines Spielers an.
- `/player <name>` – Vollständiges Mojang-Profil mit UUID, NameMC-Link und Ingame-Kopfbefehl.
- `/head <name>` – Gibt den passenden `/give` Befehl für den Kopf des Spielers aus.

### 6. 🧪 Material-Rechner & Minecraft-Guides
- `/calc-blocks <länge> <breite> <höhe> [hohl]` – Berechnet exakt benötigte Blöcke, Stacks, Shulkerkisten und Doppelkisten für Bauprojekte.
- `/enchant-guide <item>` – Zeigt die besten God-Roll-Verzauberungen für Schwert, Streitkolben, Rüstung, Spitzhacke, Elytra usw.
- `/potion-guide <trank>` – Schritt-für-Schritt Braurezepte für Schnelligkeit, Stärke, Nachtsicht, Sanfter Fall & Heilung.

### 7. 🍓 Raspberry Pi 4B Hardware-Telemetrie
- `/status` – Live CPU-Auslastung, CPU-Temperatur, RAM-Belegung, SD-Karten-Speicher, Uptime und Ping.
- `/ping` – Schnelle Bot-Latenzprüfung.
- `/help` – Interaktives Dropdown-Hilfsmenü mit allen Befehlen und Kategorien.

---

## 🛠️ Verwaltung & Wartung

| Befehl | Ausführung |
| :--- | :--- |
| **Änderungen auf den Pi übertragen** | `./deploy.sh` |
| **Bot-Status prüfen** | `ssh admin@192.168.178.94 "systemctl status discord-bot"` |
| **Bot neu starten** | `ssh admin@192.168.178.94 "sudo systemctl restart discord-bot"` |
| **Live-Logs ansehen** | `ssh admin@192.168.178.94 "journalctl -u discord-bot -f"` |
