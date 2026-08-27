import discord
from discord import app_commands
from discord.ext import commands
import logging
import database

logger = logging.getLogger("WhitelistSystem")

class WhitelistModal(discord.ui.Modal, title="Minecraft SMP Whitelist Antrag"):
    mc_name = discord.ui.TextInput(
        label="Minecraft Ingame-Name (Java)",
        placeholder="z.B. MinecraftGamer123",
        required=True,
        max_length=32
    )
    experience = discord.ui.TextInput(
        label="Was baust/machst du am liebsten in Minecraft?",
        placeholder="z.B. Große Städte, Redstone-Farmen, Erkunden...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_channel_id = await database.get_guild_setting(guild.id, "whitelist_channel_id")
        
        # Look for a channel named `#mod-log` or `#admin-chat` or `#allgemein` if not explicitly set
        target_channel = guild.get_channel(staff_channel_id) if staff_channel_id else None
        if not target_channel:
            for ch in guild.text_channels:
                if "bot" in ch.name or "admin" in ch.name or "allgemein" in ch.name:
                    target_channel = ch
                    break

        embed = discord.Embed(
            title="📋 Neuer Whitelist-Antrag eingegangen!",
            color=discord.Color.blue(),
            timestamp=interaction.created_at
        )
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/face/64/{self.mc_name.value}.png")
        embed.add_field(name="Discord User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Minecraft Name", value=f"`{self.mc_name.value}`", inline=True)
        if self.experience.value:
            embed.add_field(name="Interessen / Spielstil", value=self.experience.value, inline=False)
        embed.set_footer(text="Admins können diesen Antrag mit den Buttons unten bearbeiten.")

        view = WhitelistDecisionView(interaction.user.id, self.mc_name.value)

        if target_channel:
            await target_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Dein Antrag für **{self.mc_name.value}** wurde an das Server-Team übermittelt!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Kein Kanal für Anträge gefunden. Bitte kontaktiere einen Admin direkt.", ephemeral=True)


class WhitelistDecisionView(discord.ui.View):
    def __init__(self, applicant_id: int, mc_name: str):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.mc_name = mc_name

    @discord.ui.button(label="Annehmen ✅", style=discord.ButtonStyle.success, custom_id="wl_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Nur Administratoren können Anträge annehmen.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.applicant_id)

        # 1. Add player to Minecraft Ingame Whitelist via RCON
        try:
            from cogs.rcon_manager import run_rcon_cmd
            run_rcon_cmd("whitelist on")
            rcon_resp = run_rcon_cmd(f"whitelist add {self.mc_name}")
            rcon_info = f" (Ingame: `{rcon_resp}`)"
        except Exception as e:
            rcon_info = f" (RCON: `{e}`)"

        # 2. Assign SMP Member role if exists
        role = discord.utils.get(guild.roles, name="⛏️ SMP Member")
        if member and role:
            try:
                await member.add_roles(role)
            except Exception:
                pass

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Whitelist-Antrag ANGENOMMEN"
        embed.set_footer(text=f"Angenommen von {interaction.user.display_name} • Ingame Whitelist: /whitelist add {self.mc_name}")

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"🎉 **{self.mc_name}** wurde angenommen und automatisch zur Server-Whitelist hinzugefügt!{rcon_info}", ephemeral=False)

        if member:
            try:
                await member.send(f"🎉 Dein Whitelist-Antrag für **{self.mc_name}** auf dem SMP **{guild.name}** wurde angenommen! Du bist nun auf der Whitelist freigeschaltet. Viel Spaß beim Spielen!\n\n🌐 **IP:** `192.168.178.128`")
            except Exception:
                pass

    @discord.ui.button(label="Ablehnen ❌", style=discord.ButtonStyle.danger, custom_id="wl_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Nur Administratoren können Anträge ablehnen.", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Whitelist-Antrag ABGELEHNT"
        embed.set_footer(text=f"Abgelehnt von {interaction.user.display_name}")

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"Antrag für **{self.mc_name}** abgelehnt.", ephemeral=True)


class WhitelistApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Whitelist beantragen 📋", style=discord.ButtonStyle.primary, custom_id="btn_apply_whitelist", emoji="⛏️")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal())


class WhitelistSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup-whitelist-button", description="Sendet den interaktiven Button zum Beantragen der Whitelist in diesen Kanal.")
    @app_commands.default_permissions(administrator=True)
    async def setup_whitelist(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        await database.set_guild_setting(interaction.guild.id, "whitelist_channel_id", interaction.channel.id)

        embed = discord.Embed(
            title="🔒 Minecraft SMP – Whitelist Freischaltung",
            description="Möchtest du auf unserem Server mitspielen? Klicke auf den Button unten, um deinen Minecraft-Namen einzutragen!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Voraussetzung", value="Ein gültiger Minecraft Java Edition Account.", inline=False)
        embed.set_footer(text="Deine Anfrage wird direkt an die Admins weitergeleitet.")

        await interaction.response.send_message(embed=embed, view=WhitelistApplyView())

async def setup(bot: commands.Bot):
    await bot.add_cog(WhitelistSystemCog(bot))
