import os
import sys
import time
import logging
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DiscordBot")

# Bot Intents
intents = discord.Intents.default()

class UltimateSMPBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # 1. Initialize SQLite Database
        await database.init_db()

        # 2. Register Persistent Views (Buttons survive restarts)
        from cogs.server_setup import RoleSelectionView, VerifyRulesView
        from cogs.unban_system import UnbanApplyView
        from cogs.whitelist_system import WhitelistApplyView
        self.add_view(RoleSelectionView())
        self.add_view(VerifyRulesView())
        self.add_view(UnbanApplyView())
        self.add_view(WhitelistApplyView())

        # 3. Load all Cogs in cogs/ directory
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    extension = f"cogs.{filename[:-3]}"
                    try:
                        await self.load_extension(extension)
                        logger.info(f"Loaded extension: {extension}")
                    except Exception as e:
                        logger.error(f"Failed to load extension {extension}: {e}", exc_info=True)

        # 4. Global sync
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} application slash command(s) globally.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"============================================================")
        logger.info(f"🚀 Bot online: {self.user} (ID: {self.user.id})")
        logger.info(f"🌐 Connected to {len(self.guilds)} Discord Server(s)")
        logger.info(f"🍓 Running on Raspberry Pi 4B")
        logger.info(f"============================================================")

        # Instant Guild Sync (Fixes 'Command outdated' / 'Befehl veraltet' client cache)
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Instantly synced {len(synced)} commands to guild: '{guild.name}' (ID: {guild.id})")
            except Exception as e:
                logger.warning(f"Could not guild-sync to {guild.id}: {e}")

        # Set rich presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Minecraft SMP | /help | !setup-smp"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_guild_join(self, guild):
        try:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands on joining new guild: {guild.name}")
        except Exception as e:
            logger.warning(f"Error syncing on guild join: {e}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")

bot = UltimateSMPBot()

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN_HERE" or token.strip() == "":
        logger.error("=" * 60)
        logger.error("FEHLER: Kein DISCORD_TOKEN in der .env-Datei gefunden!")
        logger.error("=" * 60)
        sys.exit(1)

    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Ungültiger Discord Token!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Starten des Bots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
