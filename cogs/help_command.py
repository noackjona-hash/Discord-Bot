import discord
from discord import app_commands
from discord.ext import commands

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎮 Minecraft & SMP Status", description="Server-Ping, Online-Spieler, Live-Abfrage", emoji="🟢", value="mc"),
            discord.SelectOption(label="📍 Koordinaten & Wegpunkte", description="Orte speichern, Liste & Nether-Portal-Rechner", emoji="📍", value="coords"),
            discord.SelectOption(label="🛒 Marktplatz & Handel", description="Items verkaufen, suchen & kaufen", emoji="💎", value="shop"),
            discord.SelectOption(label="👤 Spieler & Skins", description="3D Skin Renders, Profile & Köpfe", emoji="🎨", value="player"),
            discord.SelectOption(label="📐 Rechner & Guides", description="Bauprojekt-Material, Verzauberungen, Tränke", emoji="🧪", value="tools"),
            discord.SelectOption(label="🛠️ Server-Setup & Whitelist", description="SMP Discord-Server einrichten, Anträge & Rollen", emoji="⚙️", value="admin"),
            discord.SelectOption(label="🍓 Raspberry Pi 4B Telemetrie", description="CPU-Temperatur, RAM, Uptime & Hardware", emoji="🍓", value="pi"),
        ]
        super().__init__(placeholder="Wähle eine Kategorie für detaillierte Befehle...", options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]

        if val == "mc":
            embed = discord.Embed(
                title="🟢 Minecraft Status, Power & Server Steuerung",
                description="Befehle zum Verwalten und Überwachen deines Minecraft Servers:",
                color=discord.Color.green()
            )
            embed.add_field(name="🚀 `/mc-start`", value="Fährt den Minecraft-Server hoch, falls er offline/im Ruhezustand ist.", inline=False)
            embed.add_field(name="🛑 `/mc-stop` & `/mc-restart`", value="*(Admin)* Fährt den Server herunter oder startet ihn neu.", inline=False)
            embed.add_field(name="⏱️ `/mc-autostop [an/aus] [minuten]`", value="*(Admin)* Konfiguriert das automatische Herunterfahren bei 15 Min. Inaktivität.", inline=False)
            embed.add_field(name="🟢 `/mcstatus` & `/mcplayers`", value="Zeigt Live-Status (Ping, Java & Bedrock, Spielerliste).", inline=False)
            embed.add_field(name="🎮 `/rcon <befehl>`", value="*(Admin)* Führt Konsolenbefehle direkt auf dem Server aus.", inline=False)
            embed.add_field(name="📢 `/broadcast <nachricht>`", value="*(Admin)* Sendet Ingame-Chatnachrichten an alle Spieler.", inline=False)
            embed.add_field(name="🌱 `/mc-seed`", value="Zeigt den World-Seed & Direktlink zur Chunkbase-Karte.", inline=False)
            embed.add_field(name="☀️ `/time-set` & `/weather-set`", value="*(Admin)* Ändert Zeit und Wetter ingame.", inline=False)

        elif val == "coords":
            embed = discord.Embed(
                title="📍 Koordinaten & Wegpunkte-System",
                description="Verwalte wichtige Orte deines SMPs:",
                color=discord.Color.teal()
            )
            embed.add_field(name="`/coords add <name> <x> <z> [y] [dimension] [info]`", value="Speichert einen Ort in der Datenbank.", inline=False)
            embed.add_field(name="`/coords list [dimension]`", value="Interaktive Liste aller Wegpunkte mit Direkt-Portal-Berechnung.", inline=False)
            embed.add_field(name="`/coords nether-calc <x> <z> [von]`", value="Rechnet Koordinaten zwischen Overworld und Nether um (1:8).", inline=False)

        elif val == "shop":
            embed = discord.Embed(
                title="💎 SMP Marktplatz & Wirtschaft",
                description="Ingame-Handel leicht gemacht:",
                color=discord.Color.gold()
            )
            embed.add_field(name="`/shop add <item> <preis> <ort> [menge]`", value="Erstelle ein Verkaufsangebot im Marktplatz.", inline=False)
            embed.add_field(name="`/shop list`", value="Zeigt alle aktuellen Angebote mit Verfügbarkeit an.", inline=False)
            embed.add_field(name="`/shop search <item>`", value="Sucht gezielt nach Waren (z.B. Elytra, Mending).", inline=False)
            embed.add_field(name="`/shop delete <id>`", value="Löscht dein Verkaufsangebot.", inline=False)

        elif val == "player":
            embed = discord.Embed(
                title="🎨 Spieler & Skin Tools",
                description="Mojang-Profile & 3D Renderings:",
                color=discord.Color.blue()
            )
            embed.add_field(name="`/skin <name>`", value="Zeigt das vollständige 3D-Modell und den Skin-Download an.", inline=False)
            embed.add_field(name="`/player <name>`", value="Zeigt UUID, NameMC Link und 3D-Büste des Spielers.", inline=False)
            embed.add_field(name="`/head <name>`", value="Gibt den Ingame /give Befehl für den Spielerkopf aus.", inline=False)

        elif val == "tools":
            embed = discord.Embed(
                title="🧪 Rechner & Minecraft Guides",
                description="Praktische Helfer für den Survival-Alltag:",
                color=discord.Color.purple()
            )
            embed.add_field(name="`/calc-blocks <länge> <breite> <höhe> [hohl]`", value="Berechnet Blöcke, Stacks, Shulkerkisten und Doppelkisten für Bauprojekte.", inline=False)
            embed.add_field(name="`/enchant-guide <item>`", value="Zeigt die besten Verzauberungen für Schwerter, Rüstung, Spitzhacken etc.", inline=False)
            embed.add_field(name="`/potion-guide <trank>`", value="Schritt-für-Schritt Braurezepte für wichtige Tränke.", inline=False)

        elif val == "admin":
            embed = discord.Embed(
                title="⚙️ Server-Setup & Administration",
                description="Vollautomatisches Management für Admins:",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="`/setup-smp [name]`", value="Erstellt automatisch alle Kategorien, Text-/Voice-Kanäle, Rollen & Regeln!", inline=False)
            embed.add_field(name="`/setup-roles`", value="Sendet ein interaktives Rollen-Auswahl-Panel mit Buttons in den Chat.", inline=False)
            embed.add_field(name="`/setup-whitelist-button`", value="Sendet das Whitelist-Antragsformular mit Admin-Annahme/Ablehnung.", inline=False)

        elif val == "pi":
            embed = discord.Embed(
                title="🍓 Raspberry Pi 4B Telemetrie",
                description="Host-Hardware-Informationen:",
                color=discord.Color.from_rgb(227, 11, 93)
            )
            embed.add_field(name="`/status`", value="Zeigt CPU-Temperatur, RAM, Festplatte, Uptime und Ping.", inline=False)
            embed.add_field(name="`/ping`", value="Zeigt die reine Websocket-Latenz.", inline=False)
            embed.add_field(name="`/info`", value="Allgemeine Bot-Details.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown())


class HelpCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Interaktive Befehlsübersicht für alle Minecraft SMP & Bot-Funktionen.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🍓 Ultimativer Minecraft SMP Bot – Hilfe-Menü",
            description=(
                "Willkommen beim umfassendsten Discord Bot für dein Minecraft SMP Projekt!\n\n"
                "**Wähle unten im Dropdown-Menü einen Bereich aus**, um die Befehle und Details anzusehen:\n\n"
                "• 🟢 **Minecraft Status:** Live-Serverstatus & Spielerabfrage\n"
                "• 📍 **Koordinaten:** Wegpunkte speichern & Nether-Portal-Rechner\n"
                "• 💎 **Marktplatz:** Ingame-Handel & Shop-Angebote\n"
                "• 🎨 **Spieler & Skins:** 3D Skin Renders & Spielerprofile\n"
                "• 🧪 **Rechner & Guides:** Blöcke/Stacks-Rechner, Enchantment- & Brau-Guides\n"
                "• ⚙️ **Server-Setup:** 1-Klick Discord-Server Konfiguration & Whitelist-System\n"
                "• 🍓 **Pi 4B Telemetrie:** Hardware-Monitoring & Bot-Status"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Gehostet auf Raspberry Pi 4B • Nutze Slash-Commands für die beste Erfahrung!")
        await interaction.response.send_message(embed=embed, view=HelpView())

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommandCog(bot))
