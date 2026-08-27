import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import re
from datetime import datetime, timezone
import database

logger = logging.getLogger("ChatBridge")

MC_HOST = "192.168.178.128"
MC_USER = "admin"
LOG_PATH = "/home/admin/minecraft/logs/latest.log"

# Regex patterns for Minecraft log parsing
RE_CHAT = re.compile(r"\[Server thread/INFO\]: <([^>]+)> (.+)")
RE_JOIN = re.compile(r"\[Server thread/INFO\]: (\w+|\.[a-zA-Z0-9_]+) joined the game")
RE_LEAVE = re.compile(r"\[Server thread/INFO\]: (\w+|\.[a-zA-Z0-9_]+) left the game")
RE_ADVANCEMENT = re.compile(r"\[Server thread/INFO\]: (\w+|\.[a-zA-Z0-9_]+) has made the advancement \[(.+)\]")
RE_CHALLENGE = re.compile(r"\[Server thread/INFO\]: (\w+|\.[a-zA-Z0-9_]+) has completed the challenge \[(.+)\]")
RE_GOAL = re.compile(r"\[Server thread/INFO\]: (\w+|\.[a-zA-Z0-9_]+) has reached the goal \[(.+)\]")

DEATH_KEYWORDS = [
    "was slain by", "fell from", "fell off", "drowned", "burned to death",
    "walked into fire", "was blown up", "blew up", "hit the ground too hard",
    "was shot by", "was pricked to death", "starved to death", "suffocated in a wall",
    "was squished", "experienced kinetic energy", "withered away", "died",
    "was killed by", "discovered floor was lava", "froze to death"
]

class ChatBridgeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tail_task = None
        self.is_running = True
        self.bot.loop.create_task(self.start_log_stream())

    def cog_unload(self):
        self.is_running = False
        if self.tail_task:
            self.tail_task.cancel()

    async def get_target_channel(self) -> discord.TextChannel | None:
        """Finds #smp-talk or #allgemein across guilds."""
        for guild in self.bot.guilds:
            for ch in guild.text_channels:
                if "smp-talk" in ch.name or "smp-chat" in ch.name:
                    return ch
        # Fallback to first general chat
        for guild in self.bot.guilds:
            for ch in guild.text_channels:
                if "allgemein" in ch.name or "general" in ch.name:
                    return ch
        return None

    async def start_log_stream(self):
        """Streams Minecraft logs over SSH in real time."""
        await self.bot.wait_until_ready()
        logger.info("Starting Minecraft Live Log Stream & Chat Bridge...")

        while self.is_running and not self.bot.is_closed():
            try:
                cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {MC_USER}@{MC_HOST} 'tail -n 0 -F {LOG_PATH}'"
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                while self.is_running and not self.bot.is_closed():
                    line_bytes = await proc.stdout.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if line:
                        await self.handle_log_line(line)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Log stream error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def handle_log_line(self, line: str):
        """Processes a single line from latest.log and routes to Discord."""
        target_channel = await self.get_target_channel()
        if not target_channel:
            return

        # 1. Ingame Chat Message
        chat_match = RE_CHAT.search(line)
        if chat_match:
            player_name, message = chat_match.groups()
            avatar_url = f"https://visage.surgeplay.com/face/64/{player_name.lstrip('.')}.png"
            embed = discord.Embed(
                description=message,
                color=discord.Color.from_rgb(46, 204, 113)
            )
            embed.set_author(name=f"[Minecraft] {player_name}", icon_url=avatar_url)
            await target_channel.send(embed=embed)
            return

        # 2. Player Join & Auto Starter-Kit
        join_match = RE_JOIN.search(line)
        if join_match:
            player_name = join_match.group(1)
            avatar_url = f"https://visage.surgeplay.com/face/64/{player_name.lstrip('.')}.png"
            embed = discord.Embed(
                description=f"🟢 **{player_name}** ist dem Server beigetreten!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=avatar_url)
            await target_channel.send(embed=embed)

            # Auto-Give Starter Kit if not already received
            try:
                from cogs.rcon_manager import run_rcon_cmd
                tag_check = run_rcon_cmd(f"tag {player_name} list")
                if "received_starter_kit" not in tag_check:
                    logger.info(f"Giving Starter Kit to new player: {player_name}")
                    run_rcon_cmd(f"tag {player_name} add received_starter_kit")
                    run_rcon_cmd(f"give {player_name} iron_sword 1")
                    run_rcon_cmd(f"give {player_name} iron_pickaxe 1")
                    run_rcon_cmd(f"give {player_name} iron_axe 1")
                    run_rcon_cmd(f"give {player_name} iron_shovel 1")
                    run_rcon_cmd(f"give {player_name} shield 1")
                    run_rcon_cmd(f"give {player_name} cooked_beef 32")
                    run_rcon_cmd(f"give {player_name} oak_log 32")
                    run_rcon_cmd(f"give {player_name} torch 32")
                    run_rcon_cmd(f"give {player_name} white_bed 1")
                    
                    welcome_title = (
                        f'tellraw {player_name} ["",'
                        f'{{"text":"\\n╔══════════════════════════════════════════════════╗\\n","color":"gold"}},'
                        f'{{"text":"  ⛏️ WILLKOMMEN AUF DEM SMP SERVER!\\n","color":"yellow","bold":true}},'
                        f'{{"text":"  Du hast dein automatisches Starter-Kit erhalten.\\n","color":"green"}},'
                        f'{{"text":"  Viel Erfolg beim Bauen, Farmen & Erkunden! 💎\\n","color":"aqua"}},'
                        f'{{"text":"╚══════════════════════════════════════════════════╝\\n","color":"gold"}}]'
                    )
                    run_rcon_cmd(welcome_title)
            except Exception as e:
                logger.error(f"Error giving starter kit to {player_name}: {e}")
            return

        # 3. Player Leave
        leave_match = RE_LEAVE.search(line)
        if leave_match:
            player_name = leave_match.group(1)
            embed = discord.Embed(
                description=f"🔴 **{player_name}** hat den Server verlassen.",
                color=discord.Color.red()
            )
            await target_channel.send(embed=embed)
            return

        # 4. Advancement / Achievement
        adv_match = RE_ADVANCEMENT.search(line) or RE_CHALLENGE.search(line) or RE_GOAL.search(line)
        if adv_match:
            player_name, adv_name = adv_match.groups()
            avatar_url = f"https://visage.surgeplay.com/face/64/{player_name.lstrip('.')}.png"
            embed = discord.Embed(
                title="🏆 Fortschritt erzielt!",
                description=f"**{player_name}** hat den Fortschritt **[{adv_name}]** freigeschaltet!",
                color=discord.Color.gold(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=avatar_url)
            await target_channel.send(embed=embed)
            return

        # 5. Death Message
        if "[Server thread/INFO]:" in line:
            content = line.split("[Server thread/INFO]:", 1)[1].strip()
            if any(keyword in content for keyword in DEATH_KEYWORDS):
                # Avoid matching join/leave or command outputs
                if not any(x in content for x in ["joined", "left", "UUID of", "RCON", "Saved"]):
                    embed = discord.Embed(
                        description=f"☠️ {content}",
                        color=discord.Color.dark_red()
                    )
                    await target_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Discord -> Ingame Chat Bridge: Forwards Discord chat to Minecraft."""
        if message.author.bot or not message.guild:
            return

        # Only forward from #smp-talk or #smp-chat
        if "smp-talk" in message.channel.name or "smp-chat" in message.channel.name:
            clean_content = message.clean_content.replace('"', '\\"').replace("'", "")
            if not clean_content.strip():
                return

            author_name = message.author.display_name.replace('"', '')

            # Send via RCON tellraw to Minecraft
            tellraw_cmd = (
                f'tellraw @a ['
                f'{{"text":"[Discord] ","color":"blue","bold":true}},'
                f'{{"text":"<{author_name}> ","color":"aqua"}},'
                f'{{"text":"{clean_content}","color":"white"}}'
                f']'
            )
            try:
                from cogs.rcon_manager import run_rcon_cmd
                run_rcon_cmd(tellraw_cmd)
            except Exception as e:
                logger.error(f"Error bridging message to Minecraft: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatBridgeCog(bot))
