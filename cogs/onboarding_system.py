import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timezone

logger = logging.getLogger("OnboardingSystem")

def get_onboarding_embed(step: int, guild_name: str) -> discord.Embed:
    if step == 1:
        embed = discord.Embed(
            title=f"👋 Willkommen auf dem {guild_name} SMP!",
            description=(
                f"Schön, dass du da bist! Bevor du den Discord-Server betreten und mitspielen kannst, "
                f"gehe bitte kurz durch diesen **3-Schritte-Willkommens-Guide**.\n\n"
                f"🎮 **Über unser Projekt:**\n"
                f"• Echter **Minecraft Fabric SMP** mit Fokus auf Bauen, Erkunden & Wirtschaft\n"
                f"• **Crossplay:** Sowohl Java (PC/Mac) als auch Bedrock (Handy, Konsole, Tablet, Win) werden unterstützt!\n"
                f"• 24/7 dauerhaft online ohne Unterbrechungen\n\n"
                f"Klicke auf den Button unten, um zu den Regeln zu gelangen 👇"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Schritt 1 von 3 • {guild_name}")
        return embed

    elif step == 2:
        embed = discord.Embed(
            title="📜 Schritt 2: Die wichtigsten Grundregeln",
            description=(
                "Für ein faires und harmonisches Miteinander gelten folgende Kernregeln:\n\n"
                "**1️⃣ Kein Griefing & Diebstahl:**\n"
                "• Zerstöre keine fremden Bauwerke und nimm nichts ungefragt aus Kisten.\n\n"
                "**2️⃣ Keine unfairen Cheats / Mods:**\n"
                "• X-Ray, Fly-Hacks, Autoclicker oder Duping führen zum sofortigen Bann.\n\n"
                "**3️⃣ Respekt & Fairplay:**\n"
                "• Freundlicher Umgangston im Chat und Voice. Beleidigungen sind verboten.\n\n"
                "**4️⃣ Freier Handel:**\n"
                "• Faire Tauschgeschäfte & Diamanten-Wirtschaft im Markt-Kanal.\n\n"
                "Klicke auf **Weiter**, um die Verbindungsdaten zu sehen 👇"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Schritt 2 von 3 • {guild_name}")
        return embed

    elif step == 3:
        embed = discord.Embed(
            title="🎮 Schritt 3: Verbindungsdaten & Freischaltung",
            description=(
                "Hier sind die Serverdaten zum Beitreten:\n\n"
                "☕ **Java Edition (PC / Mac):**\n"
                "• **Adresse:** `olds-skimpily.tun.ply.gg`\n\n"
                "📱 **Bedrock Edition (Handy / Konsole / Tablet):**\n"
                "• **Server-IP:** `olds-lieu.tun.ply.gg`\n"
                "• **Port:** `58695` *(Wichtig: Port eintragen!)*\n\n"
                "✅ **Bereit?**\n"
                "Klicke auf den grünen Button **'Regeln akzeptieren & Freischalten ✅'**, um alle Kanäle freizuschalten!"
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Schritt 3 von 3 • Bereit zum Spielen!")
        return embed


class OnboardingStep1View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Weiter zu den Regeln ➡️", style=discord.ButtonStyle.primary, emoji="📜")
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = get_onboarding_embed(2, interaction.guild.name)
        await interaction.response.edit_message(embed=embed, view=OnboardingStep2View())


class OnboardingStep2View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
    async def prev_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = get_onboarding_embed(1, interaction.guild.name)
        await interaction.response.edit_message(embed=embed, view=OnboardingStep1View())

    @discord.ui.button(label="Weiter zur Server-Info ➡️", style=discord.ButtonStyle.primary, emoji="🎮")
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = get_onboarding_embed(3, interaction.guild.name)
        await interaction.response.edit_message(embed=embed, view=OnboardingStep3View())


class OnboardingStep3View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="⬅️ Zurück", style=discord.ButtonStyle.secondary)
    async def prev_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = get_onboarding_embed(2, interaction.guild.name)
        await interaction.response.edit_message(embed=embed, view=OnboardingStep2View())

    @discord.ui.button(label="Regeln akzeptieren & Freischalten ✅", style=discord.ButtonStyle.success, emoji="🎉")
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="⛏️ SMP Member")
        if not role:
            role = await guild.create_role(name="⛏️ SMP Member", color=discord.Color.green(), hoist=True)

        if role in interaction.user.roles:
            await interaction.response.send_message("Du bist bereits als SMP Member freigeschaltet! Viel Spaß!", ephemeral=True)
            return

        try:
            await interaction.user.add_roles(role)
            
            embed_success = discord.Embed(
                title="🎉 Erfolgreich freigeschaltet!",
                description="Du hast nun vollen Zugriff auf alle Kanäle des Discord-Servers!\n\nSchau gerne in `#💬-allgemein` oder `#ℹ️-server-info` vorbei!",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed_success, view=None)

            # Welcome message in general chat
            general = None
            for ch in guild.text_channels:
                if "allgemein" in ch.name or "general" in ch.name or "smp-talk" in ch.name:
                    general = ch
                    break
            if general:
                embed_welcome = discord.Embed(
                    title="🎉 Neues Mitglied freigeschaltet!",
                    description=f"Herzlich Willkommen {interaction.user.mention} auf dem **{guild.name}**!\nViel Spaß beim gemeinsamen Bauen und Zocken! ⛏️💎",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed_welcome.set_thumbnail(url=interaction.user.display_avatar.url)
                await general.send(embed=embed_welcome)

        except Exception as e:
            logger.error(f"Fehler bei Freischaltung: {e}")
            await interaction.response.send_message("❌ Fehler beim Zuweisen der Rolle. Bitte wende dich an einen Admin.", ephemeral=True)


class PermanentWelcomeView(discord.ui.View):
    """Static persistent button placed in #willkommen-verifikation that opens the interactive guide."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Server betreten & Freischaltung starten 🚀", style=discord.ButtonStyle.success, custom_id="btn_start_onboarding", emoji="🚪")
    async def start_onboarding(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="⛏️ SMP Member")
        if role and role in interaction.user.roles:
            await interaction.response.send_message("Du bist bereits freigeschaltet und hast vollen Zugriff auf alle Kanäle! ⛏️", ephemeral=True)
            return

        # Send step 1 as a clean private ephemeral message to the user
        embed = get_onboarding_embed(1, interaction.guild.name)
        view = OnboardingStep1View()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class OnboardingSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup-welcome-portal", description="Sendet das interaktive Willkommens- & Freischaltungs-Portal in diesen Kanal.")
    @app_commands.default_permissions(administrator=True)
    async def setup_portal(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🚪 Willkommen auf dem {interaction.guild.name}!",
            description=(
                "Um Zugriff auf alle Textkanäle, Sprachkanäle und den Minecraft-Server zu erhalten, "
                "klicke unten auf den Button und schließe die kurze Willkommens-Tour ab!\n\n"
                "⏱️ **Dauert nur 30 Sekunden.**"
            ),
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.set_footer(text="Klicke auf den grünen Button, um zu starten 👇")
        await interaction.response.send_message(embed=embed, view=PermanentWelcomeView())


async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingSystemCog(bot))
