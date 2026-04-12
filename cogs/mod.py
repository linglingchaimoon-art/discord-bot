import discord
from discord.ext import commands
from discord import app_commands
import json
import os

LOG_CHANNEL_ID = 1442896372549550143

# -------------------------
# CASE SYSTEM
# -------------------------
def load_cases():
   if not os.path.exists("cases.json"):
       return {}
   with open("cases.json", "r") as f:
       return json.load(f)

def save_cases(data):
   with open("cases.json", "w") as f:
       json.dump(data, f, indent=4)

def create_case(guild_id, user_id, moderator_id, action, reason):
   data = load_cases()
   gid = str(guild_id)

   if gid not in data:
       data[gid] = {"count": 0, "cases": {}}

   data[gid]["count"] += 1
   case_id = data[gid]["count"]

   data[gid]["cases"][str(case_id)] = {
       "user": user_id,
       "moderator": moderator_id,
       "action": action,
       "reason": reason
   }

   save_cases(data)
   return case_id

# -------------------------
# LOG
# -------------------------
async def send_log(guild, embed):
   channel = guild.get_channel(LOG_CHANNEL_ID)
   if channel:
       await channel.send(embed=embed)

# -------------------------
# MODAL
# -------------------------
class ReasonModal(discord.ui.Modal, title="Enter Reason"):
   reason = discord.ui.TextInput(label="Reason", required=False)

   def __init__(self, action, member, cog):
       super().__init__()
       self.action = action
       self.member = member
       self.cog = cog

   async def on_submit(self, interaction: discord.Interaction):
       reason = self.reason.value or "No reason"

       case_id = create_case(
           interaction.guild.id,
           self.member.id,
           interaction.user.id,
           self.action,
           reason
       )

       try:
           if self.action == "Kick":
               await interaction.guild.kick(self.member, reason=reason)
               emoji = "👢"

           elif self.action == "Ban":
               await interaction.guild.ban(self.member, reason=reason)
               emoji = "🔨"

           elif self.action == "Mute":
               role = discord.utils.get(interaction.guild.roles, name="Muted")
               if role is None:
                   role = await interaction.guild.create_role(name="Muted")
                   for c in interaction.guild.channels:
                       await c.set_permissions(role, send_messages=False, speak=False)
               await self.member.add_roles(role)
               emoji = "🔇"

           elif self.action == "Unmute":
               role = discord.utils.get(interaction.guild.roles, name="Muted")
               if role and role in self.member.roles:
                   await self.member.remove_roles(role)
                   emoji = "🔊"
               else:
                   return await interaction.response.send_message("❌ Not muted", ephemeral=True)

           elif self.action == "Unban":
               await interaction.guild.unban(self.member)
               emoji = "🔓"

           await interaction.response.edit_message(
               content=f"{emoji} {self.action} {self.member}\nReason: {reason}",
               view=None
           )

           embed = discord.Embed(
               title=f"{self.action} | Case #{case_id}",
               color=discord.Color.red()
           )
           embed.add_field(name="User", value=str(self.member))
           embed.add_field(name="Moderator", value=interaction.user.mention)
           embed.add_field(name="Reason", value=reason)

           await send_log(interaction.guild, embed)

       except Exception as e:
           await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

# -------------------------
# DROPDOWN
# -------------------------
class ModSelect(discord.ui.Select):
   def __init__(self, view):
       self.view_ref = view
       super().__init__(placeholder="Select action...", options=[
           discord.SelectOption(label="Kick"),
           discord.SelectOption(label="Ban"),
           discord.SelectOption(label="Mute"),
           discord.SelectOption(label="Unmute"),
       ])

   async def callback(self, interaction: discord.Interaction):
       self.view_ref.action = self.values[0]
       await interaction.response.send_message(f"Selected: {self.values[0]}", ephemeral=True)

# -------------------------
# VIEW
# -------------------------
class ModView(discord.ui.View):
   def __init__(self, member, cog):
       super().__init__(timeout=60)
       self.member = member
       self.cog = cog
       self.action = None

       self.add_item(ModSelect(self))

   async def interaction_check(self, interaction: discord.Interaction):
       if not interaction.user.guild_permissions.administrator:
           await interaction.response.send_message("❌ Admin only", ephemeral=True)
           return False
       return True

   @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
   async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
       if not self.action:
           return await interaction.response.send_message("❌ Select action first", ephemeral=True)

       await interaction.response.send_modal(
           ReasonModal(self.action, self.member, self.cog)
       )

   @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
   async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
       await interaction.message.delete()

# -------------------------
# COG
# -------------------------
class Mod(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   def is_admin(self, user):
       return user.guild_permissions.administrator

   # 🎛 PANEL
   @commands.command()
   async def modpanel(self, ctx, member: discord.Member = None):
       if not self.is_admin(ctx.author):
           return await ctx.send("❌ Admin only")

       if not member:
           return await ctx.send("❌ Usage: !modpanel @user")

       embed = discord.Embed(
           title="🎛 Moderation Panel",
           description=f"Target: {member.mention}",
           color=discord.Color.blurple()
       )

       await ctx.send(embed=embed, view=ModView(member, self))

   # 🔓 UNBAN
   @app_commands.command(name="unban")
   async def unban(self, interaction: discord.Interaction, user_id: str):
       user_id = user_id.replace("<@", "").replace(">", "").replace("!", "")
       user = await self.bot.fetch_user(int(user_id))

       await interaction.response.send_modal(
           ReasonModal("Unban", user, self)
       )

   # 🔍 BANLIST
   @app_commands.command(name="banlist")
   async def banlist(self, interaction: discord.Interaction):
       bans = [b async for b in interaction.guild.bans()]
       desc = "\n".join([f"{b.user} ({b.user.id})" for b in bans[:10]]) or "No bans"

       await interaction.response.send_message(
           embed=discord.Embed(title="Ban List", description=desc),
           ephemeral=True
       )

   # 🔍 CASE
   @app_commands.command(name="case")
   async def case(self, interaction: discord.Interaction, case_id: int):
       data = load_cases()
       gid = str(interaction.guild.id)

       if gid not in data or str(case_id) not in data[gid]["cases"]:
           return await interaction.response.send_message("❌ Case not found", ephemeral=True)

       case = data[gid]["cases"][str(case_id)]

       embed = discord.Embed(title=f"Case #{case_id}")
       embed.add_field(name="User", value=f"<@{case['user']}>")
       embed.add_field(name="Moderator", value=f"<@{case['moderator']}>")
       embed.add_field(name="Action", value=case["action"])
       embed.add_field(name="Reason", value=case["reason"])

       await interaction.response.send_message(embed=embed, ephemeral=True)

   # 📜 CASES
   @app_commands.command(name="cases")
   async def cases(self, interaction: discord.Interaction, user: discord.Member):
       data = load_cases()
       gid = str(interaction.guild.id)

       if gid not in data:
           return await interaction.response.send_message("No cases", ephemeral=True)

       lines = []
       for cid, case in data[gid]["cases"].items():
           if case["user"] == user.id:
               lines.append(f"#{cid} → {case['action']}")

       if not lines:
           return await interaction.response.send_message("No cases for user", ephemeral=True)

       await interaction.response.send_message(
           embed=discord.Embed(title=f"Cases for {user}", description="\n".join(lines[:10])),
           ephemeral=True
       )

   # 👤 USER DASHBOARD
   @app_commands.command(name="user")
   async def user_dashboard(self, interaction: discord.Interaction, user: discord.Member):
       data = load_cases()
       gid = str(interaction.guild.id)

       embed = discord.Embed(title=f"{user}", color=discord.Color.blurple())
       embed.add_field(name="ID", value=user.id)
       embed.add_field(name="Joined", value=user.joined_at.strftime("%Y-%m-%d"))

       if gid in data:
           user_cases = [c for c in data[gid]["cases"].values() if c["user"] == user.id]
           embed.add_field(name="Cases", value=str(len(user_cases)))
       else:
           embed.add_field(name="Cases", value="0")

       await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------------
# SETUP
# -------------------------
async def setup(bot):
   await bot.add_cog(Mod(bot))