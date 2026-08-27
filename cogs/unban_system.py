import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timezone
import database

logger = logging.getLogger("UnbanSystem")

class UnbanModal(discord.ui.Modal, title="Minecraft SMP Entbannungsantrag"):
    mc_name = discord.ui.TextInput(
        label="Dein Minecraft Ingame-Name",
        placeholder="z.B. MinecraftGamer123",
        required=True,
        max_length=32
    )
    reason = discord.ui.TextInput(
        label="Warum wurdest du gebannt? (Grund)",
        placeholder="z.B. Griefing, X-Ray, Missverständnis...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )
    explanation = discord.ui.TextInput(
        label="Warum sollten wir dich entbannen?",
        placeholder="Erkläre die Situation und warum du wieder mitspielen möchtest...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_channel_id = await database.get_guild_setting(guild.id, "whitelist_channel_id")
        
        target_channel = guild.get_channel(staff_channel_id) if staff_channel_id else None
        if not target_channel:
            for ch in guild.text_channels:
                if "bot" in ch.name or "admin" in ch.name or "allgemein" in ch.name:
                    target_channel = ch
                    break

        embed = discord.Embed(
            title="⚖️ Neuer Entbannungsantrag eingereicht!",
            description=f"Antrag von {interaction.user.mention} (`{interaction.user.name}`)",
            color=discord.Color.orange(),
            timestamp=interaction.created_at
        )
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/face/64/{self.mc_name.value}.png")
        embed.add_field(name="Minecraft Ingame-Name", value=f"`{self.mc_name.value}`", inline=True)
        embed.add_field(name="Ban-Grund", value=f"`{self.reason.value}`", inline=True)
        embed.add_field(name="Stellungnahme / Entschuldigung", value=self.explanation.value, inline=False)
        embed.set_footer(text="Admins können diesen Antrag mit den Buttons bearbeiten.")

        view = UnbanDecisionView(interaction.user.id, self.mc_name.value)

        if target_channel:
            await target_channel.send(embed=embed, view=view)
            await interaction.response.send_message("✅ Dein Entbannungsantrag wurde erfolgreich an die Server-Admins übermittelt!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Es konnte kein Admin-Kanal gefunden werden. Bitte wende dich direkt an einen Admin.", ephemeral=True)


class UnbanDecisionView(discord.ui.View):
    def __init__(self, applicant_id: int, mc_name: str):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.mc_name = mc_name

    @discord.ui.button(label="Entbannen ✅", style=discord.ButtonStyle.success, custom_id="unban_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Nur Administratoren können Entbannungsanträge bearbeiten.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.applicant_id)

        # 1. Unban in Minecraft via RCON
        rcon_msg = "Unbekannt"
        try:
            from cogs.rcon_manager import run_rcon_cmd
            resp = run_rcon_cmd(f"pardon {self.mc_name}")
            rcon_msg = resp
        except Exception as e:
            rcon_msg = str(e)

        # 2. Remove Ban role on Discord if exists
        banned_role = discord.utils.get(guild.roles, name="🚫 Gebannt")
        member_role = discord.utils.get(guild.roles, name="⛏️ SMP Member")
        if member:
            try:
                if banned_role and banned_role in member.roles:
                    await member.remove_roles(banned_role)
                if member_role and member_role not in member.roles:
                    await member.add_roles(member_role)
            except Exception:
                pass

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Entbannungsantrag ANGENOMMEN"
        embed.set_footer(text=f"Entbannt von {interaction.user.display_name} • Ingame: /pardon {self.mc_name}")

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"🎉 **{self.mc_name}** wurde entbannt! (`{rcon_msg}`)", ephemeral=False)

        if member:
            try:
                await member.send(f"🎉 Dein Entbannungsantrag für **{self.mc_name}** auf dem SMP **{guild.name}** wurde angenommen! Du kannst dem Server nun wieder beitreten.\n\n🌐 **Adresse:** `olds-skimpily.tun.ply.gg`")
            except Exception:
                pass

    @discord.ui.button(label="Ablehnen ❌", style=discord.ButtonStyle.danger, custom_id="unban_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Nur Administratoren können Entbannungsanträge bearbeiten.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.applicant_id)

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Entbannungsantrag ABGELEHNT"
        embed.set_footer(text=f"Abgelehnt von {interaction.user.display_name}")

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"Antrag für **{self.mc_name}** abgelehnt.", ephemeral=True)

        if member:
            try:
                await member.send(f"❌ Dein Entbannungsantrag für **{self.mc_name}** auf dem SMP **{guild.name}** wurde leider abgelehnt.")
            except Exception:
                pass


class UnbanApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entbannungsantrag stellen 📝", style=discord.ButtonStyle.danger, custom_id="btn_apply_unban", emoji="⚖️")
    async def apply_unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UnbanModal())


class UnbanSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mc-ban", description="Bannt einen Spieler von Minecraft und Discord (Nur Admins).")
    @app_commands.describe(
        player_name="Minecraft Ingame-Name",
        reason="Grund für den Bann",
        discord_user="Zugehöriger Discord-Nutzer (optional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def mc_ban(self, interaction: discord.Interaction, player_name: str, reason: str = "Regelverstoß", discord_user: discord.Member = None):
        await interaction.response.defer(thinking=True)

        # 1. Ban in Minecraft via RCON
        from cogs.rcon_manager import run_rcon_cmd
        rcon_resp = run_rcon_cmd(f"ban {player_name} {reason}")

        # 2. Assign Ban role in Discord if user passed
        if discord_user:
            banned_role = discord.utils.get(interaction.guild.roles, name="🚫 Gebannt")
            if not banned_role:
                banned_role = await interaction.guild.create_role(name="🚫 Gebannt", color=discord.Color.dark_red())
            
            member_role = discord.utils.get(interaction.guild.roles, name="⛏️ SMP Member")
            try:
                if member_role and member_role in discord_user.roles:
                    await discord_user.remove_roles(member_role)
                await discord_user.add_roles(banned_role)
            except Exception:
                pass

        embed = discord.Embed(
            title="🔨 Spieler gebannt",
            description=f"Spieler: **`{player_name}`**\nGrund: `{reason}`\n\nRückmeldung: `{rcon_resp}`",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Gebannt von {interaction.user.display_name} • Entbannung via /mc-unban oder Antrag")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="mc-unban", description="Entbannt einen Spieler auf dem Minecraft-Server (Nur Admins).")
    @app_commands.describe(player_name="Minecraft Ingame-Name")
    @app_commands.default_permissions(administrator=True)
    async def mc_unban(self, interaction: discord.Interaction, player_name: str):
        from cogs.rcon_manager import run_rcon_cmd
        resp = run_rcon_cmd(f"pardon {player_name}")
        embed = discord.Embed(
            title="✅ Spieler entbannt",
            description=f"Spieler **`{player_name}`** wurde entbannt.\nRückmeldung: `{resp}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setup-unban-button", description="Sendet das Entbannungsantrag-Panel in den aktuellen Kanal.")
    @app_commands.default_permissions(administrator=True)
    async def setup_unban(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚖️ Minecraft SMP – Entbannungsantrag",
            description=(
                "Du wurdest auf unserem Minecraft-Server oder Discord gebannt?\n\n"
                "Klicke auf den Button unten, um eine Entschuldigung und einen Antrag auf Entbannung an das Server-Team einzureichen.\n\n"
                "**Hinweis:** Begründe dein Verhalten sachlich und ehrlich."
            ),
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, view=UnbanApplyView())


async def setup(bot: commands.Bot):
    await bot.add_cog(UnbanSystemCog(bot))
