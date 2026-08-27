import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import logging
import asyncio
from cogs.unban_system import UnbanApplyView
from cogs.onboarding_system import PermanentWelcomeView

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
        """Core logic to build gated SMP server structure with onboarding verification."""
        try:
            # 1. Altes SMP Setup bereinigen falls gewünscht
            if clean_old:
                smp_categories = ["WILLKOMMEN", "COMMUNITY", "HANDEL", "PROJEKTE", "SPRACHKANÄLE", "INFO", "EINGANG"]
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
                {"name": "🚫 Gebannt", "color": discord.Color.dark_red(), "hoist": True},
            ]

            roles_map = {}
            for r in roles_data:
                role = discord.utils.get(guild.roles, name=r["name"])
                if not role:
                    try:
                        role = await guild.create_role(name=r["name"], color=r["color"], hoist=r["hoist"], mentionable=True)
                    except Exception as e:
                        logger.warning(f"Konnte Rolle {r['name']} nicht erstellen: {e}")
                roles_map[r["name"]] = role

            everyone_role = guild.default_role
            member_role = roles_map.get("⛏️ SMP Member")

            # Category permission overwrites
            # Public read-only for onboarding & info
            public_read_only = {
                everyone_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
            }

            # Locked category for verified members only
            members_only_overwrites = {
                everyone_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, manage_channels=True)
            }
            if member_role:
                members_only_overwrites[member_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, connect=True, speak=True)

            # 3. Kategorien & Kanäle erstellen
            async def get_or_create_cat(name: str, overwrites=None):
                cat = discord.utils.get(guild.categories, name=name)
                if not cat:
                    kwargs = {}
                    if overwrites and isinstance(overwrites, dict):
                        kwargs["overwrites"] = overwrites
                    cat = await guild.create_category(name, **kwargs)
                return cat

            async def get_or_create_text(name: str, cat: discord.CategoryChannel, overwrites=None):
                ch = discord.utils.get(cat.text_channels, name=name)
                if not ch:
                    kwargs = {"category": cat}
                    if overwrites and isinstance(overwrites, dict):
                        kwargs["overwrites"] = overwrites
                    ch = await guild.create_text_channel(name, **kwargs)
                return ch

            async def get_or_create_voice(name: str, cat: discord.CategoryChannel, user_limit=0):
                ch = discord.utils.get(cat.voice_channels, name=name)
                if not ch:
                    kwargs = {"category": cat}
                    if user_limit > 0:
                        kwargs["user_limit"] = user_limit
                    ch = await guild.create_voice_channel(name, **kwargs)
                return ch

            # 1. WILLKOMMEN & FREISCHALTUNG (Für alle sichtbar)
            cat_info = await get_or_create_cat("📌 WILLKOMMEN & FREISCHALTUNG", public_read_only)
            chan_welcome = await get_or_create_text("🚪-eingang-freischaltung", cat_info, public_read_only)
            chan_rules = await get_or_create_text("📜-regeln", cat_info, public_read_only)
            chan_info = await get_or_create_text("ℹ️-server-info", cat_info, public_read_only)
            chan_roles = await get_or_create_text("🎭-rollen-auswahl", cat_info, public_read_only)
            chan_unban = await get_or_create_text("📝-entbannungsantrag", cat_info, public_read_only)

            # 2. COMMUNITY (Gesperrt bis Freischaltung)
            cat_comm = await get_or_create_cat("💬 COMMUNITY", members_only_overwrites)
            await get_or_create_text("💬-allgemein", cat_comm)
            await get_or_create_text("⛏️-smp-talk", cat_comm)
            await get_or_create_text("📢-ankündigungen", cat_comm)
            await get_or_create_text("📸-screenshots-clips", cat_comm)
            await get_or_create_text("🤖-bot-befehle", cat_comm)

            # 3. HANDEL & PROJEKTE (Gesperrt bis Freischaltung)
            cat_smp = await get_or_create_cat("🤝 HANDEL & PROJEKTE", members_only_overwrites)
            await get_or_create_text("🛒-shops-und-handel", cat_smp)
            await get_or_create_text("🏗️-bauprojekte", cat_smp)
            await get_or_create_text("📍-koordinaten", cat_smp)

            # 4. SPRACHKANÄLE (Gesperrt bis Freischaltung)
            cat_voice = await get_or_create_cat("🔊 SPRACHKANÄLE", members_only_overwrites)
            await get_or_create_voice("🔊 Talk 1 (Unbegrenzt)", cat_voice)
            await get_or_create_voice("🔊 Talk 2 (Duo)", cat_voice, user_limit=2)
            await get_or_create_voice("🔊 Talk 3 (Squad)", cat_voice, user_limit=4)
            await get_or_create_voice("⛏️ Mining & Farmen", cat_voice)
            await get_or_create_voice("⚔️ Bossfight / End", cat_voice)
            await get_or_create_voice("💤 AFK", cat_voice)

            # 4. Willkommens- & Freischaltungsportal senden
            history_welcome = [msg async for msg in chan_welcome.history(limit=5)]
            if len(history_welcome) == 0:
                embed_welcome = discord.Embed(
                    title=f"🚪 Willkommen auf dem {server_name}!",
                    description=(
                        "Herzlich Willkommen auf unserem Minecraft SMP Discord Server!\n\n"
                        "🔒 **Server-Zugang gesperrt:**\n"
                        "Bevor du Zugriff auf alle Textkanäle, Sprachkanäle und Server-Features erhältst, "
                        "musst du kurz unsere 3-Schritte-Willkommenstour abschließen.\n\n"
                        "⏱️ **Dauert ca. 30 Sekunden:**\n"
                        "1️⃣ Server-Überblick & Konzept\n"
                        "2️⃣ Grundregeln & Fairplay\n"
                        "3️⃣ Verbindungsdaten & Bestätigung\n\n"
                        "Klicke auf den grünen Button unten, um deine Freischaltung zu starten! 👇"
                    ),
                    color=discord.Color.from_rgb(88, 101, 242),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_welcome.set_footer(text="Automatisches Onboarding-System • 24/7 aktiv")
                await chan_welcome.send(embed=embed_welcome, view=PermanentWelcomeView())

            # 5. Regelwerk Embed senden
            history_rules = [msg async for msg in chan_rules.history(limit=5)]
            if len(history_rules) == 0:
                embed_rules = discord.Embed(
                    title=f"📜 {server_name} – Offizielles Regelwerk",
                    description="Damit wir alle Spaß haben, befolge bitte die folgenden Grundregeln auf dem SMP und im Discord:",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_rules.add_field(name="1️⃣ Kein Griefing & Diebstahl", value="Fremde Bauwerke dürfen nicht beschädigt werden. Nichts ohne Erlaubnis aus Kisten entnehmen.", inline=False)
                embed_rules.add_field(name="2️⃣ Respekt & Fairplay", value="Toxizität, Beleidigungen und unangebrachtes Verhalten sind verboten.", inline=False)
                embed_rules.add_field(name="3️⃣ Keine Cheats / Unfaire Mods", value="X-Ray, Fly-Hacks, Autoclicker oder Duping führen zu einem sofortigen Bann.", inline=False)
                embed_rules.add_field(name="4️⃣ Basen-Abstand", value="Baue nicht direkt neben anderen Spielern ohne vorherige Absprache.", inline=False)
                embed_rules.add_field(name="5️⃣ Handel & Wirtschaft", value="Handel fair in Diamanten oder Tauschwaren im Kanal `#🛒-shops-und-handel`.", inline=False)
                embed_rules.set_footer(text=f"{server_name} • Fairplay ist Ehrensache!")
                await chan_rules.send(embed=embed_rules)

            # 6. Server-Info Embed senden
            history_info = [msg async for msg in chan_info.history(limit=5)]
            if len(history_info) == 0:
                embed_info = discord.Embed(
                    title=f"ℹ️ {server_name} – Verbindungsdaten (Weltweit erreichbar)",
                    description="Unser SMP-Server läuft mit **Fabric** und unterstützt dank **GeyserMC** sowohl Java- als auch Bedrock-Spieler von überall auf der Welt!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_info.add_field(name="☕ Java Edition (PC / Mac)", value="**Server-Adresse:** `olds-skimpily.tun.ply.gg`\n**Port:** Standard (`25565`)\n**Version:** `1.21.x Fabric`", inline=False)
                embed_info.add_field(name="📱 Bedrock Edition (Handy / Konsole / Tablet / Win)", value="**Server-IP / Name:** `olds-lieu.tun.ply.gg`\n**Port:** `58695` *(Wichtig!)*\n**Version:** `Aktuelle Bedrock`", inline=False)
                embed_info.add_field(name="🔓 Server-Zugang", value="Der Server ist öffentlich erreichbar. Bei Regelverstößen bannen Admins.", inline=False)
                embed_info.add_field(name="🏠 Lokales Netzwerk (LAN/WLAN)?", value="Im selben Heimnetzwerk kannst du auch direkt `192.168.178.128` (Java: `25565`, Bedrock: `19132`) nutzen.", inline=False)
                embed_info.add_field(name="🤖 Bot-Funktionen", value="Nutze `/mcstatus` für Live-Spieler, `/coords` für Wegpunkte & `/shop` für den Handel!", inline=False)
                embed_info.set_footer(text="Playit.gg Tunnel aktiv • 24/7 Dauerbetrieb")
                await chan_info.send(embed=embed_info)

            # 7. Rollenauswahl Panel senden
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

            # 8. Entbannungsantrag Panel senden
            history_unban = [msg async for msg in chan_unban.history(limit=5)]
            if len(history_unban) == 0:
                embed_unban = discord.Embed(
                    title="⚖️ Minecraft SMP – Entbannungsantrag",
                    description=(
                        "Du wurdest auf unserem Minecraft-Server oder Discord gebannt?\n\n"
                        "Klicke auf den Button unten, um eine Entschuldigung und einen Antrag auf Entbannung an das Server-Team einzureichen.\n\n"
                        "**Hinweis:** Begründe dein Verhalten sachlich und ehrlich. Admins prüfen deinen Antrag zeitnah."
                    ),
                    color=discord.Color.dark_red()
                )
                await chan_unban.send(embed=embed_unban, view=UnbanApplyView())

            # Bestätigung
            embed_success = discord.Embed(
                title="🎉 SMP Discord Server Setup Erfolgreich!",
                description=(
                    f"Der Server **{server_name}** wurde komplett eingerichtet!\n\n"
                    f"• **Onboarding-Schranke:** Neue Nutzer müssen erst die Tour in {chan_welcome.mention} absolvieren.\n"
                    f"• **Regelwerk & Details** in {chan_rules.mention} & {chan_info.mention}\n"
                    f"• **Interaktive Rollenauswahl** in {chan_roles.mention}\n"
                    f"• **Entbannungsanträge** in {chan_unban.mention}\n"
                    f"• Alle Hauptkanäle sind für freigeschaltete **⛏️ SMP Member** geöffnet!\n"
                ),
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed_success.set_footer(text="Dein Discord Minecraft Bot ist bereit!")

            if isinstance(sender, discord.Interaction):
                await sender.followup.send(embed=embed_success)
            else:
                await sender.send(embed=embed_success)

        except Exception as e:
            logger.error(f"Fehler beim Server-Setup: {e}", exc_info=True)
            err_msg = f"❌ Fehler beim Einrichten des Servers: `{e}`"
            if isinstance(sender, discord.Interaction):
                await sender.followup.send(err_msg)
            else:
                await sender.send(err_msg)

    @app_commands.command(name="setup-smp", description="Richtet automatisch den perfekten Minecraft SMP Discord Server mit Onboarding-Schranke ein.")
    @app_commands.describe(
        server_name="Name deines Minecraft SMPs (z.B. Mein SMP)",
        clean_old="Löscht alte SMP-Standardkanäle vor dem Setup für einen sauberen Neuaufbau (Standard: True)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_smp(self, interaction: discord.Interaction, server_name: str = "Minecraft SMP", clean_old: bool = True):
        if not interaction.guild:
            await interaction.response.send_message("❌ Dieser Befehl kann nur auf einem Discord Server ausgeführt werden.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        await self.execute_smp_setup(interaction.guild, server_name, clean_old, interaction)

    @commands.command(name="setup-smp")
    @commands.has_permissions(administrator=True)
    async def setup_smp_prefix(self, ctx: commands.Context, *, server_name: str = "Minecraft SMP"):
        """Prefix-Fallback für !setup-smp"""
        msg = await ctx.send("⏳ Richte den Minecraft SMP Server ein...")
        await self.execute_smp_setup(ctx.guild, server_name, True, ctx)

    @app_commands.command(name="setup-roles", description="Sendet das interaktive Panel zur Rollenauswahl in diesen Kanal.")
    @app_commands.default_permissions(administrator=True)
    async def setup_roles(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎭 Wähle deine SMP-Rollen & Benachrichtigungen",
            description="Klicke auf die Buttons unten, um dir Rollen zu geben oder zu entfernen:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔔 Ankündigungen", value="Werde benachrichtigt bei Events & Updates.", inline=False)
        embed.add_field(name="⛏️ / 🏗️ / ⚔️ / ⚡ Spezialisierungen", value="Zeige anderen Spielern deine Spezialisierung im SMP!", inline=False)
        await interaction.response.send_message(embed=embed, view=RoleSelectionView())

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerSetupCog(bot))
