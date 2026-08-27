import discord
from discord import app_commands
from discord.ext import commands
import math

class MCToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="calc-blocks", description="Berechnet Blöcke, Stacks und Doppelkisten für Bauprojekte.")
    @app_commands.describe(
        length="Länge (in Blöcken)",
        width="Breite (in Blöcken)",
        height="Höhe (in Blöcken)",
        hollow="Ist das Gebäude innen hohl? (Standard: True)"
    )
    async def calc_blocks(self, interaction: discord.Interaction, length: int, width: int, height: int, hollow: bool = True):
        if hollow:
            if length <= 2 or width <= 2:
                total_blocks = length * width * height
            else:
                outer = length * width * height
                inner = (length - 2) * (width - 2) * max(1, height - 2)
                total_blocks = outer - inner
        else:
            total_blocks = length * width * height

        stacks = total_blocks / 64
        shulkers = total_blocks / (64 * 27)
        double_chests = total_blocks / (64 * 54)

        embed = discord.Embed(
            title="🏗️ Bauprojekt Material-Rechner",
            description=f"Maße: **{length}x{width}x{height}** Blöcke ({'Hohl' if hollow else 'Massiv'})",
            color=discord.Color.orange()
        )
        embed.add_field(name="🧱 Gesamtblöcke", value=f"**{total_blocks:,}** Blöcke", inline=False)
        embed.add_field(name="📦 Stacks (64er)", value=f"**{stacks:.1f}** Stacks ({math.ceil(stacks)} angefangen)", inline=True)
        embed.add_field(name="🎒 Shulker-Kisten", value=f"**{shulkers:.2f}** Shulker", inline=True)
        embed.add_field(name="🧰 Doppelkisten", value=f"**{double_chests:.2f}** Kisten", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="enchant-guide", description="Zeigt die besten Verzauberungen für Rüstung, Waffen & Werkzeuge.")
    @app_commands.describe(item="Gegenstand auswählen")
    @app_commands.choices(item=[
        app_commands.Choice(name="⚔️ Schwert (Sword)", value="sword"),
        app_commands.Choice(name="🔨 Streitkolben (Mace)", value="mace"),
        app_commands.Choice(name="⛏️ Spitzhacke (Pickaxe)", value="pickaxe"),
        app_commands.Choice(name="🪓 Axt (Axe)", value="axe"),
        app_commands.Choice(name="🏹 Bogen & Armbrust", value="bow"),
        app_commands.Choice(name="🛡️ Rüstung (Armor Set)", value="armor"),
        app_commands.Choice(name="🪽 Elytra & Dreizack", value="elytra_trident"),
    ])
    async def enchant_guide(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        guides = {
            "sword": (
                "⚔️ Bestes Schwert (God Sword)",
                "• **Schärfe V (Sharpness V)**\n• **Plünderung III (Looting III)**\n• **Schwungkraft III (Sweeping Edge III)**\n• **Haltbarkeit III (Unbreaking III)**\n• **Reparatur (Mending)**\n• **Verbrennung II (Fire Aspect II)** *(optional)*\n• **Rückstoß II (Knockback II)** *(situativ)*"
            ),
            "mace": (
                "🔨 Bester Streitkolben (Mace)",
                "• **Dichte V (Density V)** oder **Bresche IV (Breach IV)**\n• **Windstoß III (Wind Burst III)**\n• **Haltbarkeit III (Unbreaking III)**\n• **Reparatur (Mending)**\n• **Verbrennung II (Fire Aspect II)**"
            ),
            "pickaxe": (
                "⛏️ Beste Spitzhacken",
                "**Glück-Spitzhacke:**\n• Effizienz V\n• Glück III (Fortune III)\n• Haltbarkeit III\n• Reparatur (Mending)\n\n**Behutsamkeit-Spitzhacke:**\n• Effizienz V\n• Behutsamkeit (Silk Touch)\n• Haltbarkeit III\n• Reparatur (Mending)"
            ),
            "axe": (
                "🪓 Beste Axt (Kampf & Holz)",
                "• **Effizienz V**\n• **Schärfe V (Sharpness V)**\n• **Haltbarkeit III**\n• **Reparatur (Mending)**\n• **Behutsamkeit** oder **Glück III**"
            ),
            "bow": (
                "🏹 Bester Bogen & Armbrust",
                "**Bogen:**\n• Stärke V (Power V)\n• Schlag II (Punch II)\n• Flamme (Flame)\n• Haltbarkeit III\n• *Entweder:* Unendlichkeit (Infinity) *oder* Reparatur (Mending)\n\n**Armbrust:**\n• Schnellladen III (Quick Charge III)\n• Mehrfachschuss (Multishot) oder Durchschuss IV (Piercing IV)\n• Haltbarkeit III & Reparatur"
            ),
            "armor": (
                "🛡️ Bestes Rüstungs-Set (God Armor)",
                "**Helm:** Schutz IV, Haltbarkeit III, Reparatur, Atmung III, Wasseraffinität\n**Brustpanzer:** Schutz IV, Haltbarkeit III, Reparatur\n**Hose:** Schutz IV, Haltbarkeit III, Reparatur, Flinkes Schleichen III (Swift Sneak)\n**Stiefel:** Schutz IV, Haltbarkeit III, Reparatur, Federfall IV, Wasserläufer III, Seelenläufer III"
            ),
            "elytra_trident": (
                "🪽 Elytra & 🔱 Dreizack",
                "**Elytra:**\n• Haltbarkeit III (Unbreaking III)\n• Reparatur (Mending)\n\n**Dreizack (Mobilität/Fliegen):**\n• Sog III (Riptide III), Haltbarkeit III, Reparatur\n\n**Dreizack (Kampf/Blitz):**\n• Loyalität III, Kanalisierung (Channeling), Harpune V (Impaling), Haltbarkeit III, Reparatur"
            )
        }

        title, content = guides[item.value]
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Minecraft 1.21+ Verzauberungs-Guide")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="potion-guide", description="Braurezepte für wichtige Minecraft Tränke.")
    @app_commands.describe(potion="Trank auswählen")
    @app_commands.choices(potion=[
        app_commands.Choice(name="💨 Schnelligkeit (Speed II)", value="speed"),
        app_commands.Choice(name="💪 Stärke (Strength II)", value="strength"),
        app_commands.Choice(name="👁️ Nachtsicht & Unsichtbarkeit", value="night_invis"),
        app_commands.Choice(name="❤️ Heilung & Regeneration", value="heal_regen"),
        app_commands.Choice(name="🪶 Sanfter Fall (Slow Falling)", value="slow_fall"),
        app_commands.Choice(name="🔥 Feuerresistenz", value="fire_res")
    ])
    async def potion_guide(self, interaction: discord.Interaction, potion: app_commands.Choice[str]):
        recipes = {
            "speed": (
                "💨 Schnelligkeitstrank (Speed II)",
                "1. **Wasserflasche** + **Netherwarze** ➔ *Seltsamer Trank (Awkward Potion)*\n2. + **Zucker** ➔ *Schnelligkeit I (3:00)*\n3. + **Leuchtsteinstaub (Glowstone)** ➔ **Schnelligkeit II (1:30)**\n*(Oder Redstone für Speed I 8:00)*"
            ),
            "strength": (
                "💪 Stärketrank (Strength II)",
                "1. **Wasserflasche** + **Netherwarze** ➔ *Seltsamer Trank*\n2. + **Lohenstaub (Blaze Powder)** ➔ *Stärke I (3:00)*\n3. + **Leuchtsteinstaub** ➔ **Stärke II (1:30)**"
            ),
            "night_invis": (
                "👁️ Nachtsicht & Unsichtbarkeit",
                "**Nachtsicht:**\n1. Seltsamer Trank + **Goldene Karotte** ➔ *Nachtsicht (3:00)*\n2. + **Redstone** ➔ **Nachtsicht (8:00)**\n\n**Unsichtbarkeit:**\n3. Nachtsichttrank + **Fermentiertes Spinnenauge** ➔ **Unsichtbarkeit (3:00 / 8:00 mit Redstone)**"
            ),
            "heal_regen": (
                "❤️ Heilung (Instant Health II) & Regeneration",
                "**Sofortige Heilung II:**\n1. Seltsamer Trank + **Glitzernde Melonenscheibe** ➔ *Heilung I*\n2. + **Leuchtsteinstaub** ➔ **Heilung II**\n\n**Regeneration II:**\n1. Seltsamer Trank + **Ghast-Träne** ➔ *Regeneration I*\n2. + **Leuchtsteinstaub** ➔ **Regeneration II**"
            ),
            "slow_fall": (
                "🪶 Sanfter Fall (Slow Falling - Perfekt für den Drachenkampf & End)",
                "1. **Wasserflasche** + **Netherwarze** ➔ *Seltsamer Trank*\n2. + **Phantomhaut (Phantom Membrane)** ➔ **Sanfter Fall (1:30)**\n3. + **Redstone** ➔ **Sanfter Fall (4:00)**"
            ),
            "fire_res": (
                "🔥 Feuerresistenz (Fire Resistance - 8 Minuten)",
                "1. **Wasserflasche** + **Netherwarze** ➔ *Seltsamer Trank*\n2. + **Magmacreme** ➔ *Feuerresistenz (3:00)*\n3. + **Redstone** ➔ **Feuerresistenz (8:00)**"
            )
        }

        title, content = recipes[potion.value]
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.dark_magenta()
        )
        embed.set_footer(text="Benötigt Lohenstaub als Brennstoff für den Braustand")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MCToolsCog(bot))
