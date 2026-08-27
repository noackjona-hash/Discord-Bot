import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import logging
from mcstatus import JavaServer
from datetime import datetime, timezone

logger = logging.getLogger("ServerPower")

MC_HOST = "192.168.178.128"
MC_USER = "admin"

class ServerPowerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.is_starting = False
        self.watchdog_24_7.start()

    def cog_unload(self):
        self.watchdog_24_7.cancel()

    async def run_ssh(self, cmd: str) -> tuple[int, str]:
        """Runs an SSH command on the Minecraft server host asynchronously."""
        full_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {MC_USER}@{MC_HOST} '{cmd}'"
        proc = await asyncio.create_subprocess_shell(
            full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out = (stdout.decode() + stderr.decode()).strip()
        return proc.returncode, out

    async def is_server_active(self) -> bool:
        """Checks if systemd service is active."""
        code, out = await self.run_ssh("sudo systemctl is-active minecraft")
        return code == 0 and "active" in out

    @app_commands.command(name="mc-start", description="Fährt den Minecraft SMP Server hoch (falls er gestoppt wurde).")
    async def mc_start(self, interaction: discord.Interaction):
        if self.is_starting:
            await interaction.response.send_message("⏳ Der Server fährt gerade bereits hoch...", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        if await self.is_server_active():
            await interaction.followup.send("🟢 Der Minecraft Server läuft bereits 24/7 und ist online! (Java: `olds-skimpily.tun.ply.gg`, Bedrock: `olds-lieu.tun.ply.gg:58695`)")
            return

        self.is_starting = True

        embed = discord.Embed(
            title="🚀 Minecraft Server wird gestartet...",
            description="Starte Fabric Server & 24/7 Überwachung...\nBitte warte ca. **10 - 20 Sekunden**.",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.followup.send(embed=embed)

        try:
            code, out = await self.run_ssh("sudo systemctl start minecraft")
            if code != 0:
                self.is_starting = False
                await interaction.channel.send(f"❌ Fehler beim Starten des Servers: `{out}`")
                return

            # Wait for ready
            online = False
            for _ in range(25):
                await asyncio.sleep(2)
                try:
                    server = await JavaServer.async_lookup(f"{MC_HOST}:25565", timeout=2)
                    await server.async_status()
                    online = True
                    break
                except Exception:
                    continue

            self.is_starting = False

            embed_ready = discord.Embed(
                title="🎉 Minecraft SMP Server ist ONLINE (24/7 Dauerbetrieb)",
                description="Der Server ist nun dauerhaft online und erreichbar.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed_ready.add_field(name="☕ Java Edition (PC)", value="`olds-skimpily.tun.ply.gg`", inline=True)
            embed_ready.add_field(name="📱 Bedrock / Handy / Konsole", value="`olds-lieu.tun.ply.gg:58695`", inline=True)
            await interaction.channel.send(embed=embed_ready)

        except Exception as e:
            self.is_starting = False
            logger.error(f"Fehler bei mc_start: {e}")
            await interaction.channel.send(f"❌ Fehler beim Starten: `{e}`")

    @app_commands.command(name="mc-stop", description="Fährt den Minecraft Server manuell herunter (Nur Admins).")
    @app_commands.default_permissions(administrator=True)
    async def mc_stop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        if not await self.is_server_active():
            await interaction.followup.send("🔴 Der Minecraft Server ist bereits offline.", ephemeral=True)
            return

        try:
            from cogs.rcon_manager import run_rcon_cmd
            run_rcon_cmd('say [Discord] Server wird heruntergefahren...')
            run_rcon_cmd('save-all')
        except Exception:
            pass

        await asyncio.sleep(2)
        await self.run_ssh("sudo systemctl stop minecraft")

        embed = discord.Embed(
            title="🛑 Minecraft Server manuell gestoppt",
            description="Der Server wurde heruntergefahren. Starte ihn mit `/mc-start` wieder.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Gestoppt von {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="mc-restart", description="Startet den Minecraft Server neu (Nur Admins).")
    @app_commands.default_permissions(administrator=True)
    async def mc_restart(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            from cogs.rcon_manager import run_rcon_cmd
            run_rcon_cmd('say [Discord] Server-Neustart wird ausgefuehrt...')
            run_rcon_cmd('save-all')
        except Exception:
            pass

        await self.run_ssh("sudo systemctl restart minecraft")

        embed = discord.Embed(
            title="🔄 Minecraft Server wird neu gestartet...",
            description="Der Server startet jetzt neu und ist in ca. 15-20 Sekunden wieder erreichbar.",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)

    @tasks.loop(minutes=2)
    async def watchdog_24_7(self):
        """24/7 Watchdog: Ensures Minecraft server and Playit tunnels are always running."""
        if self.is_starting:
            return

        try:
            active = await self.is_server_active()
            if not active:
                logger.info("24/7 Watchdog: Minecraft server is not active. Auto-starting...")
                await self.run_ssh("sudo systemctl start minecraft")

            # Check Playit tunnel
            code, out = await self.run_ssh("systemctl is-active playit")
            if "active" not in out:
                logger.info("24/7 Watchdog: Playit service not active. Starting playit...")
                await self.run_ssh("sudo systemctl restart playit")

        except Exception as e:
            logger.error(f"Watchdog Error: {e}")

    @watchdog_24_7.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerPowerCog(bot))
