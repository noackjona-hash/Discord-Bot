import discord
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer, BedrockServer
import logging
import io
import base64
import database

logger = logging.getLogger("MCStatus")

class MCStatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.live_updater.start()

    def cog_unload(self):
        self.live_updater.cancel()

    @app_commands.command(name="set-server-ip", description="Speichert die Standard-Minecraft-Server-IP für diesen Discord Server.")
    @app_commands.describe(ip="Server-IP oder Domain (z.B. mein-smp.de)", port="Port (Standard: 25565)")
    @app_commands.default_permissions(administrator=True)
    async def set_server_ip(self, interaction: discord.Interaction, ip: str, port: int = 25565):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern möglich.", ephemeral=True)
            return

        await database.set_guild_setting(interaction.guild.id, "server_ip", ip)
        await database.set_guild_setting(interaction.guild.id, "server_port", port)

        await interaction.response.send_message(f"✅ Server-IP gespeichert: `{ip}:{port}`", ephemeral=True)

    @app_commands.command(name="mcstatus", description="Prüft den Live-Status eines Minecraft Servers (Spieler, Ping, MOTD, Version).")
    @app_commands.describe(ip="Server-IP (optional, falls mit /set-server-ip hinterlegt)", port="Server-Port (optional)")
    async def mcstatus(self, interaction: discord.Interaction, ip: str = None, port: int = None):
        await interaction.response.defer(thinking=True)

        if not ip and interaction.guild:
            ip = await database.get_guild_setting(interaction.guild.id, "server_ip")
            if not port:
                port = await database.get_guild_setting(interaction.guild.id, "server_port", 25565)

        if not ip:
            await interaction.followup.send("❌ Bitte gib eine Server-IP an oder speichere eine mit `/set-server-ip`.")
            return

        target_port = port if port else 25565
        address = f"{ip}:{target_port}"

        try:
            # Try Java Server Query
            server = await JavaServer.async_lookup(address, timeout=5)
            status = await server.async_status()

            # Clean MOTD
            motd = status.motd.to_plain() if hasattr(status.motd, 'to_plain') else str(status.motd)
            clean_motd = motd.strip()

            embed = discord.Embed(
                title="🟢 Minecraft Server Online",
                description=f"```\n{clean_motd}\n```" if clean_motd else "Keine Beschreibung verfügbar.",
                color=discord.Color.green()
            )
            embed.add_field(name="🌐 Adresse", value=f"`{address}`", inline=True)
            embed.add_field(name="🎮 Version", value=f"`{status.version.name}`", inline=True)
            embed.add_field(name="⚡ Latenz", value=f"**{round(status.latency)} ms**", inline=True)

            player_count_str = f"**{status.players.online}** / **{status.players.max}**"
            embed.add_field(name="👥 Spieler", value=player_count_str, inline=True)

            # Player sample
            if status.players.sample:
                player_names = [p.name for p in status.players.sample[:15]]
                embed.add_field(
                    name="🕹️ Online Spieler",
                    value=", ".join([f"`{name}`" for name in player_names]),
                    inline=False
                )

            # Server Icon if available
            file = None
            if status.icon:
                try:
                    icon_data = base64.b64decode(status.icon.split(",")[-1])
                    file = discord.File(io.BytesIO(icon_data), filename="server_icon.png")
                    embed.set_thumbnail(url="attachment://server_icon.png")
                except Exception:
                    pass

            if file:
                await interaction.followup.send(file=file, embed=embed)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e_java:
            # Fallback to Bedrock check
            try:
                bedrock = BedrockServer.lookup(address, timeout=4)
                status = await bedrock.async_status()

                embed = discord.Embed(
                    title="🟢 Minecraft Bedrock Server Online",
                    description=f"```\n{status.motd.to_plain()}\n```",
                    color=discord.Color.green()
                )
                embed.add_field(name="🌐 Adresse", value=f"`{address}`", inline=True)
                embed.add_field(name="🎮 Version", value=f"`{status.version.name}`", inline=True)
                embed.add_field(name="⚡ Latenz", value=f"**{round(status.latency)} ms**", inline=True)
                embed.add_field(name="👥 Spieler", value=f"**{status.players_online}** / **{status.players_max}**", inline=True)
                await interaction.followup.send(embed=embed)
            except Exception:
                embed_offline = discord.Embed(
                    title="🔴 Minecraft Server Offline / Unerreichbar",
                    description=f"Der Server unter `{address}` konnte nicht erreicht werden.",
                    color=discord.Color.red()
                )
                embed_offline.add_field(name="🔍 Mögliche Gründe", value="• Server ist offline oder startet gerade neu\n• Falsche IP / Port\n• Firewall blockiert Anfragen", inline=False)
                await interaction.followup.send(embed=embed_offline)

    @app_commands.command(name="mcplayers", description="Listet alle aktuell auf dem SMP eingeloggten Spieler auf.")
    async def mcplayers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not interaction.guild:
            await interaction.followup.send("❌ Nur auf Servern ausführbar.")
            return

        ip = await database.get_guild_setting(interaction.guild.id, "server_ip")
        port = await database.get_guild_setting(interaction.guild.id, "server_port", 25565)

        if not ip:
            await interaction.followup.send("❌ Keine Server-IP hinterlegt. Nutze `/set-server-ip`.")
            return

        try:
            server = await JavaServer.async_lookup(f"{ip}:{port}", timeout=5)
            status = await server.async_status()

            if status.players.online == 0:
                embed = discord.Embed(
                    title="👥 Online Spieler (0)",
                    description="Aktuell ist niemand auf dem Server online.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"👥 Online Spieler ({status.players.online}/{status.players.max})",
                description=f"Server: `{ip}`",
                color=discord.Color.green()
            )

            if status.players.sample:
                names = [f"• `{p.name}`" for p in status.players.sample]
                embed.add_field(name="Spielerliste:", value="\n".join(names), inline=False)
            else:
                embed.add_field(name="Spielerliste:", value="*Spielernamen werden vom Server verborgen.*", inline=False)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Fehler beim Abrufen der Spielerliste: `{e}`")

    @tasks.loop(minutes=3)
    async def live_updater(self):
        """Optional task to update live server status embed or presence."""
        pass

    @live_updater.before_loop
    async def before_live_updater(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(MCStatusCog(bot))
