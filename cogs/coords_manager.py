import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import logging
from database import DB_PATH

logger = logging.getLogger("CoordsManager")

class WaypointSelect(discord.ui.Select):
    def __init__(self, waypoints):
        options = []
        for wp in waypoints[:25]:
            dim_emoji = "🌍" if wp["dimension"] == "Overworld" else "🔥" if wp["dimension"] == "Nether" else "🌌"
            label = f"{wp['name']} ({wp['dimension']})"[:100]
            desc = f"X: {wp['x']} | Z: {wp['z']}"[:100]
            options.append(discord.SelectOption(label=label, value=str(wp["id"]), description=desc, emoji=dim_emoji))

        super().__init__(placeholder="📍 Wähle einen Ort aus für Details & Portal-Berechnung...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        wp_id = int(self.values[0])
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM waypoints WHERE id = ?", (wp_id,)) as cursor:
                wp = await cursor.fetchone()

        if not wp:
            await interaction.response.send_message("❌ Ort nicht gefunden.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📍 {wp['name']} ({wp['dimension']})",
            description=wp['description'] or "*Keine Beschreibung vorhanden*",
            color=discord.Color.teal()
        )
        y_str = f", Y: {wp['y']}" if wp['y'] is not None else ""
        embed.add_field(name="📌 Koordinaten", value=f"**X:** `{wp['x']}`{y_str} **Z:** `{wp['z']}`", inline=False)

        # Dimension calculation
        if wp["dimension"] == "Overworld":
            nether_x = round(wp["x"] / 8)
            nether_z = round(wp["z"] / 8)
            embed.add_field(
                name="🔥 Entsprechende Nether-Koordinaten (Portal)",
                value=f"**X:** `{nether_x}` **Z:** `{nether_z}`",
                inline=False
            )
        elif wp["dimension"] == "Nether":
            ow_x = wp["x"] * 8
            ow_z = wp["z"] * 8
            embed.add_field(
                name="🌍 Entsprechende Overworld-Koordinaten (Portal)",
                value=f"**X:** `{ow_x}` **Z:** `{ow_z}`",
                inline=False
            )

        embed.set_footer(text=f"Eingetragen von {wp['created_by']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class WaypointsView(discord.ui.View):
    def __init__(self, waypoints):
        super().__init__(timeout=120)
        self.add_item(WaypointSelect(waypoints))


class CoordsGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="coords", description="Verwalte und berechne SMP-Wegpunkte & Koordinaten.")

    @app_commands.command(name="add", description="Fügt neue Koordinaten zur SMP-Datenbank hinzu.")
    @app_commands.describe(
        name="Name des Ortes (z.B. 'Jonas Base', 'Nether Fortress', 'Spawn Shop')",
        x="X-Koordinate",
        z="Z-Koordinate",
        y="Y-Koordinate (Höhe, optional)",
        dimension="Dimension (Overworld, Nether, End)",
        description="Optionale Zusatzinformationen"
    )
    @app_commands.choices(dimension=[
        app_commands.Choice(name="🌍 Overworld", value="Overworld"),
        app_commands.Choice(name="🔥 Nether", value="Nether"),
        app_commands.Choice(name="🌌 The End", value="End")
    ])
    async def add_coord(
        self,
        interaction: discord.Interaction,
        name: str,
        x: int,
        z: int,
        y: int = None,
        dimension: app_commands.Choice[str] = None,
        description: str = None
    ):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern ausführbar.", ephemeral=True)
            return

        dim_val = dimension.value if dimension else "Overworld"
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO waypoints (guild_id, name, dimension, x, y, z, description, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (interaction.guild.id, name, dim_val, x, y, z, description, interaction.user.display_name))
            await db.commit()

        embed = discord.Embed(
            title="✅ Wegpunkt gespeichert!",
            description=f"**{name}** wurde zur SMP-Karte hinzugefügt.",
            color=discord.Color.green()
        )
        embed.add_field(name="Dimension", value=dim_val, inline=True)
        y_val = f", Y: {y}" if y is not None else ""
        embed.add_field(name="Koordinaten", value=f"X: `{x}`{y_val} Z: `{z}`", inline=True)
        if description:
            embed.add_field(name="Info", value=description, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Listet alle gespeicherten SMP-Koordinaten auf.")
    @app_commands.describe(dimension="Filter nach Dimension (optional)")
    @app_commands.choices(dimension=[
        app_commands.Choice(name="🌍 Overworld", value="Overworld"),
        app_commands.Choice(name="🔥 Nether", value="Nether"),
        app_commands.Choice(name="🌌 The End", value="End")
    ])
    async def list_coords(self, interaction: discord.Interaction, dimension: app_commands.Choice[str] = None):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern möglich.", ephemeral=True)
            return

        query = "SELECT * FROM waypoints WHERE guild_id = ?"
        params = [interaction.guild.id]
        if dimension:
            query += " AND dimension = ?"
            params.append(dimension.value)
        query += " ORDER BY id DESC"

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                waypoints = await cursor.fetchall()

        if not waypoints:
            dim_str = f" in {dimension.name}" if dimension else ""
            await interaction.response.send_message(f"ℹ️ Keine gespeicherten Koordinaten{dim_str} gefunden. Erstelle welche mit `/coords add`!")
            return

        embed = discord.Embed(
            title="📍 Gespeicherte SMP-Wegpunkte",
            description=f"Insgesamt **{len(waypoints)}** Orte gespeichert. Wähle unten einen Ort aus für Details & Nether-Portal-Rechner:",
            color=discord.Color.blue()
        )

        for wp in waypoints[:10]:
            emoji = "🌍" if wp["dimension"] == "Overworld" else "🔥" if wp["dimension"] == "Nether" else "🌌"
            y_str = f" Y: {wp['y']}" if wp['y'] is not None else ""
            embed.add_field(
                name=f"{emoji} {wp['name']}",
                value=f"X: `{wp['x']}`{y_str} Z: `{wp['z']}` ({wp['dimension']})",
                inline=True
            )

        view = WaypointsView(waypoints)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="nether-calc", description="Berechnet sofort die entsprechenden Nether/Overworld-Portal-Koordinaten.")
    @app_commands.describe(
        x="X-Koordinate",
        z="Z-Koordinate",
        from_dimension="Ausgangs-Dimension (Standard: Overworld)"
    )
    @app_commands.choices(from_dimension=[
        app_commands.Choice(name="🌍 Von Overworld -> Nether", value="to_nether"),
        app_commands.Choice(name="🔥 Von Nether -> Overworld", value="to_overworld")
    ])
    async def nether_calc(self, interaction: discord.Interaction, x: int, z: int, from_dimension: app_commands.Choice[str] = None):
        direction = from_dimension.value if from_dimension else "to_nether"

        if direction == "to_nether":
            res_x = round(x / 8)
            res_z = round(z / 8)
            embed = discord.Embed(
                title="🔥 Portal-Rechner: Overworld ➔ Nether",
                description="Für eine perfekte 1:1 Portal-Verknüpfung im Nether:",
                color=discord.Color.red()
            )
            embed.add_field(name="🌍 Overworld Koordinaten", value=f"X: `{x}` | Z: `{z}`", inline=False)
            embed.add_field(name="🔥 Baue das Nether-Portal bei:", value=f"**X:** `{res_x}` | **Z:** `{res_z}`", inline=False)
            embed.set_footer(text="Formel: X/8, Z/8")
        else:
            res_x = x * 8
            res_z = z * 8
            embed = discord.Embed(
                title="🌍 Portal-Rechner: Nether ➔ Overworld",
                description="Für die entsprechende Position in der Overworld:",
                color=discord.Color.green()
            )
            embed.add_field(name="🔥 Nether Koordinaten", value=f"X: `{x}` | Z: `{z}`", inline=False)
            embed.add_field(name="🌍 Baue das Overworld-Portal bei:", value=f"**X:** `{res_x}` | **Z:** `{res_z}`", inline=False)
            embed.set_footer(text="Formel: X*8, Z*8")

        await interaction.response.send_message(embed=embed)


class CoordsManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(CoordsGroup())


async def setup(bot: commands.Bot):
    await bot.add_cog(CoordsManagerCog(bot))
