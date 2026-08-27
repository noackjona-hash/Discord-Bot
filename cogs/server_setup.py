import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import logging

logger = logging.getLogger("ServerSetup")

class RoleButton(discord.ui.Button):
    def __init__(self, role_name: str, emoji: str, custom_id: str, style: discord.ButtonStyle):
        super().__init__(label=role_name, emoji=emoji, custom_id=custom_id, style=style)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            # Create if missing
            role = await guild.create_role(name=self.role_name, mentionable=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ Rolle **{self.role_name}** entfernt.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rolle **{self.role_name}** vergeben!", ephemeral=True)


class RoleSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        roles = [
            ("🔔 Ankündigungen", "🔔", "role_announcements", discord.ButtonStyle.primary),
            ("⛏️ Minenarbeiter", "⛏️", "role_miner", discord.ButtonStyle.secondary),
            ("🏗️ Baumeister", "🏗️", "role_builder", discord.ButtonStyle.secondary),
            ("⚔️ Krieger", "⚔️", "role_warrior", discord.ButtonStyle.secondary),
            ("⚡ Redstone-Ingenieur", "⚡", "role_redstone", discord.ButtonStyle.secondary),
        ]
        for name, emoji, cid, style in roles:
            self.add_item(RoleButton(name, emoji, cid, style))


class ServerSetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup-smp", description="Richtet diesen Discord-Server komplett für ein Minecraft SMP ein.")
    @app_commands.describe(server_name="Name des SMP-Projekts (z. B. 'Jona & Friends SMP')")
    @app_commands.default_permissions(administrator=True)
    async def setup_smp(self, interaction: discord.Interaction, server_name: str = "Minecraft SMP"):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern ausführbar.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        guild = interaction.guild

        try:
            # 1. Rollen erstellen
            roles_data = [
                {"name": "👑 Admin", "color": discord.Color.gold(), "hoist": True},
                {"name": "🛡️ Moderator", "color": discord.Color.blue(), "hoist": True},
                {"name": "⛏️ SMP Member", "color": discord.Color.green(), "hoist": True},
                {"name": "🔔 Ankündigungen", "color": discord.Color.teal(), "hoist": False},
                {"name": "⛏️ Minenarbeiter", "color": discord.Color.dark_gray(), "hoist": False},
                {"name": "🏗️ Baumeister", "color": discord.Color.orange(), "hoist": False},
                {"name": "⚔️ Krieger", "color": discord.Color.red(), "hoist": False},
                {"name": "⚡ Redstone-Ingenieur", "color": discord.Color.purple(), "hoist": False},
            ]

            for r in roles_data:
                if not discord.utils.get(guild.roles, name=r["name"]):
                    await guild.create_role(name=r["name"], color=r["color"], hoist=r["hoist"], mentionable=True)

            everyone_role = guild.default_role
            read_only_overwrites = {
                everyone_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
            }

            # 2. Kategorien & Channels
            # INFO
            cat_info = await guild.create_category("📌 WILLKOMMEN & INFO")
            chan_rules = await guild.create_text_channel("📜-regeln", category=cat_info, overwrites=read_only_overwrites)
            chan_news = await guild.create_text_channel("📢-ankündigungen", category=cat_info, overwrites=read_only_overwrites)
            chan_info = await guild.create_text_channel("ℹ️-server-info", category=cat_info, overwrites=read_only_overwrites)
            chan_roles = await guild.create_text_channel("🎭-rollen-auswahl", category=cat_info, overwrites=read_only_overwrites)

            # COMMUNITY
            cat_comm = await guild.create_category("💬 COMMUNITY")
            await guild.create_text_channel("💬-allgemein", category=cat_comm)
            await guild.create_text_channel("⛏️-smp-talk", category=cat_comm)
            await guild.create_text_channel("📸-screenshots-clips", category=cat_comm)
            await guild.create_text_channel("🤖-bot-befehle", category=cat_comm)

            # SMP PROJEKTE & WIRTSCHAFT
            cat_smp = await guild.create_category("🤝 HANDEL & PROJEKTE")
            await guild.create_text_channel("🛒-shops-und-handel", category=cat_smp)
            await guild.create_text_channel("🏗️-bauprojekte", category=cat_smp)
            await guild.create_text_channel("📍-koordinaten", category=cat_smp)
            await guild.create_text_channel("🗺️-dynmap-links", category=cat_smp)

            # VOICE
            cat_voice = await guild.create_category("🔊 SPRACHKANÄLE")
            await guild.create_voice_channel("🔊 Talk 1 (Unbegrenzt)", category=cat_voice)
            await guild.create_voice_channel("🔊 Talk 2 (Duo)", category=cat_voice, user_limit=2)
            await guild.create_voice_channel("🔊 Talk 3 (Squad)", category=cat_voice, user_limit=4)
            await guild.create_voice_channel("⛏️ Mining & Farmen", category=cat_voice)
            await guild.create_voice_channel("⚔️ Bossfight / End", category=cat_voice)
            await guild.create_voice_channel("💤 AFK", category=cat_voice)

            # 3. Regelwerk Embed
            embed_rules = discord.Embed(
                title=f"📜 {server_name} – Offizielles Regelwerk",
                description="Damit wir alle Spaß haben, befolge bitte die folgenden Grundregeln:",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed_rules.add_field(name="1️⃣ Kein Griefing & Diebstahl", value="Fremde Bauwerke dürfen nicht beschädigt werden. Nichts ohne Erlaubnis aus Kisten entnehmen.", inline=False)
            embed_rules.add_field(name="2️⃣ Respekt & Fairplay", value="Toxizität, Beleidigungen und unangebrachtes Verhalten sind verboten.", inline=False)
            embed_rules.add_field(name="3️⃣ Keine Cheats / Unfaire Mods", value="X-Ray, Fly-Hacks, Autoclicker oder Duping führen zu einem sofortigen Bann.", inline=False)
            embed_rules.add_field(name="4️⃣ Basen-Abstand", value="Baue nicht direkt neben anderen Spielern ohne vorherige Absprache.", inline=False)
            embed_rules.add_field(name="5️⃣ Handel & Wirtschaft", value="Handel fair in Diamanten oder Tauschwaren im Kanal `#shops-und-handel`.", inline=False)
            embed_rules.set_footer(text=f"{server_name} • Fairplay ist Ehrensache!")
            await chan_rules.send(embed=embed_rules)

            # 4. Server-Info Embed
            embed_info = discord.Embed(
                title=f"ℹ️ {server_name} – Server-Informationen",
                description="Alle Details, um dem Minecraft SMP Server beizutreten:",
                color=discord.Color.gold(),
                timestamp=datetime.now(timezone.utc)
            )
            embed_info.add_field(name="🌐 Server-IP", value="`Wird vom Admin eingetragen`", inline=True)
            embed_info.add_field(name="🎮 Version", value="`Java 1.21.x`", inline=True)
            embed_info.add_field(name="🔒 Whitelist", value="Aktiviert (Admin anschreiben)", inline=True)
            embed_info.add_field(name="🤖 Bot-Funktionen", value="Nutze `/mcstatus`, `/coords`, `/shop`, `/skin` und `/calc-nether`!", inline=False)
            await chan_info.send(embed=embed_info)

            # 5. Rollenauswahl Embed & View
            embed_role_select = discord.Embed(
                title="🎭 Wähle deine SMP-Rollen & Benachrichtigungen",
                description="Klicke auf die Buttons unten, um dir Rollen zu geben oder zu entfernen:",
                color=discord.Color.blue()
            )
            embed_role_select.add_field(name="🔔 Ankündigungen", value="Werde benachrichtigt bei Events & Updates.", inline=False)
            embed_role_select.add_field(name="⛏️ / 🏗️ / ⚔️ / ⚡ Spezialisierungen", value="Zeige anderen Spielern deine Spezialisierung im SMP!", inline=False)
            await chan_roles.send(embed=embed_role_select, view=RoleSelectionView())

            # Bestätigung
            confirm = discord.Embed(
                title="🎉 SMP Server-Setup erfolgreich abgeschlossen!",
                description=f"Der Server **{guild.name}** wurde mit allen Kanälen, Rollen, Berechtigungen und interaktiven Buttons für **{server_name}** eingerichtet.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=confirm)

        except Exception as e:
            logger.error(f"Fehler bei setup_smp: {e}")
            await interaction.followup.send(f"❌ Fehler beim Setup: `{e}`")

    @app_commands.command(name="setup-roles", description="Sendet das interaktive Rollen-Auswahl-Panel in den aktuellen Kanal.")
    @app_commands.default_permissions(administrator=True)
    async def setup_roles(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎭 Wähle deine Rollen",
            description="Klicke auf einen Button, um die entsprechende Rolle zu erhalten oder abzuwählen.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=RoleSelectionView())

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerSetupCog(bot))
