import discord
from discord.ext import commands
from discord import app_commands
import json, os
from datetime import datetime

LOG_CHANNEL_ID = 1442896372549550143  # 🔥 CHANGE THIS

# 🧠 AUTO PUNISH SETTINGS
WARN_LIMITS = {
   2: "mute",
   3: "kick",
   4: "ban"
}

# ---------------- DEBUG ----------------
def debug(msg):
   print(f"[MOD DEBUG] {msg}")

# ---------------- JSON ----------------
def load_json(file):
   if not os.path.exists(file):
       debug(f"{file} not found, creating new")
       return {}
   with open(file, "r") as f:
       return json.load(f)

def save_json(file, data):
   with open(file, "w") as f:
       json.dump(data, f, indent=4)

# ---------------- CASE ----------------
def create_case(gid, uid, mid, action, reason):
   debug(f"Creating case: {action} for {uid}")

   data = load_json("cases.json")

   if str(gid) not in data:
       data[str(gid)] = {"count": 0, "cases": {}}

   data[str(gid)]["count"] += 1
   cid = data[str(gid)]["count"]

   data[str(gid)]["cases"][str(cid)] = {
       "user": uid,
       "mod": mid,
       "action": action,
       "reason": reason,
       "time": str(datetime.utcnow())
   }

   save_json("cases.json", data)
   return cid

# ---------------- WARN ----------------
def add_warn(gid, uid, reason):
   debug(f"Adding warn to {uid}: {reason}")

   data = load_json("warnings.json")

   if str(gid) not in data:
       data[str(gid)] = {}

   if str(uid) not in data[str(gid)]:
       data[str(gid)][str(uid)] = []

   data[str(gid)][str(uid)].append(reason)
   save_json("warnings.json", data)

def get_warns(gid, uid):
   data = load_json("warnings.json")
   return data.get(str(gid), {}).get(str(uid), [])

# ---------------- PANEL ----------------
class ModPanel(discord.ui.View):
   def __init__(self, cog, member):
       super().__init__(timeout=60)
       self.cog = cog
       self.member = member

   @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger)
   async def ban(self, interaction: discord.Interaction, button):
       debug(f"Ban button clicked by {interaction.user}")
       await interaction.response.send_modal(ReasonModal(self.cog, "ban", self.member))

   @discord.ui.button(label="Kick", style=discord.ButtonStyle.blurple)
   async def kick(self, interaction: discord.Interaction, button):
       debug(f"Kick button clicked by {interaction.user}")
       await interaction.response.send_modal(ReasonModal(self.cog, "kick", self.member))

   @discord.ui.button(label="Mute", style=discord.ButtonStyle.gray)
   async def mute(self, interaction: discord.Interaction, button):
       debug(f"Mute button clicked by {interaction.user}")
       await interaction.response.send_modal(ReasonModal(self.cog, "mute", self.member))

   @discord.ui.button(label="Warn", style=discord.ButtonStyle.green)
   async def warn(self, interaction: discord.Interaction, button):
       debug(f"Warn button clicked by {interaction.user}")
       await interaction.response.send_modal(ReasonModal(self.cog, "warn", self.member))

# ---------------- MODAL ----------------
class ReasonModal(discord.ui.Modal, title="Reason"):
   reason = discord.ui.TextInput(label="Reason", required=False)

   def __init__(self, cog, action, member):
       super().__init__()
       self.cog = cog
       self.action = action
       self.member = member

   async def on_submit(self, interaction: discord.Interaction):
       reason = self.reason.value or "No reason"
       debug(f"Modal submit: {self.action} → {self.member} | {reason}")

       # ⚠️ WARN
       if self.action == "warn":
           add_warn(interaction.guild.id, self.member.id, reason)
           warns = len(get_warns(interaction.guild.id, self.member.id))

           debug(f"User now has {warns} warnings")

           await interaction.response.send_message(f"⚠️ Warn #{warns}", ephemeral=True)

           # 🧠 AUTO PUNISH
           if warns in WARN_LIMITS:
               action = WARN_LIMITS[warns]
               debug(f"Auto punish triggered: {action}")

               try:
                   if action == "mute":
                       role = discord.utils.get(interaction.guild.roles, name="Muted")
                       if not role:
                           role = await interaction.guild.create_role(name="Muted")
                       await self.member.add_roles(role)

                   elif action == "kick":
                       await interaction.guild.kick(self.member)

                   elif action == "ban":
                       await interaction.guild.ban(self.member)

                   await interaction.followup.send(f"⚡ Auto {action} triggered!", ephemeral=True)

               except Exception as e:
                   debug(f"Auto punish failed: {e}")

           return

       # 🔨 ACTIONS
       try:
           if self.action == "ban":
               await interaction.guild.ban(self.member)

           elif self.action == "kick":
               await interaction.guild.kick(self.member)

           elif self.action == "mute":
               role = discord.utils.get(interaction.guild.roles, name="Muted")
               if not role:
                   role = await interaction.guild.create_role(name="Muted")
               await self.member.add_roles(role)

       except Exception as e:
           debug(f"Action failed: {e}")
           return await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

       # 📜 CASE
       cid = create_case(
           interaction.guild.id,
           self.member.id,
           interaction.user.id,
           self.action,
           reason
       )

       # 🔔 DM
       try:
           await self.member.send(f"You were {self.action} in {interaction.guild.name}\nReason: {reason}")
       except Exception as e:
           debug(f"DM failed: {e}")

       # 📜 LOG
       try:
           embed = discord.Embed(title=f"{self.action.upper()} | Case #{cid}", color=discord.Color.red())
           embed.add_field(name="User", value=self.member)
           embed.add_field(name="Mod", value=interaction.user)
           embed.add_field(name="Reason", value=reason)

           log = interaction.guild.get_channel(LOG_CHANNEL_ID)
           if log:
               await log.send(embed=embed)
           else:
               debug("Log channel not found")

       except Exception as e:
           debug(f"Logging failed: {e}")

       await interaction.response.send_message(f"✅ {self.action} done (Case #{cid})", ephemeral=True)

# ---------------- COG ----------------
class Mod(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   def is_admin(self, user):
       return user.guild_permissions.manage_messages

   @app_commands.command(name="modpanel")
   async def panel(self, interaction: discord.Interaction, member: discord.Member):
       debug(f"Modpanel opened by {interaction.user} for {member}")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       await interaction.response.send_message(
           f"🎛 Panel for {member}",
           view=ModPanel(self, member),
           ephemeral=True
       )

# ---------------- SETUP ----------------
async def setup(bot):
   await bot.add_cog(Mod(bot))