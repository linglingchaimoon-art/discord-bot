import discord
from discord.ext import commands
from discord import app_commands

LOG_CHANNEL_ID = 1442896372549550143  # 🔥 your log channel id


class Mod(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   def is_admin(self, user):
       return user.guild_permissions.manage_messages

   async def send_log(self, guild, embed):
       channel = guild.get_channel(LOG_CHANNEL_ID)
       if channel:
           await channel.send(embed=embed)
       else:
           print("[MOD DEBUG] Log channel not found")

   # ---------------- BAN ----------------
   @app_commands.command(name="ban", description="Ban a user")
   async def ban(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       await interaction.response.defer(ephemeral=True)  # ✅ FIX

       await interaction.guild.ban(member)

       embed = discord.Embed(title="🔨 User Banned", color=discord.Color.red())
       embed.add_field(name="User", value=member.mention)
       embed.add_field(name="Moderator", value=interaction.user.mention)

       await self.send_log(interaction.guild, embed)

       await interaction.followup.send(f"🔨 Banned {member}", ephemeral=True)

   # ---------------- KICK ----------------
   @app_commands.command(name="kick", description="Kick a user")
   async def kick(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       await interaction.guild.kick(member)

       embed = discord.Embed(title="👢 User Kicked", color=discord.Color.orange())
       embed.add_field(name="User", value=member.mention)
       embed.add_field(name="Moderator", value=interaction.user.mention)

       await self.send_log(interaction.guild, embed)

       await interaction.followup.send(f"👢 Kicked {member}", ephemeral=True)

   # ---------------- MUTE ----------------
   @app_commands.command(name="mute", description="Mute a user")
   async def mute(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       role = discord.utils.get(interaction.guild.roles, name="Muted")

       if role is None:
           role = await interaction.guild.create_role(name="Muted")
           for channel in interaction.guild.channels:
               await channel.set_permissions(role, send_messages=False, speak=False)

       await member.add_roles(role)

       embed = discord.Embed(title="🔇 User Muted", color=discord.Color.dark_gray())
       embed.add_field(name="User", value=member.mention)
       embed.add_field(name="Moderator", value=interaction.user.mention)

       await self.send_log(interaction.guild, embed)

       await interaction.followup.send(f"🔇 Muted {member}", ephemeral=True)

   # ---------------- PURGE ----------------
   @app_commands.command(name="purge", description="Delete messages")
   async def purge(self, interaction: discord.Interaction, amount: int):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       await interaction.channel.purge(limit=amount)

       embed = discord.Embed(title="🧹 Messages Deleted", color=discord.Color.blue())
       embed.add_field(name="Amount", value=str(amount))
       embed.add_field(name="Moderator", value=interaction.user.mention)

       await self.send_log(interaction.guild, embed)

       await interaction.followup.send(f"🧹 Deleted {amount} messages", ephemeral=True)


async def setup(bot):
   await bot.add_cog(Mod(bot))