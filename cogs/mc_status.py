import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer, BedrockServer
import logging
import io
import base64
import database

logger = logging.getLogger("MCStatus")

PUBLIC_JAVA_HOST = "olds-skimpily.tun.ply.gg"
PUBLIC_BEDROCK_HOST = "olds-lieu.tun.ply.gg"
PUBLIC_BEDROCK_PORT = 58695

LOCAL_IP = "192.168.178.128"
LOCAL_JAVA_PORT = 25565
LOCAL_BEDROCK_PORT = 19132

class MCStatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set-server-ip", description="Speichert eine benutzerdefinierte Server-Adresse.")
    @app_commands.describe(ip="Server-IP oder Domain", java_port="Port (Standard: 25565)")
    @app_commands.default_permissions(administrator=True)
    async def set_server_ip(self, interaction: discord.Interaction, ip: str, java_port: int = 25565):
        if not interaction.guild:
            return

        await database.set_guild_setting(interaction.guild.id, "server_ip", ip)
        await database.set_guild_setting(interaction.guild.id, "server_port", java_port)
        await interaction.response.send_message(f"✅ Server-IP gespeichert: `{ip}`", ephemeral=True)

    @app_commands.command(name="mcstatus", description="Live-Statusabfrage für deinen weltweiten Minecraft Server (Java & Bedrock).")
    @app_commands.describe(ip="Optionale abweichende Server-IP")
    async def mcstatus(self, interaction: discord.Interaction, ip: str = None):
        await interaction.response.defer(thinking=True)

        target_java = ip if ip else PUBLIC_JAVA_HOST
        target_bedrock = ip if ip else PUBLIC_BEDROCK_HOST
        bedrock_port = PUBLIC_BEDROCK_PORT if not ip else 19132

        # 1. Query Java Server
        java_status = None
        try:
            j_server = await JavaServer.async_lookup(target_java, timeout=4)
            java_status = await j_server.async_status()
        except Exception:
            # Fallback to local if public query fails locally
            try:
                j_server = await JavaServer.async_lookup(f"{LOCAL_IP}:{LOCAL_JAVA_PORT}", timeout=3)
                java_status = await j_server.async_status()
            except Exception:
                pass

        # 2. Query Bedrock Server
        bedrock_status = None
        try:
            b_server = BedrockServer.lookup(f"{target_bedrock}:{bedrock_port}", timeout=3)
            bedrock_status = await b_server.async_status()
        except Exception:
            # Fallback to local
            try:
                b_server = BedrockServer.lookup(f"{LOCAL_IP}:{LOCAL_BEDROCK_PORT}", timeout=3)
                bedrock_status = await b_server.async_status()
            except Exception:
                pass

        if not java_status and not bedrock_status:
            embed_offline = discord.Embed(
                title="🔴 Minecraft Server Offline / Unerreichbar",
                description=f"Der Server unter `{PUBLIC_JAVA_HOST}` ist aktuell nicht erreichbar.\nStarte ihn mit `/mc-start`!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_offline)
            return

        motd_text = "Minecraft SMP Server | Bedrock & Java"
        if java_status and hasattr(java_status.motd, "to_plain"):
            motd_text = java_status.motd.to_plain().strip()
        elif bedrock_status:
            motd_text = str(bedrock_status.motd)

        embed = discord.Embed(
            title="🟢 Minecraft SMP Server Online (Weltweit erreichbar)",
            description=f"```fix\n{motd_text}\n```",
            color=discord.Color.green()
        )

        # Java Information
        if java_status:
            players_str = f"**{java_status.players.online}** / **{java_status.players.max}**"
            java_info = (
                f"🌐 **Server-Adresse:** `{PUBLIC_JAVA_HOST}`\n"
                f"🎮 **Version:** Fabric `{java_status.version.name}`\n"
                f"⚡ **Ping:** `{round(java_status.latency)} ms`\n"
                f"👥 **Spieler:** {players_str}"
            )
            embed.add_field(name="☕ Java Edition (PC / Mac)", value=java_info, inline=False)

        # Bedrock Information
        if bedrock_status:
            b_players = f"**{bedrock_status.players.online}** / **{bedrock_status.players.max}**"
            bedrock_info = (
                f"🌐 **Server-Name / IP:** `{PUBLIC_BEDROCK_HOST}`\n"
                f"🔌 **Port:** `{PUBLIC_BEDROCK_PORT}`\n"
                f"🎮 **Version:** Geyser `{bedrock_status.version.name}`\n"
                f"⚡ **Ping:** `{round(bedrock_status.latency)} ms`\n"
                f"👥 **Spieler:** {b_players}"
            )
            embed.add_field(name="📱 Bedrock Edition (Handy / Konsole / Tablet / Win)", value=bedrock_info, inline=False)

        # Online Players Sample
        if java_status and java_status.players.sample:
            names = [f"`{p.name}`" for p in java_status.players.sample]
            embed.add_field(name="🕹️ Aktuell online:", value=", ".join(names), inline=False)
        else:
            embed.add_field(name="🕹️ Aktuell online:", value="*Keine Spieler online*", inline=False)

        # Home Network Note
        embed.add_field(
            name="🏠 Im selben Heimnetzwerk (LAN/WLAN)?",
            value=f"Du kannst dich auch direkt verbinden über: `{LOCAL_IP}` (Java: `25565`, Bedrock: `19132`)",
            inline=False
        )

        # Server Icon
        file = None
        if java_status and java_status.icon:
            try:
                icon_data = base64.b64decode(java_status.icon.split(",")[-1])
                file = discord.File(io.BytesIO(icon_data), filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
            except Exception:
                pass

        embed.set_footer(text="Playit.gg Tunnel aktiv • Crossplay aktiviert")

        if file:
            await interaction.followup.send(file=file, embed=embed)
        else:
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="mcplayers", description="Listet alle aktuell eingeloggten Spieler auf.")
    async def mcplayers(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            server = await JavaServer.async_lookup(f"{LOCAL_IP}:25565", timeout=3)
            status = await server.async_status()

            if status.players.online == 0:
                embed = discord.Embed(
                    title="👥 Online Spieler: 0",
                    description="Aktuell ist niemand auf dem Server online.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"👥 Online Spieler: {status.players.online} / {status.players.max}",
                description=f"Server: `{PUBLIC_JAVA_HOST}`",
                color=discord.Color.green()
            )

            if status.players.sample:
                names = [f"• `{p.name}`" for p in status.players.sample]
                embed.add_field(name="Spielerliste:", value="\n".join(names), inline=False)
            else:
                embed.add_field(name="Spielerliste:", value="*Spielernamen verborgen*", inline=False)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Server nicht erreichbar: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(MCStatusCog(bot))
