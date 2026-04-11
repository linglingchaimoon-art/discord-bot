import discord
from discord.ext import commands
from discord import app_commands


class Mod(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   # -------------------------
   # ADMIN CHECK
   # -------------------------
   def is_admin(self, user):
       return user.guild_permissions.administrator

   # =====================================================
   # 🔥 SLASH COMMANDS (HIDDEN)
   # =====================================================

   @app_commands.command(name="ping")
   async def slash_ping(self, interaction: discord.Interaction):
       await interaction.response.defer(ephemeral=True)
       await interaction.followup.send(f"🏓 {round(self.bot.latency * 1000)}ms", ephemeral=True)

   @app_commands.command(name="mute")
   async def slash_mute(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       role = discord.utils.get(interaction.guild.roles, name="Muted")

       if role is None:
           role = await interaction.guild.create_role(name="Muted")
           for channel in interaction.guild.channels:
               await channel.set_permissions(role, send_messages=False, speak=False)

       await member.add_roles(role)
       await interaction.followup.send(f"🔇 {member.mention} muted", ephemeral=True)

   @app_commands.command(name="unmute")
   async def slash_unmute(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       role = discord.utils.get(interaction.guild.roles, name="Muted")

       if role and role in member.roles:
           await member.remove_roles(role)
           await interaction.followup.send(f"🔊 {member.mention} unmuted", ephemeral=True)
       else:
           await interaction.followup.send("❌ User is not muted", ephemeral=True)

   @app_commands.command(name="ban")
   async def slash_ban(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       await interaction.guild.ban(member)
       await interaction.followup.send(f"🔨 {member} banned", ephemeral=True)

   @app_commands.command(name="kick")
   async def slash_kick(self, interaction: discord.Interaction, member: discord.Member):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       await interaction.guild.kick(member)
       await interaction.followup.send(f"👢 {member} kicked", ephemeral=True)

   @app_commands.command(name="purge")
   async def slash_purge(self, interaction: discord.Interaction, amount: int):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       await interaction.channel.purge(limit=amount)
       await interaction.followup.send(f"🧹 Deleted {amount} messages", ephemeral=True)

   @app_commands.command(name="unban")
   async def slash_unban(self, interaction: discord.Interaction, user_id: str):
       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       await interaction.response.defer(ephemeral=True)

       user = await self.bot.fetch_user(int(user_id))
       await interaction.guild.unban(user)
       await interaction.followup.send(f"🔓 {user} unbanned", ephemeral=True)

   # =====================================================
   # 💬 PREFIX COMMANDS (!)
   # =====================================================

   @commands.command()
   async def ping(self, ctx):
       await ctx.send(f"🏓 {round(self.bot.latency * 1000)}ms")

   @commands.command()
   async def mute(self, ctx, member: discord.Member = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if member is None:
           return await ctx.send("❌ Usage: !mute @user")

       role = discord.utils.get(ctx.guild.roles, name="Muted")

       if role is None:
           role = await ctx.guild.create_role(name="Muted")
           for channel in ctx.guild.channels:
               await channel.set_permissions(role, send_messages=False, speak=False)

       await member.add_roles(role)
       await ctx.send(f"🔇 {member.mention} muted")

   @commands.command()
   async def unmute(self, ctx, member: discord.Member = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if member is None:
           return await ctx.send("❌ Usage: !unmute @user")

       role = discord.utils.get(ctx.guild.roles, name="Muted")

       if role is None:
           return await ctx.send("❌ Muted role not found")

       if role not in member.roles:
           return await ctx.send("❌ User is not muted")

       await member.remove_roles(role)
       await ctx.send(f"🔊 {member.mention} unmuted")

   @commands.command()
   async def ban(self, ctx, member: discord.Member = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if member is None:
           return await ctx.send("❌ Usage: !ban @user")

       await ctx.guild.ban(member)
       await ctx.send(f"🔨 {member} banned")

   @commands.command()
   async def kick(self, ctx, member: discord.Member = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if member is None:
           return await ctx.send("❌ Usage: !kick @user")

       await ctx.guild.kick(member)
       await ctx.send(f"👢 {member} kicked")

   @commands.command()
   async def purge(self, ctx, amount: int = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if amount is None:
           return await ctx.send("❌ Usage: !purge <amount>")

       await ctx.channel.purge(limit=amount)
       await ctx.send(f"🧹 Deleted {amount} messages")
       await asyncio.sleep(5)
       await msg.delete()

   @commands.command()
   async def unban(self, ctx, user_id: int = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if user_id is None:
           return await ctx.send("❌ Usage: !unban <id>")

       user = await self.bot.fetch_user(user_id)
       await ctx.guild.unban(user)
       await ctx.send(f"🔓 {user} unbanned")


# -------------------------
# SETUP
# -------------------------
async def setup(bot):
   await bot.add_cog(Mod(bot))