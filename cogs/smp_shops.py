import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import logging
from database import DB_PATH

logger = logging.getLogger("SMPShops")

class ShopStockButton(discord.ui.Button):
    def __init__(self, shop_id: int, owner_id: int, current_stock: bool):
        label = "Als Ausverkauft markieren" if current_stock else "Wieder auf Lager setzen"
        style = discord.ButtonStyle.danger if current_stock else discord.ButtonStyle.success
        super().__init__(label=label, style=style, custom_id=f"shop_stock_{shop_id}")
        self.shop_id = shop_id
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Nur der Shop-Besitzer oder Admins können den Lagerbestand ändern.", ephemeral=True)
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE shops SET in_stock = 1 - in_stock WHERE id = ?", (self.shop_id,))
            await db.commit()

        await interaction.response.send_message("✅ Lagerstatus aktualisiert! Rufe `/shop list` erneut auf.", ephemeral=True)


class ShopGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="shop", description="SMP Marktplatz: Verkaufe Items, kaufe ein & durchsuche Angebote.")

    @app_commands.command(name="add", description="Erstelle ein neues Verkaufsangebot im SMP Marktplatz.")
    @app_commands.describe(
        item_name="Item, das du verkaufst (z.B. 'Mending Buch', 'Elytra', 'Netherite Barren')",
        price="Preis (z.B. '5 Diamanten', '32 Smaragde')",
        location="Wo ist dein Shop? (z.B. 'Spawn Markt Stand 3', 'X: 120, Z: -450')",
        quantity="Menge pro Verkauf (Standard: 1)"
    )
    async def add_shop(
        self,
        interaction: discord.Interaction,
        item_name: str,
        price: str,
        location: str,
        quantity: int = 1
    ):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern ausführbar.", ephemeral=True)
            return

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                INSERT INTO shops (guild_id, owner_id, owner_name, item_name, quantity, price, location, in_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (interaction.guild.id, interaction.user.id, interaction.user.display_name, item_name, quantity, price, location))
            shop_id = cursor.lastrowid
            await db.commit()

        embed = discord.Embed(
            title="🛒 Neues Angebot im SMP-Marktplatz!",
            description=f"**{interaction.user.mention}** bietet ein neues Item zum Verkauf an:",
            color=discord.Color.gold()
        )
        embed.add_field(name="📦 Item", value=f"**{quantity}x {item_name}**", inline=True)
        embed.add_field(name="💎 Preis", value=f"`{price}`", inline=True)
        embed.add_field(name="📍 Ort / Shop", value=f"`{location}`", inline=True)
        embed.add_field(name="Status", value="🟢 **Auf Lager**", inline=True)
        embed.set_footer(text=f"Shop-ID: #{shop_id} • Kontaktiere den Verkäufer per DM oder Ingame!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Zeigt alle aktuellen Angebote im SMP-Marktplatz.")
    async def list_shops(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern möglich.", ephemeral=True)
            return

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM shops WHERE guild_id = ? ORDER BY in_stock DESC, id DESC LIMIT 15", (interaction.guild.id,)) as cursor:
                shops = await cursor.fetchall()

        if not shops:
            await interaction.response.send_message("ℹ️ Aktuell sind keine Angebote im Marktplatz vorhanden. Erstelle eines mit `/shop add`!")
            return

        embed = discord.Embed(
            title="🏪 SMP Marktplatz – Aktuelle Angebote",
            description=f"Hier findest du Waren von Mitspielern ({len(shops)} Angebote):",
            color=discord.Color.teal()
        )

        for s in shops:
            stock_badge = "🟢 Auf Lager" if s["in_stock"] else "🔴 Ausverkauft"
            embed.add_field(
                name=f"#{s['id']} {s['quantity']}x {s['item_name']} – {s['price']}",
                value=f"👤 **Verkäufer:** {s['owner_name']}\n📍 **Ort:** `{s['location']}`\n📊 **Status:** {stock_badge}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="search", description="Sucht nach einem bestimmten Item im Marktplatz.")
    @app_commands.describe(item="Name des gesuchten Items (z.B. 'Elytra', 'Buch')")
    async def search_shop(self, interaction: discord.Interaction, item: str):
        if not interaction.guild:
            return

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM shops WHERE guild_id = ? AND item_name LIKE ? ORDER BY in_stock DESC", (interaction.guild.id, f"%{item}%")) as cursor:
                results = await cursor.fetchall()

        if not results:
            await interaction.response.send_message(f"🔍 Kein Angebot für **{item}** gefunden.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🔍 Suchergebnisse für: {item}",
            description=f"**{len(results)}** Angebote gefunden:",
            color=discord.Color.blue()
        )
        for s in results:
            stock_badge = "🟢 Auf Lager" if s["in_stock"] else "🔴 Ausverkauft"
            embed.add_field(
                name=f"#{s['id']} {s['quantity']}x {s['item_name']} für {s['price']}",
                value=f"👤 {s['owner_name']} | 📍 `{s['location']}` | {stock_badge}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete", description="Löscht eines deiner Shop-Angebote.")
    @app_commands.describe(shop_id="ID des Shops (z.B. 1, 2)")
    async def delete_shop(self, interaction: discord.Interaction, shop_id: int):
        if not interaction.guild:
            return

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM shops WHERE id = ? AND guild_id = ?", (shop_id, interaction.guild.id)) as cursor:
                shop = await cursor.fetchone()

            if not shop:
                await interaction.response.send_message("❌ Shop-ID nicht gefunden.", ephemeral=True)
                return

            if shop["owner_id"] != interaction.user.id and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Du kannst nur deine eigenen Angebote löschen.", ephemeral=True)
                return

            await db.execute("DELETE FROM shops WHERE id = ?", (shop_id,))
            await db.commit()

        await interaction.response.send_message(f"🗑️ Shop-Angebot **#{shop_id} ({shop['item_name']})** gelöscht.", ephemeral=True)


class SMPShopsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(ShopGroup())


async def setup(bot: commands.Bot):
    await bot.add_cog(SMPShopsCog(bot))
