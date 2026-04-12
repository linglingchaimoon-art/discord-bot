
import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime

LOG_CHANNEL_ID = 1442896372549550143  # 🔥 CHANGE THIS


# ---------------- CASE SYSTEM ----------------
def load_cases():
    if not os.path.exists("cases.json"):
        return {}
    with open("cases.json", "r") as f:
        return json.load(f)

def save_cases(data):
    with open("cases.json", "w") as f:
        json.dump(data, f, indent=4)

def create_case(gid, uid, mid, action, reason):
    data = load_cases()

    if str(gid) not in data:
        data[str(gid)] = {"count": 0, "cases": {}}

    data[str(gid)]["count"] += 1
    cid = data[str(gid)]["count"]

    data[str(gid)]["cases"][str(cid)] = {
        "user": uid,
        "mod": mid,
        "action": action,
        "reason": reason,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_cases(data)
    return cid


# ---------------- MODAL ----------------
class ReasonModal(discord.ui.Modal, title="Enter Reason"):
    reason = discord.ui.TextInput(label="Reason", required=False)

    def __init__(self, cog, action, member):
        super().__init__()
        self.cog = cog
        self.action = action
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        reason = self.reason.value or "No reason"

        if self.action == "ban":
            await interaction.guild.ban(self.member)
            emoji = "🔨"

        elif self.action == "kick":
            await interaction.guild.kick(self.member)
            emoji = "👢"

        elif self.action == "mute":
            role = discord.utils.get(interaction.guild.roles, name="Muted")
            if not role:
                role = await interaction.guild.create_role(name="Muted")
                for c in interaction.guild.channels:
                    await c.set_permissions(role, send_messages=False, speak=False)
            await self.member.add_roles(role)
            emoji = "🔇"

        # 📜 CASE
        cid = create_case(
            interaction.guild.id,
            self.member.id,
            interaction.user.id,
            self.action,
            reason
        )

        # 📜 LOG
        embed = discord.Embed(
            title=f"{emoji} {self.action.upper()} | Case #{cid}",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=self.member.mention)
        embed.add_field(name="Moderator", value=interaction.user.mention)
        embed.add_field(name="Reason", value=reason)

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(embed=embed)

        await interaction.followup.send(
            f"{emoji} {self.action} done (Case #{cid})",
            ephemeral=True
        )


# ---------------- PANEL ----------------
class ModPanel(discord.ui.View):
    def __init__(self, cog, member):
        super().__init__(timeout=120)
        self.cog = cog
        self.member = member

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(ReasonModal(self.cog, "ban", self.member))

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.blurple)
    async def kick(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(ReasonModal(self.cog, "kick", self.member))

    @discord.ui.button(label="Mute", style=discord.ButtonStyle.gray)
    async def mute(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(ReasonModal(self.cog, "mute", self.member))

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button):
        await interaction.message.delete()


# ---------------- COG ----------------
class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, user):
        return user.guild_permissions.manage_messages

    # 🎛 PANEL
    @app_commands.command(name="modpanel", description="Open moderation panel")
    async def modpanel(self, interaction: discord.Interaction, member: discord.Member):
        if not self.is_admin(interaction.user):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        await interaction.response.send_message(
            f"🎛 Moderation panel for {member}",
            view=ModPanel(self, member),
            ephemeral=True
        )

    # 🔥 SLASH COMMANDS

    @app_commands.command(name="ban", description="Ban user")
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(ReasonModal(self, "ban", member))

    @app_commands.command(name="kick", description="Kick user")
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(ReasonModal(self, "kick", member))

    @app_commands.command(name="mute", description="Mute user")
    async def mute(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(ReasonModal(self, "mute", member))

    @app_commands.command(name="purge", description="Delete messages")
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not self.is_admin(interaction.user):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        await interaction.channel.purge(limit=amount)

        embed = discord.Embed(
            title="🧹 Messages Deleted",
            color=discord.Color.blue()
        )
        embed.add_field(name="Amount", value=str(amount))
        embed.add_field(name="Moderator", value=interaction.user.mention)

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(embed=embed)

        await interaction.followup.send(f"🧹 Deleted {amount} messages", ephemeral=True)


# ---------------- SETUP ----------------
async def setup(bot):
    await bot.add_cog(Mod(bot))