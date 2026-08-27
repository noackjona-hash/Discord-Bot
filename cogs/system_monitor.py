import os
import sys
import time
import platform
from datetime import datetime, timezone
import psutil
import discord
from discord import app_commands
from discord.ext import commands

START_TIME = time.time()

def get_cpu_temp() -> str:
    try:
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read().strip()) / 1000.0
                return f"{temp:.1f} °C"
    except Exception:
        pass
    return "N/A"

def format_uptime(seconds: float) -> str:
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


class SystemMonitorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Zeigt die aktuelle Bot-Latenz an.")
    async def slash_ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Websocket Latenz: **{latency_ms} ms**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Zeigt System- und Hardware-Status des Raspberry Pi 4B an.")
    async def slash_status(self, interaction: discord.Interaction):
        cpu_usage = psutil.cpu_percent(interval=None)
        cpu_temp = get_cpu_temp()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        bot_uptime = format_uptime(time.time() - START_TIME)
        sys_uptime = format_uptime(time.time() - psutil.boot_time())

        embed = discord.Embed(
            title="🍓 Raspberry Pi 4B Telemetrie & Status",
            description="Hardware-Auslastung & Host-Informationen",
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
            value=f"Ping: **{round(self.bot.latency * 1000)} ms**\nServer: **{len(self.bot.guilds)}**",
            inline=True
        )
        embed.add_field(
            name="🐍 Software",
            value=f"Python: **{platform.python_version()}**\ndiscord.py: **{discord.__version__}**",
            inline=True
        )

        embed.set_footer(text=f"Host: {platform.node()} ({platform.system()} {platform.machine()})")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info", description="Allgemeine Informationen über den Bot.")
    async def slash_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ℹ️ Über diesen Discord Bot",
            description="Der ultimative Discord Bot für deinen Minecraft SMP Server – gehostet auf einem Raspberry Pi 4B.",
            color=discord.Color.blue()
        )
        embed.add_field(name="👑 Entwickler", value="Jona", inline=True)
        embed.add_field(name="⚙️ Framework", value=f"discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="📍 Host", value="Raspberry Pi 4B", inline=True)
        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Lässt den Bot eine Nachricht wiederholen.")
    @app_commands.describe(message="Die Nachricht, die gesendet werden soll")
    async def slash_say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(SystemMonitorCog(bot))
