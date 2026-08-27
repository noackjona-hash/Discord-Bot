import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging

logger = logging.getLogger("PlayerLookup")

class PlayerLookupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_player_data(self, player_name: str):
        """Fetches UUID from Mojang API."""
        url = f"https://api.mojang.com/users/profiles/minecraft/{player_name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        return None

    @app_commands.command(name="skin", description="Zeigt den Minecraft Skin & 3D-Modell eines Spielers an.")
    @app_commands.describe(player_name="Minecraft Ingame-Name (z.B. Notch, BastiGHG)")
    async def skin(self, interaction: discord.Interaction, player_name: str):
        await interaction.response.defer(thinking=True)
        data = await self.get_player_data(player_name)

        if not data:
            await interaction.followup.send(f"❌ Der Spieler **{player_name}** wurde nicht gefunden (nur offizielle Java Accounts).")
            return

        uuid = data["id"]
        exact_name = data["name"]

        # High resolution 3D render URLs from Visage / Minotar / Crafatar
        body_render = f"https://visage.surgeplay.com/full/512/{uuid}.png"
        head_render = f"https://visage.surgeplay.com/head/128/{uuid}.png"
        skin_download = f"https://visage.surgeplay.com/skin/{uuid}.png"

        embed = discord.Embed(
            title=f"🎨 Minecraft Skin von {exact_name}",
            url=f"https://namemc.com/profile/{exact_name}",
            color=discord.Color.from_rgb(0, 170, 255)
        )
        embed.set_thumbnail(url=head_render)
        embed.set_image(url=body_render)
        embed.add_field(name="🆔 UUID", value=f"`{uuid}`", inline=False)
        embed.add_field(name="🔗 Download & Links", value=f"[Skin herunterladen]({skin_download}) • [NameMC Profil](https://namemc.com/profile/{exact_name})", inline=False)
        embed.set_footer(text="3D Rendering von Visage API")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="player", description="Zeigt das vollständige Minecraft Spielerprofil mit UUID, NameMC & 3D-Büste.")
    @app_commands.describe(player_name="Minecraft Ingame-Name")
    async def player(self, interaction: discord.Interaction, player_name: str):
        await interaction.response.defer(thinking=True)
        data = await self.get_player_data(player_name)

        if not data:
            await interaction.followup.send(f"❌ Spieler **{player_name}** konnte nicht gefunden werden.")
            return

        uuid = data["id"]
        exact_name = data["name"]

        bust_render = f"https://visage.surgeplay.com/bust/512/{uuid}.png"
        avatar_face = f"https://visage.surgeplay.com/face/64/{uuid}.png"

        embed = discord.Embed(
            title=f"👤 Minecraft Profil: {exact_name}",
            url=f"https://namemc.com/profile/{exact_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=avatar_face)
        embed.set_image(url=bust_render)
        embed.add_field(name="Spielername", value=f"**{exact_name}**", inline=True)
        embed.add_field(name="UUID", value=f"`{uuid}`", inline=True)
        embed.add_field(name="Kopf-Befehl (Ingame)", value=f"```/give @p player_head[profile=\"{exact_name}\"]```", inline=False)
        embed.add_field(name="Links", value=f"🌐 [NameMC Profil ansehen](https://namemc.com/profile/{exact_name})", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="head", description="Gibt den Ingame-Befehl für den Kopf eines Spielers aus.")
    @app_commands.describe(player_name="Minecraft Ingame-Name")
    async def head(self, interaction: discord.Interaction, player_name: str):
        head_url = f"https://visage.surgeplay.com/head/256/{player_name}.png"
        embed = discord.Embed(
            title=f"🗿 Kopf von {player_name}",
            color=discord.Color.orange()
        )
        embed.set_image(url=head_url)
        embed.add_field(name="📦 Ingame Give-Befehl (1.20.5+):", value=f"```/give @p player_head[profile=\"{player_name}\"]```", inline=False)
        embed.add_field(name="📦 Ältere Versionen (1.13 - 1.20.4):", value=f"```/give @p minecraft:player_head{{SkullOwner:\"{player_name}\"}}```", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerLookupCog(bot))
