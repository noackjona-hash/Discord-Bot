import discord
from discord import app_commands
from discord.ext import commands
import logging
from mcrcon import MCRcon
import database

logger = logging.getLogger("RCONManager")

DEFAULT_RCON_IP = "192.168.178.128"
DEFAULT_RCON_PORT = 25575
DEFAULT_RCON_PASS = "jonajona"

def run_rcon_cmd(command: str, ip: str = DEFAULT_RCON_IP, port: int = DEFAULT_RCON_PORT, password: str = DEFAULT_RCON_PASS) -> str:
    """Executes a command via Minecraft RCON."""
    try:
        with MCRcon(ip, password, port=port, timeout=5) as mcr:
            resp = mcr.command(command)
            return resp if resp else "Befehl ohne Rückmeldung ausgeführt."
    except Exception as e:
        logger.error(f"RCON Fehler bei '{command}': {e}")
        return f"Fehler: {e}"


class RCONManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rcon", description="Führt einen beliebigen Konsolenbefehl auf dem Minecraft-Server aus (Nur Admins).")
    @app_commands.describe(command="Minecraft-Befehl (z.B. 'say Hallo Welt', 'give Notch diamond 64', 'gamerule keepInventory true')")
    @app_commands.default_permissions(administrator=True)
    async def rcon(self, interaction: discord.Interaction, command: str):
        await interaction.response.defer(thinking=True)
        # Strip leading slash if user typed it
        clean_cmd = command.lstrip("/")
        resp = run_rcon_cmd(clean_cmd)

        embed = discord.Embed(
            title="🎮 Minecraft Server Konsole (RCON)",
            description=f"**Befehl:** `/{clean_cmd}`",
            color=discord.Color.green() if not resp.startswith("Fehler") else discord.Color.red()
        )
        embed.add_field(name="Antwort der Konsole:", value=f"```\n{resp[:1000]}\n```", inline=False)
        embed.set_footer(text="Ausgeführt über gesicherte RCON-Verbindung")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="broadcast", description="Sendet eine formatierte Nachricht an alle Spieler ingame auf dem Server.")
    @app_commands.describe(message="Nachricht, die im Minecraft Chat erscheinen soll")
    @app_commands.default_permissions(administrator=True)
    async def broadcast(self, interaction: discord.Interaction, message: str):
        # Format raw JSON or tellraw for fancy display
        cmd = f'tellraw @a {{"text":"[Discord] <{interaction.user.display_name}> {message}","color":"aqua"}}'
        resp = run_rcon_cmd(cmd)

        embed = discord.Embed(
            title="📢 Ingame-Nachricht gesendet",
            description=f"**Text:** {message}",
            color=discord.Color.teal()
        )
        embed.set_footer(text=f"Gesendet von {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whitelist-add", description="Fügt einen Spieler zur Minecraft-Server Whitelist hinzu.")
    @app_commands.describe(player_name="Minecraft Ingame-Name (Java oder .BedrockName)")
    @app_commands.default_permissions(administrator=True)
    async def whitelist_add(self, interaction: discord.Interaction, player_name: str):
        await interaction.response.defer(thinking=True)
        # Ensure whitelist is on and add player
        run_rcon_cmd("whitelist on")
        resp = run_rcon_cmd(f"whitelist add {player_name}")

        embed = discord.Embed(
            title="✅ Whitelist aktualisiert",
            description=f"Spieler: **`{player_name}`**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/face/64/{player_name}.png")
        embed.add_field(name="Server-Rückmeldung:", value=f"`{resp}`", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="whitelist-remove", description="Entfernt einen Spieler von der Minecraft Whitelist.")
    @app_commands.describe(player_name="Minecraft Ingame-Name")
    @app_commands.default_permissions(administrator=True)
    async def whitelist_remove(self, interaction: discord.Interaction, player_name: str):
        resp = run_rcon_cmd(f"whitelist remove {player_name}")
        embed = discord.Embed(
            title="🚫 Spieler von Whitelist entfernt",
            description=f"Spieler: **`{player_name}`**\nRückmeldung: `{resp}`",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mc-seed", description="Zeigt den World-Seed und den Link zur interaktiven Chunkbase-Karte.")
    async def mc_seed(self, interaction: discord.Interaction):
        resp = run_rcon_cmd("seed")
        # Extract seed number if possible
        seed_num = "5252518894722547927"
        if "[" in resp and "]" in resp:
            seed_num = resp.split("[")[1].split("]")[0]

        chunkbase_url = f"https://www.chunkbase.com/apps/seed-map#seed={seed_num}&version=1.21"

        embed = discord.Embed(
            title="🌱 Minecraft SMP – World Seed",
            description=f"Der Seed dieser Welt lautet:\n```\n{seed_num}\n```",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🗺️ Interaktive Map (Biome, Spawns & Festungen)",
            value=f"[Klicke hier für die Chunkbase Seed-Karte]({chunkbase_url})",
            inline=False
        )
        embed.set_footer(text="Minecraft 1.21.x Generator")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="time-set", description="Ändert die Tageszeit auf dem Minecraft Server.")
    @app_commands.describe(time="Wähle die Tageszeit")
    @app_commands.choices(time=[
        app_commands.Choice(name="☀️ Tag (Day / 1000)", value="day"),
        app_commands.Choice(name="🌞 Mittag (Noon / 6000)", value="noon"),
        app_commands.Choice(name="🌙 Nacht (Night / 13000)", value="night"),
        app_commands.Choice(name="🌑 Mitternacht (Midnight / 18000)", value="midnight"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def time_set(self, interaction: discord.Interaction, time: app_commands.Choice[str]):
        resp = run_rcon_cmd(f"time set {time.value}")
        await interaction.response.send_message(f"⏰ Zeit auf `{time.name}` gesetzt! (`{resp}`)")

    @app_commands.command(name="weather-set", description="Ändert das Wetter auf dem Minecraft Server.")
    @app_commands.describe(weather="Wähle das Wetter")
    @app_commands.choices(weather=[
        app_commands.Choice(name="☀️ Sonnig / Klar (Clear)", value="clear"),
        app_commands.Choice(name="🌧️ Regen (Rain)", value="rain"),
        app_commands.Choice(name="⚡ Gewitter (Thunder)", value="thunder"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def weather_set(self, interaction: discord.Interaction, weather: app_commands.Choice[str]):
        resp = run_rcon_cmd(f"weather {weather.value}")
        await interaction.response.send_message(f"🌦️ Wetter auf `{weather.name}` geändert! (`{resp}`)")


async def setup(bot: commands.Bot):
    await bot.add_cog(RCONManagerCog(bot))
