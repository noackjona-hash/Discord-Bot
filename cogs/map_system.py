import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger("MapSystem")

SEED = "5252518894722547927"
CHUNKBASE_URL = f"https://www.chunkbase.com/apps/seed-map#seed={SEED}&version=1.21"
LOCAL_DASHBOARD_URL = "http://192.168.178.128:8080"

class MapSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="map", description="Zeigt die interaktive Web-Karte des SMPs (Biome, Spawns, Festungen & Städte).")
    async def map_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🗺️ Minecraft SMP – Interaktive Web-Karte & Seed",
            description=(
                f"Erkunde unsere Minecraft-Welt im Browser mit detaillierter Biome- und Struktur-Übersicht!\n\n"
                f"🌱 **World Seed:**\n"
                f"```\n{SEED}\n```\n"
                f"🌐 **Interaktive Karten-Links:**\n"
                f"• [🗺️ **Chunkbase Seed-Map (Hier klicken)]({CHUNKBASE_URL})**\n"
                f"  *(Findet Festungen, Antike Städte, Trial Chambers, Schleim-Chunks & Biome)*\n\n"
                f"• [📊 **Server Web-Dashboard (Im Heimnetz)]({LOCAL_DASHBOARD_URL})**\n"
                f"  *(Server-Status, Backups & Performance)*"
            ),
            color=discord.Color.from_rgb(52, 152, 219)
        )
        embed.set_thumbnail(url="https://visage.surgeplay.com/bust/128/Steve.png")
        embed.add_field(name="🧭 Orientierungs-Tipp", value="Nutze `/coords list` für gespeicherte Spieler-Basen oder `/coords nether-calc` für Portal-Koordinaten!", inline=False)
        embed.set_footer(text="Minecraft 1.21.x Generator")

        # Create a view with direct link buttons
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Chunkbase Karte öffnen 🗺️", url=CHUNKBASE_URL, style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="Web-Dashboard 📊", url=LOCAL_DASHBOARD_URL, style=discord.ButtonStyle.link))

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MapSystemCog(bot))
