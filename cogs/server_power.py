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
DEFAULT_IDLE_TIMEOUT = 15  # 15 minutes

class ServerPowerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.idle_minutes = 0
        self.auto_shutdown_enabled = True
        self.timeout_minutes = DEFAULT_IDLE_TIMEOUT
        self.is_starting = False
        self.auto_shutdown_loop.start()

    def cog_unload(self):
        self.auto_shutdown_loop.cancel()

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

    @app_commands.command(name="mc-start", description="Fährt den Minecraft SMP Server hoch (falls er offline ist).")
    async def mc_start(self, interaction: discord.Interaction):
        if self.is_starting:
            await interaction.response.send_message("⏳ Der Server fährt gerade bereits hoch. Bitte habe einen kurzen Moment Geduld!", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        if await self.is_server_active():
            await interaction.followup.send("🟢 Der Minecraft Server läuft bereits und ist online! (IP: `192.168.178.128`)")
            return

        self.is_starting = True
        self.idle_minutes = 0

        embed = discord.Embed(
            title="🚀 Minecraft Server wird hochgefahren...",
            description="Starte Fabric + Geyser Server auf dem Host...\nBitte warte ca. **10 - 25 Sekunden**.",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        msg = await interaction.followup.send(embed=embed)

        try:
            # Start service via SSH
            code, out = await self.run_ssh("sudo systemctl start minecraft")
            if code != 0:
                self.is_starting = False
                await interaction.followup.send(f"❌ Fehler beim Starten des Servers: `{out}`")
                return

            # Poll for server ready
            online = False
            for _ in range(25):
                await asyncio.sleep(2)
                try:
                    server = await JavaServer.async_lookup(f"{MC_HOST}:25565", timeout=2)
                    status = await server.async_status()
                    online = True
                    break
                except Exception:
                    continue

            self.is_starting = False

            if online:
                embed_ready = discord.Embed(
                    title="🎉 Minecraft SMP Server ist BEREIT!",
                    description="Der Server wurde erfolgreich gestartet und wartet auf Spieler.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_ready.add_field(name="☕ Java Edition (PC)", value="`192.168.178.128:25565`", inline=True)
                embed_ready.add_field(name="📱 Bedrock / Handy / Konsole", value="`192.168.178.128:19132`", inline=True)
                embed_ready.set_footer(text=f"Auto-Sleep nach {self.timeout_minutes} Minuten Inaktivität aktiv.")
                await interaction.channel.send(embed=embed_ready)
            else:
                embed_slow = discord.Embed(
                    title="⏳ Server startet noch...",
                    description="Der Dienst wurde gestartet. Die Welt wird geladen und sollte in wenigen Sekunden erreichbar sein.\nPrüfe den Status mit `/mcstatus`.",
                    color=discord.Color.orange()
                )
                await interaction.channel.send(embed=embed_slow)

        except Exception as e:
            self.is_starting = False
            logger.error(f"Fehler bei mc_start: {e}")
            await interaction.channel.send(f"❌ Fehler beim Hochfahren: `{e}`")

    @app_commands.command(name="mc-stop", description="Fährt den Minecraft Server manuell herunter (Nur Admins).")
    @app_commands.default_permissions(administrator=True)
    async def mc_stop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        if not await self.is_server_active():
            await interaction.followup.send("🔴 Der Minecraft Server ist bereits offline.", ephemeral=True)
            return

        # Announce and save in-game
        try:
            from cogs.rcon_manager import run_rcon_cmd
            run_rcon_cmd('say [Discord] Server wird in 5 Sekunden heruntergefahren...')
            run_rcon_cmd('save-all')
        except Exception:
            pass

        await asyncio.sleep(2)
        code, out = await self.run_ssh("sudo systemctl stop minecraft")

        self.idle_minutes = 0
        embed = discord.Embed(
            title="🛑 Minecraft Server heruntergefahren",
            description="Der Server wurde gestoppt. Er kann jederzeit mit `/mc-start` wieder gestartet werden.",
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

        code, out = await self.run_ssh("sudo systemctl restart minecraft")
        self.idle_minutes = 0

        embed = discord.Embed(
            title="🔄 Minecraft Server wird neu gestartet...",
            description="Der Neustart wurde eingeleitet. In ca. 15-20 Sekunden ist der Server wieder erreichbar.",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="mc-autostop", description="Konfiguriert die automatische Abschaltung bei Inaktivität.")
    @app_commands.describe(
        enabled="Auto-Shutdown aktivieren oder deaktivieren",
        minutes="Minuten Inaktivität vor dem Abschalten (Standard: 15)"
    )
    @app_commands.default_permissions(administrator=True)
    async def mc_autostop(self, interaction: discord.Interaction, enabled: bool = True, minutes: int = 15):
        self.auto_shutdown_enabled = enabled
        self.timeout_minutes = max(5, minutes)
        self.idle_minutes = 0

        state_str = "Aktiviert ✅" if enabled else "Deaktiviert ❌"
        embed = discord.Embed(
            title="⚙️ Auto-Shutdown Konfiguration",
            description=f"Status: **{state_str}**\nTimeout: **{self.timeout_minutes} Minuten** Inaktivität",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @tasks.loop(minutes=1)
    async def auto_shutdown_loop(self):
        """Monitors player count every minute and shuts down after inactivity."""
        if not self.auto_shutdown_enabled or self.is_starting:
            return

        try:
            active = await self.is_server_active()
            if not active:
                self.idle_minutes = 0
                return

            # Check online players via mcstatus
            try:
                server = await JavaServer.async_lookup(f"{MC_HOST}:25565", timeout=3)
                status = await server.async_status()
                player_count = status.players.online
            except Exception:
                # If cannot reach ping while service is active, could be starting up
                return

            if player_count > 0:
                # Players are active, reset idle counter
                if self.idle_minutes > 0:
                    logger.info(f"Players online ({player_count}). Resetting idle timer.")
                self.idle_minutes = 0
            else:
                # No players online
                self.idle_minutes += 1
                logger.info(f"Minecraft server idle: {self.idle_minutes}/{self.timeout_minutes} minute(s).")

                # In-game warning at 5 minutes before shutdown
                if self.idle_minutes == max(1, self.timeout_minutes - 5):
                    try:
                        from cogs.rcon_manager import run_rcon_cmd
                        run_rcon_cmd(f'tellraw @a {{"text":"[Auto-Sleep] Server wird in 5 Minuten heruntergefahren, da keine Spieler online sind.","color":"yellow"}}')
                    except Exception:
                        pass

                # Reached timeout -> Shut down
                if self.idle_minutes >= self.timeout_minutes:
                    logger.info(f"Auto-shutting down Minecraft server after {self.timeout_minutes} min inactivity.")
                    
                    # Graceful in-game save
                    try:
                        from cogs.rcon_manager import run_rcon_cmd
                        run_rcon_cmd('say [Auto-Sleep] Server faehrt in den Ruhezustand...')
                        run_rcon_cmd('save-all')
                        run_rcon_cmd('stop')
                    except Exception:
                        pass

                    await asyncio.sleep(4)
                    await self.run_ssh("sudo systemctl stop minecraft")

                    self.idle_minutes = 0

                    # Notify Discord Channels
                    embed_sleep = discord.Embed(
                        title="💤 Minecraft Server im Ruhezustand (Auto-Sleep)",
                        description=(
                            f"Da **{self.timeout_minutes} Minuten** lang kein Spieler mehr online war, "
                            f"wurde der Minecraft Server automatisch heruntergefahren, um Strom & Ressourcen zu sparen.\n\n"
                            f"👉 **Möchtest du spielen?** Tippe einfach **/mc-start** in Discord!"
                        ),
                        color=discord.Color.from_rgb(100, 110, 240),
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed_sleep.set_footer(text="Auto-Sleep Modus aktiv")

                    # Broadcast to active Discord guilds
                    for guild in self.bot.guilds:
                        target = None
                        for ch in guild.text_channels:
                            if "ankündig" in ch.name or "allgemein" in ch.name or "smp-talk" in ch.name:
                                target = ch
                                break
                        if target:
                            try:
                                await target.send(embed=embed_sleep)
                            except Exception:
                                pass

        except Exception as e:
            logger.error(f"Fehler im Auto-Shutdown Loop: {e}")

    @auto_shutdown_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerPowerCog(bot))
