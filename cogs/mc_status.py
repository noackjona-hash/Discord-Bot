import discord
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer, BedrockServer
import logging
import io
import base64
import database

logger = logging.getLogger("MCStatus")

DEFAULT_IP = "192.168.178.128"
DEFAULT_JAVA_PORT = 25565
DEFAULT_BEDROCK_PORT = 19132

class MCStatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set-server-ip", description="Speichert die Standard-Minecraft-Server-IP für diesen Discord Server.")
    @app_commands.describe(ip="Server-IP (z.B. 192.168.178.128 oder deine-domain.de)", java_port="Java Port (Standard: 25565)")
    @app_commands.default_permissions(administrator=True)
    async def set_server_ip(self, interaction: discord.Interaction, ip: str, java_port: int = 25565):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern möglich.", ephemeral=True)
            return

        await database.set_guild_setting(interaction.guild.id, "server_ip", ip)
        await database.set_guild_setting(interaction.guild.id, "server_port", java_port)
        await interaction.response.send_message(f"✅ Server-IP gespeichert: `{ip}` (Java: `{java_port}`, Bedrock: `19132`)", ephemeral=True)

    @app_commands.command(name="mcstatus", description="Live-Statusabfrage für deinen Fabric + Geyser Minecraft Server (Java & Bedrock).")
    @app_commands.describe(ip="Optionale abweichende Server-IP")
    async def mcstatus(self, interaction: discord.Interaction, ip: str = None):
        await interaction.response.defer(thinking=True)

        if not ip and interaction.guild:
            ip = await database.get_guild_setting(interaction.guild.id, "server_ip", DEFAULT_IP)
        if not ip:
            ip = DEFAULT_IP

        java_port = DEFAULT_JAVA_PORT
        bedrock_port = DEFAULT_BEDROCK_PORT

        # Query Java Server
        java_status = None
        java_error = None
        try:
            j_server = await JavaServer.async_lookup(f"{ip}:{java_port}", timeout=4)
            java_status = await j_server.async_status()
        except Exception as e:
            java_error = str(e)

        # Query Bedrock / Geyser Server
        bedrock_status = None
        try:
            b_server = BedrockServer.lookup(f"{ip}:{bedrock_port}", timeout=3)
            bedrock_status = await b_server.async_status()
        except Exception:
            pass

        if not java_status and not bedrock_status:
            embed_offline = discord.Embed(
                title="🔴 Minecraft Server Offline / Unerreichbar",
                description=f"Der Server unter `{ip}` antwortet aktuell weder auf Java (`:{java_port}`) noch auf Bedrock (`:{bedrock_port}`).",
                color=discord.Color.red()
            )
            embed_offline.add_field(name="Mögliche Ursachen", value="• Der Minecraft-Server ist gestoppt oder startet gerade neu\n• Firewall blockiert Port 25565 / 19132", inline=False)
            await interaction.followup.send(embed=embed_offline)
            return

        # Build Rich Dual Embed
        motd_text = "Minecraft SMP Server"
        if java_status and hasattr(java_status.motd, "to_plain"):
            motd_text = java_status.motd.to_plain().strip()
        elif bedrock_status:
            motd_text = str(bedrock_status.motd)

        embed = discord.Embed(
            title="🟢 Minecraft SMP Server Online",
            description=f"```fix\n{motd_text}\n```",
            color=discord.Color.green()
        )

        # Java Information
        if java_status:
            players_str = f"**{java_status.players.online}** / **{java_status.players.max}**"
            java_info = (
                f"• **IP / Port:** `{ip}:{java_port}`\n"
                f"• **Version:** Fabric `{java_status.version.name}`\n"
                f"• **Ping:** `{round(java_status.latency)} ms`\n"
                f"• **Spieler:** {players_str}"
            )
            embed.add_field(name="☕ Java Edition (PC / Mac)", value=java_info, inline=True)
        else:
            embed.add_field(name="☕ Java Edition", value=f"🔴 Nicht erreichbar (`{java_error}`)", inline=True)

        # Bedrock / Geyser Information
        if bedrock_status:
            b_players = f"**{bedrock_status.players.online}** / **{bedrock_status.players.max}**"
            bedrock_info = (
                f"• **IP / Port:** `{ip}:{bedrock_port}`\n"
                f"• **Version:** Geyser `{bedrock_status.version.name}`\n"
                f"• **Ping:** `{round(bedrock_status.latency)} ms`\n"
                f"• **Spieler:** {b_players}"
            )
            embed.add_field(name="📱 Bedrock Edition (Handy / Konsole / Win)", value=bedrock_info, inline=True)
        else:
            embed.add_field(name="📱 Bedrock Edition (Geyser)", value=f"• **Port:** `{bedrock_port}` (Geyser aktiv)", inline=True)

        # Online Player Names list
        if java_status and java_status.players.sample:
            names = [f"`{p.name}`" for p in java_status.players.sample]
            embed.add_field(name="👥 Aktuell online:", value=", ".join(names), inline=False)
        else:
            embed.add_field(name="👥 Aktuell online:", value="*Keine Spieler eingeloggt oder Liste verborgen*", inline=False)

        # Server Icon
        file = None
        if java_status and java_status.icon:
            try:
                icon_data = base64.b64decode(java_status.icon.split(",")[-1])
                file = discord.File(io.BytesIO(icon_data), filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
            except Exception:
                pass

        embed.set_footer(text=f"Gehostet im Heimnetzwerk • Crossplay aktiviert via GeyserMC")

        if file:
            await interaction.followup.send(file=file, embed=embed)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="mcplayers", description="Listet alle aktuell eingeloggten Spieler auf dem Server auf.")
    async def mcplayers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        ip = await database.get_guild_setting(interaction.guild.id, "server_ip", DEFAULT_IP) if interaction.guild else DEFAULT_IP

        try:
            server = await JavaServer.async_lookup(f"{ip}:25565", timeout=4)
            status = await server.async_status()

            if status.players.online == 0:
                embed = discord.Embed(
                    title="👥 Online Spieler: 0 / 10",
                    description=f"Aktuell ist niemand auf `{ip}` online.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"👥 Online Spieler: {status.players.online} / {status.players.max}",
                description=f"Server: `{ip}` (Fabric + Geyser)",
                color=discord.Color.green()
            )

            if status.players.sample:
                names = [f"• `{p.name}`" for p in status.players.sample]
                embed.add_field(name="Spielerliste:", value="\n".join(names), inline=False)
            else:
                embed.add_field(name="Spieler:", value="*Spielernamen sind verborgen.*", inline=False)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Server nicht erreichbar: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(MCStatusCog(bot))
