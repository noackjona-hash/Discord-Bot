import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import logging
import asyncio

logger = logging.getLogger("ServerSetup")

class RoleButton(discord.ui.Button):
    def __init__(self, role_name: str, emoji: str, custom_id: str, style: discord.ButtonStyle):
        super().__init__(label=role_name, emoji=emoji, custom_id=custom_id, style=style)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
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

    async def execute_smp_setup(self, guild: discord.Guild, server_name: str, clean_old: bool, sender):
        """Core logic to build SMP server structure cleanly."""
        try:
            # 1. Altes SMP Setup bereinigen falls gewünscht
            if clean_old:
                smp_categories = ["WILLKOMMEN", "COMMUNITY", "HANDEL", "PROJEKTE", "SPRACHKANÄLE", "INFO"]
                for cat in list(guild.categories):
                    if any(key in cat.name.upper() for key in smp_categories):
                        for ch in list(cat.channels):
                            try:
                                await ch.delete(reason="SMP Re-Setup Bereinigung")
                            except Exception:
                                pass
                        try:
                            await cat.delete(reason="SMP Re-Setup Bereinigung")
                        except Exception:
                            pass
                await asyncio.sleep(1)

            # 2. Rollen erstellen falls nicht vorhanden
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
                    try:
                        await guild.create_role(name=r["name"], color=r["color"], hoist=r["hoist"], mentionable=True)
                    except Exception as e:
                        logger.warning(f"Konnte Rolle {r['name']} nicht erstellen: {e}")

            everyone_role = guild.default_role
            read_only_overwrites = {
                everyone_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
            }

            # 3. Kategorien & Kanäle erstellen (oder wiederverwenden)
            async def get_or_create_cat(name: str):
                cat = discord.utils.get(guild.categories, name=name)
                if not cat:
                    cat = await guild.create_category(name)
                return cat

            async def get_or_create_text(name: str, cat: discord.CategoryChannel, overwrites=None):
                ch = discord.utils.get(cat.text_channels, name=name)
                if not ch:
                    ch = await guild.create_text_channel(name, category=cat, overwrites=overwrites)
                return ch

            async def get_or_create_voice(name: str, cat: discord.CategoryChannel, user_limit=0):
                ch = discord.utils.get(cat.voice_channels, name=name)
                if not ch:
                    ch = await guild.create_voice_channel(name, category=cat, user_limit=user_limit)
                return ch

            # INFO KATEGORIE
            cat_info = await get_or_create_cat("📌 WILLKOMMEN & INFO")
            chan_rules = await get_or_create_text("📜-regeln", cat_info, read_only_overwrites)
            chan_news = await get_or_create_text("📢-ankündigungen", cat_info, read_only_overwrites)
            chan_info = await get_or_create_text("ℹ️-server-info", cat_info, read_only_overwrites)
            chan_roles = await get_or_create_text("🎭-rollen-auswahl", cat_info, read_only_overwrites)

            # COMMUNITY KATEGORIE
            cat_comm = await get_or_create_cat("💬 COMMUNITY")
            await get_or_create_text("💬-allgemein", cat_comm)
            await get_or_create_text("⛏️-smp-talk", cat_comm)
            await get_or_create_text("📸-screenshots-clips", cat_comm)
            await get_or_create_text("🤖-bot-befehle", cat_comm)

            # HANDEL & PROJEKTE KATEGORIE
            cat_smp = await get_or_create_cat("🤝 HANDEL & PROJEKTE")
            await get_or_create_text("🛒-shops-und-handel", cat_smp)
            await get_or_create_text("🏗️-bauprojekte", cat_smp)
            await get_or_create_text("📍-koordinaten", cat_smp)
            await get_or_create_text("🗺️-dynmap-links", cat_smp)

            # VOICE KATEGORIE
            cat_voice = await get_or_create_cat("🔊 SPRACHKANÄLE")
            await get_or_create_voice("🔊 Talk 1 (Unbegrenzt)", cat_voice)
            await get_or_create_voice("🔊 Talk 2 (Duo)", cat_voice, user_limit=2)
            await get_or_create_voice("🔊 Talk 3 (Squad)", cat_voice, user_limit=4)
            await get_or_create_voice("⛏️ Mining & Farmen", cat_voice)
            await get_or_create_voice("⚔️ Bossfight / End", cat_voice)
            await get_or_create_voice("💤 AFK", cat_voice)

            # 4. Regelwerk Embed senden (falls Kanal leer)
            history = [msg async for msg in chan_rules.history(limit=5)]
            if len(history) == 0:
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

            # 5. Server-Info Embed senden (falls Kanal leer)
            history_info = [msg async for msg in chan_info.history(limit=5)]
            if len(history_info) == 0:
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

            # 6. Rollenauswahl Panel senden (falls Kanal leer)
            history_roles = [msg async for msg in chan_roles.history(limit=5)]
            if len(history_roles) == 0:
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
            confirm.add_field(name="Bereinigung alter Kanäle", value="✅ Vollständig durchgeführt" if clean_old else "ℹ️ Bestehende Kanäle beibehalten", inline=False)
            
            if isinstance(sender, discord.Interaction):
                await sender.followup.send(embed=confirm)
            else:
                await sender.send(embed=confirm)

        except Exception as e:
            logger.error(f"Fehler bei setup_smp: {e}", exc_info=True)
            msg = f"❌ Fehler beim Setup: `{e}`"
            if isinstance(sender, discord.Interaction):
                await sender.followup.send(msg)
            else:
                await sender.send(msg)

    @app_commands.command(name="setup-smp", description="Richtet diesen Discord-Server komplett für dein Minecraft SMP ein.")
    @app_commands.describe(
        server_name="Name deines SMP-Projekts (z. B. 'Jona & Friends SMP')",
        clean_old="Alte SMP-Kanäle vorher sauber löschen? (Standard: True)"
    )
    @app_commands.default_permissions(administrator=True)
    async def slash_setup_smp(self, interaction: discord.Interaction, server_name: str = "Minecraft SMP", clean_old: bool = True):
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern ausführbar.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Du benötigst Administrator-Rechte für diesen Befehl.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        await self.execute_smp_setup(interaction.guild, server_name, clean_old, interaction)

    @commands.command(name="setup-smp", aliases=["setupsmp", "smp-setup"])
    @commands.has_permissions(administrator=True)
    async def cmd_setup_smp(self, ctx: commands.Context, *, args: str = ""):
        """Prefix-Befehl: !setup-smp [Name]"""
        server_name = args.strip() if args.strip() else "Minecraft SMP"
        msg = await ctx.send("⏳ Richte den Minecraft SMP Server ein...")
        await self.execute_smp_setup(ctx.guild, server_name, clean_old=True, sender=ctx)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def cmd_sync(self, ctx: commands.Context):
        """Prefix-Befehl: !sync (Synchronisiert Slash-Commands sofort auf diesen Server)"""
        msg = await ctx.send("⏳ Synchronisiere Slash-Commands direkt mit diesem Server...")
        try:
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ **{len(synced)}** Slash-Commands sofort für diesen Server synchronisiert!")
        except Exception as e:
            await msg.edit(content=f"❌ Fehler bei der Synchronisation: `{e}`")

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
