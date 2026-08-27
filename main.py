import os
import sys
import time
import platform
import logging
from datetime import datetime, timezone
import psutil
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DiscordBot")

# Bot start timestamp for uptime calculation
START_TIME = time.time()

# Discord Bot Intents
intents = discord.Intents.default()

class RaspberryBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Sync application slash commands globally
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} slash command(s).")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Set custom presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Minecraft SMP | /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

bot = RaspberryBot()


def get_cpu_temp() -> str:
    """Reads Raspberry Pi CPU temperature."""
    try:
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read().strip()) / 1000.0
                return f"{temp:.1f} °C"
    except Exception:
        pass
    return "N/A"


def format_uptime(seconds: float) -> str:
    """Formats seconds into days, hours, minutes, and seconds."""
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# ==========================================
# Slash Commands - General & System
# ==========================================

@bot.tree.command(name="ping", description="Zeigt die aktuelle Bot-Latenz an.")
async def slash_ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Websocket Latenz: **{latency_ms} ms**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="status", description="Zeigt System- und Hardware-Status des Raspberry Pi 4B an.")
async def slash_status(interaction: discord.Interaction):
    cpu_usage = psutil.cpu_percent(interval=None)
    cpu_temp = get_cpu_temp()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    bot_uptime = format_uptime(time.time() - START_TIME)
    sys_uptime = format_uptime(time.time() - psutil.boot_time())

    embed = discord.Embed(
        title="🍓 Raspberry Pi 4B Status",
        description="Aktuelle Telemetrie & Systeminformationen",
        color=discord.Color.from_rgb(227, 11, 93),
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="⚡ Prozessor (CPU)",
        value=f"Auslastung: **{cpu_usage}%**\nTemperatur: **{cpu_temp}**\nKerne: **{psutil.cpu_count(logical=True)}**",
        inline=True
    )
    embed.add_field(
        name="🧠 Arbeitsspeicher (RAM)",
        value=f"Belegt: **{ram.used / (1024**3):.2f} GB** / **{ram.total / (1024**3):.2f} GB**\nAuslastung: **{ram.percent}%**",
        inline=True
    )
    embed.add_field(
        name="💾 Festplatte / SD-Karte",
        value=f"Belegt: **{disk.used / (1024**3):.1f} GB** / **{disk.total / (1024**3):.1f} GB**\nFrei: **{disk.free / (1024**3):.1f} GB** ({100 - disk.percent:.1f}%)",
        inline=True
    )

    embed.add_field(
        name="⏱️ Uptime",
        value=f"Bot: **{bot_uptime}**\nSystem: **{sys_uptime}**",
        inline=True
    )
    embed.add_field(
        name="📡 Verbindung",
        value=f"Ping: **{round(bot.latency * 1000)} ms**\nServer: **{len(bot.guilds)}**",
        inline=True
    )
    embed.add_field(
        name="🐍 Software",
        value=f"Python: **{platform.python_version()}**\ndiscord.py: **{discord.__version__}**",
        inline=True
    )

    embed.set_footer(text=f"Host: {platform.node()} ({platform.system()} {platform.machine()})")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info", description="Allgemeine Informationen über den Bot.")
async def slash_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ Über diesen Bot",
        description="Ein moderner, performanter Discord Bot für deinen Minecraft SMP Server, der auf einem Raspberry Pi 4B läuft.",
        color=discord.Color.blue()
    )
    embed.add_field(name="👑 Entwickler", value="Jona", inline=True)
    embed.add_field(name="⚙️ Framework", value=f"discord.py v{discord.__version__}", inline=True)
    embed.add_field(name="📍 Host", value="Raspberry Pi 4B", inline=True)
    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="say", description="Lässt den Bot eine Nachricht wiederholen.")
@app_commands.describe(message="Die Nachricht, die der Bot senden soll")
async def slash_say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)


@bot.tree.command(name="help", description="Zeigt alle verfügbaren Befehle an.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Hilfe & Befehlsübersicht",
        description="Hier ist eine Liste aller verfügbaren Befehle:",
        color=discord.Color.purple()
    )
    embed.add_field(name="🛠️ `/setup-smp`", value="Richtet den Discord-Server automatisch mit Rollen, Kanälen & Regeln für ein Minecraft SMP ein! (Nur Admins)", inline=False)
    embed.add_field(name="🎮 `/smp-info`", value="Zeigt Minecraft Server-IP, Version, Regeln und Infos an.", inline=False)
    embed.add_field(name="🍓 `/status`", value="Zeigt CPU-Temperatur, RAM und Uptime des Raspberry Pi an.", inline=False)
    embed.add_field(name="🏓 `/ping`", value="Zeigt die aktuelle Bot-Latenz (Ping) an.", inline=False)
    embed.add_field(name="ℹ️ `/info`", value="Zeigt Informationen über den Bot an.", inline=False)
    embed.add_field(name="💬 `/say [text]`", value="Wiederholt den angegebenen Text.", inline=False)
    embed.set_footer(text="Tipp: Alle Befehle sind modern als Slash-Commands integriert.")
    await interaction.response.send_message(embed=embed)


# ==========================================
# Slash Commands - Minecraft SMP Server Setup
# ==========================================

@bot.tree.command(name="setup-smp", description="Richtet diesen Discord-Server automatisch für deinen Minecraft SMP Server ein.")
@app_commands.describe(server_name="Name des SMP-Projekts (z.B. 'Jona & Friends SMP')")
@app_commands.default_permissions(administrator=True)
async def slash_setup_smp(interaction: discord.Interaction, server_name: str = "Minecraft SMP"):
    if not interaction.guild:
        await interaction.response.send_message("❌ Dieser Befehl kann nur auf einem Discord-Server ausgeführt werden!", ephemeral=True)
        return

    # Check permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Du benötigst Administrator-Rechte, um das Server-Setup durchzuführen!", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    guild = interaction.guild

    try:
        # 1. Rollen erstellen
        roles_to_create = [
            {"name": "👑 Admin", "color": discord.Color.gold(), "hoist": True, "mentionable": True},
            {"name": "🛡️ Moderator", "color": discord.Color.blue(), "hoist": True, "mentionable": True},
            {"name": "⛏️ SMP Member", "color": discord.Color.green(), "hoist": True, "mentionable": True},
            {"name": "🔔 Ankündigungen", "color": discord.Color.teal(), "hoist": False, "mentionable": True},
        ]
        
        created_roles = {}
        for role_data in roles_to_create:
            existing = discord.utils.get(guild.roles, name=role_data["name"])
            if not existing:
                role = await guild.create_role(
                    name=role_data["name"],
                    color=role_data["color"],
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"],
                    reason="SMP Auto-Setup"
                )
                created_roles[role_data["name"]] = role
            else:
                created_roles[role_data["name"]] = existing

        # Permissions Overwrites
        everyone_role = guild.default_role
        read_only_overwrites = {
            everyone_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }

        # 2. Kategorie 1: WILLKOMMEN & INFO
        cat_info = await guild.create_category("📌 WILLKOMMEN & INFO")
        chan_regeln = await guild.create_text_channel("📜-regeln", category=cat_info, overwrites=read_only_overwrites)
        chan_announcements = await guild.create_text_channel("📢-ankündigungen", category=cat_info, overwrites=read_only_overwrites)
        chan_server_info = await guild.create_text_channel("ℹ️-server-info", category=cat_info, overwrites=read_only_overwrites)

        # 3. Kategorie 2: COMMUNITY CHAT
        cat_community = await guild.create_category("💬 COMMUNITY")
        chan_general = await guild.create_text_channel("💬-allgemein", category=cat_community)
        chan_smp_talk = await guild.create_text_channel("⛏️-smp-talk", category=cat_community)
        chan_media = await guild.create_text_channel("📸-screenshots-clips", category=cat_community)
        chan_bot = await guild.create_text_channel("🤖-bot-befehle", category=cat_community)

        # 4. Kategorie 3: HANDEL & PROJEKTE
        cat_projects = await guild.create_category("🤝 HANDEL & PROJEKTE")
        chan_shops = await guild.create_text_channel("🛒-shops-und-handel", category=cat_projects)
        chan_builds = await guild.create_text_channel("🏗️-bauprojekte", category=cat_projects)
        chan_coords = await guild.create_text_channel("📍-koordinaten", category=cat_projects)

        # 5. Kategorie 4: VOICE CHANNELS
        cat_voice = await guild.create_category("🔊 SPRACHKANÄLE")
        await guild.create_voice_channel("🔊 Talk 1", category=cat_voice)
        await guild.create_voice_channel("🔊 Talk 2", category=cat_voice)
        await guild.create_voice_channel("⛏️ Mining & Farmen", category=cat_voice)
        await guild.create_voice_channel("⚔️ Bossfight / End", category=cat_voice)
        await guild.create_voice_channel("💤 AFK", category=cat_voice)

        # 6. Willkommens- & Regel-Embeds posten
        embed_rules = discord.Embed(
            title=f"📜 {server_name} – Serverregeln",
            description="Herzlich willkommen! Bitte halte dich an die folgenden Grundregeln für ein faires und entspanntes Miteinander:",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed_rules.add_field(name="1️⃣ Kein Griefing & Stehlen", value="Zerstöre keine fremden Gebäude und nimm nichts ungefragt aus Kisten.", inline=False)
        embed_rules.add_field(name="2️⃣ Respektvoller Umgang", value="Behandle alle Mitspieler freundlich und respektvoll. Beleidigungen oder Toxizität sind tabu.", inline=False)
        embed_rules.add_field(name="3️⃣ Keine Hacks & Cheats", value="X-Ray, Autoclicker, Fly-Hacks oder unfaire Client-Modifikationen führen zum Bann.", inline=False)
        embed_rules.add_field(name="4️⃣ Bauabstand", value="Halte ausreichend Abstand zu den Basen anderer Spieler, es sei denn, es ist abgesprochen.", inline=False)
        embed_rules.add_field(name="5️⃣ Handel & Währung", value="Handel fair in Diamanten oder nach gegenseitiger Absprache im Kanal <#shops-und-handel>.", inline=False)
        embed_rules.set_footer(text=f"{server_name} • Viel Spaß beim Bauen & Überleben!")
        await chan_regeln.send(embed=embed_rules)

        embed_info = discord.Embed(
            title=f"ℹ️ {server_name} – Serverinformationen",
            description="Hier findest du alle wichtigen Verbindungsdaten zum Minecraft SMP Server.",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        embed_info.add_field(name="🌐 Server-IP", value="`deine-server-ip-oder-domain.de`", inline=True)
        embed_info.add_field(name="🎮 Minecraft Version", value="`Java 1.21.x`", inline=True)
        embed_info.add_field(name="🔒 Whitelist", value="Aktiviert (Schreibe einem Admin deinen Ingame-Namen)", inline=True)
        embed_info.add_field(name="🗺️ Dynmap / Live-Map", value="*Optional / folgt*", inline=True)
        embed_info.add_field(name="💡 Tipps", value="Teile deine Bauwerke in <#screenshots-clips> und trage wichtige Orte in <#koordinaten> ein!", inline=False)
        embed_info.set_footer(text="Gesteuert von deinem Raspberry Pi 4B Bot")
        await chan_server_info.send(embed=embed_info)

        # 7. Erfolgsmeldung
        success_embed = discord.Embed(
            title="🎉 Minecraft SMP Server-Setup erfolgreich!",
            description=f"Der Server **{guild.name}** wurde komplett für dein Projekt **{server_name}** eingerichtet.",
            color=discord.Color.green()
        )
        success_embed.add_field(
            name="✨ Erstellte Kategorien & Kanäle",
            value=(
                "• **📌 WILLKOMMEN & INFO:** `#📜-regeln`, `#📢-ankündigungen`, `#ℹ️-server-info`\n"
                "• **💬 COMMUNITY:** `#💬-allgemein`, `#⛏️-smp-talk`, `#📸-screenshots-clips`, `#🤖-bot-befehle`\n"
                "• **🤝 HANDEL & PROJEKTE:** `#🛒-shops-und-handel`, `#🏗️-bauprojekte`, `#📍-koordinaten`\n"
                "• **🔊 SPRACHKANÄLE:** Talk 1, Talk 2, Mining, Bossfight, AFK"
            ),
            inline=False
        )
        success_embed.add_field(
            name="🛡️ Erstellte Rollen",
            value="• `👑 Admin`\n• `🛡️ Moderator`\n• `⛏️ SMP Member`\n• `🔔 Ankündigungen`",
            inline=False
        )
        success_embed.set_footer(text="Tipp: Passe die Server-IP im Kanal #server-info an!")
        await interaction.followup.send(embed=success_embed)

    except Exception as e:
        logger.error(f"Fehler beim SMP-Setup: {e}")
        await interaction.followup.send(f"❌ Es ist ein Fehler beim Setup aufgetreten: `{e}`")


@bot.tree.command(name="smp-info", description="Zeigt oder aktualisiert die Minecraft Server-Informationen.")
@app_commands.describe(
    ip="Server-IP oder Domain (z.B. mein-smp.de)",
    version="Minecraft Version (z.B. 1.21.1)",
    dynmap="Link zur Dynmap / Live-Map (optional)"
)
async def slash_smp_info(interaction: discord.Interaction, ip: str = None, version: str = "Java 1.21.x", dynmap: str = "Keine"):
    embed = discord.Embed(
        title="⛏️ Minecraft SMP – Server Details",
        description="Hier sind die aktuellen Daten zum Mitspielen:",
        color=discord.Color.teal()
    )
    server_ip_display = f"`{ip}`" if ip else "`Wird vom Admin bekanntgegeben`"
    embed.add_field(name="🌐 Server-IP", value=server_ip_display, inline=True)
    embed.add_field(name="🎮 Version", value=f"`{version}`", inline=True)
    embed.add_field(name="🗺️ Live-Karte", value=dynmap if dynmap != "Keine" else "*Keine*", inline=True)
    embed.set_footer(text="Viel Spaß beim Spielen!")
    await interaction.response.send_message(embed=embed)


# ==========================================
# Main Execution
# ==========================================

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN_HERE" or token.strip() == "":
        logger.error("=" * 60)
        logger.error("FEHLER: Kein DISCORD_TOKEN in der .env-Datei gefunden!")
        logger.error("Bitte trage deinen Discord Bot Token in die .env Datei ein:")
        logger.error("DISCORD_TOKEN=dein_bot_token_hier")
        logger.error("=" * 60)
        sys.exit(1)

    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Ungültiger Discord Token! Bitte überprüfe den Token in der .env-Datei.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Starten des Bots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
