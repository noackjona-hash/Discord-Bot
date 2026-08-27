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
intents.message_content = True  # Enable message content for prefix commands

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
            name="auf Raspberry Pi 4B | /help"
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
# Slash Commands
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
    # Calculate stats
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
        description="Ein moderner, performanter Discord Bot, der auf einem Raspberry Pi 4B läuft.",
        color=discord.Color.blue()
    )
    embed.add_field(name="👑 Entwickler", value="Jona", inline=True)
    embed.add_field(name="⚙️ Framework", value=f"discord.py v{discord.__version__}", inline=True)
    embed.add_field(name="📍 Host", value="Raspberry Pi 4B", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user else None)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="say", description="Lässt den Bot eine Nachricht wiederholen.")
@app_commands.describe(message="Die Nachricht, die der Bot senden soll")
async def slash_say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)


@bot.tree.command(name="help", description="Zeigt die verfügbaren Befehle an.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Hilfe & Befehlsübersicht",
        description="Hier ist eine Liste aller verfügbaren Slash-Befehle:",
        color=discord.Color.purple()
    )
    embed.add_field(name="`/ping`", value="Zeigt die aktuelle Bot-Latenz (Ping) an.", inline=False)
    embed.add_field(name="`/status`", value="Zeigt CPU, RAM, Temperatur und Uptime des Raspberry Pi an.", inline=False)
    embed.add_field(name="`/info`", value="Zeigt Informationen über den Bot an.", inline=False)
    embed.add_field(name="`/say [text]`", value="Wiederholt den angegebenen Text.", inline=False)
    embed.add_field(name="`/help`", value="Zeigt diese Hilfe an.", inline=False)
    embed.set_footer(text="Tipp: Alle Befehle funktionieren auch mit Präfix '!' (z.B. !ping, !status)")
    await interaction.response.send_message(embed=embed)


# ==========================================
# Traditional Prefix Commands (Fallback)
# ==========================================

@bot.command(name="ping")
async def cmd_ping(ctx: commands.Context):
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency_ms} ms`")

@bot.command(name="status", aliases=["pi"])
async def cmd_status(ctx: commands.Context):
    cpu_usage = psutil.cpu_percent(interval=None)
    cpu_temp = get_cpu_temp()
    ram = psutil.virtual_memory()
    bot_uptime = format_uptime(time.time() - START_TIME)

    msg = (
        f"🍓 **Raspberry Pi 4B Status**\n"
        f"• **CPU:** {cpu_usage}% ({cpu_temp})\n"
        f"• **RAM:** {ram.used / (1024**3):.2f} / {ram.total / (1024**3):.2f} GB ({ram.percent}%)\n"
        f"• **Ping:** {round(bot.latency * 1000)} ms\n"
        f"• **Uptime:** {bot_uptime}"
    )
    await ctx.send(msg)

@bot.command(name="help")
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "📖 **Befehle:** `!ping`, `!status`, `!help` oder nutze die modernen Slash-Commands (`/ping`, `/status`, `/help`)."
    )


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
