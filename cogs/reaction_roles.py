import discord
from discord.ext import commands
from discord import app_commands
import json, os

# =====================================================
# ⚙️ CONFIG (EDIT THIS)
# =====================================================

FILE = "reaction_roles.json"

# 🔥 CHANGE THIS → your setup channel ID
ALLOWED_CHANNEL_ID = 1493012783942598819


# =====================================================
# 🐛 DEBUG FUNCTION
# =====================================================
def debug(msg):
   print(f"[RR DEBUG] {msg}")


# =====================================================
# 📂 JSON FUNCTIONS
# =====================================================
def load_data():
   if not os.path.exists(FILE):
       debug("JSON file not found, creating new")
       return {}

   with open(FILE, "r") as f:
       return json.load(f)


def save_data(data):
   with open(FILE, "w") as f:
       json.dump(data, f, indent=4)


# =====================================================
# 🎛 MAIN COG
# =====================================================
class ReactionRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   # ---------------- PERMISSION ----------------
   def is_admin(self, user):
       return user.guild_permissions.manage_messages

   # ---------------- CHANNEL CHECK ----------------
   def check_channel(self, interaction):
       if interaction.channel.id != ALLOWED_CHANNEL_ID:
           debug(f"Wrong channel used: {interaction.channel.id}")
           return False
       return True

   # =====================================================
   # 🎨 CREATE PANEL
   # =====================================================
   @app_commands.command(name="rr_create", description="Create reaction role panel")
   async def rr_create(self, interaction: discord.Interaction, title: str, description: str):

       debug(f"/rr_create used by {interaction.user}")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Use this in the setup channel", ephemeral=True)

       embed = discord.Embed(
           title=title,
           description=description,
           color=discord.Color.blue()
       )

       msg = await interaction.channel.send(embed=embed)

       data = load_data()
       data[str(msg.id)] = {}
       save_data(data)

       debug(f"Created panel with ID {msg.id}")

       await interaction.response.send_message(f"✅ Panel created\nID: {msg.id}", ephemeral=True)

   # =====================================================
   # ➕ ADD ROLE
   # =====================================================
   @app_commands.command(name="rr_add", description="Add emoji role")
   async def rr_add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):

       debug(f"/rr_add used by {interaction.user}")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Use this in setup channel", ephemeral=True)

       data = load_data()

       if message_id not in data:
           debug("Panel not found")
           return await interaction.response.send_message("❌ Panel not found", ephemeral=True)

       # Save mapping
       data[message_id][emoji] = role.id
       save_data(data)

       try:
           msg = await interaction.channel.fetch_message(int(message_id))
           await msg.add_reaction(emoji)

           # Update embed text
           embed = msg.embeds[0]
           desc = embed.description or ""
           desc += f"\n{emoji} = {role.mention}"
           embed.description = desc

           await msg.edit(embed=embed)

           debug(f"Added role {role.name} to emoji {emoji}")

       except Exception as e:
           debug(f"Failed to update message: {e}")
           return await interaction.response.send_message("❌ Failed to update message", ephemeral=True)

       await interaction.response.send_message("✅ Role added", ephemeral=True)

   # =====================================================
   # ➖ REMOVE ROLE
   # =====================================================
   @app_commands.command(name="rr_remove", description="Remove emoji role")
   async def rr_remove(self, interaction: discord.Interaction, message_id: str, emoji: str):

       debug(f"/rr_remove used by {interaction.user}")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Use this in setup channel", ephemeral=True)

       data = load_data()

       if message_id not in data or emoji not in data[message_id]:
           debug("Emoji mapping not found")
           return await interaction.response.send_message("❌ Not found", ephemeral=True)

       del data[message_id][emoji]
       save_data(data)

       debug(f"Removed emoji {emoji}")

       await interaction.response.send_message("✅ Removed", ephemeral=True)

   # =====================================================
   # 🔁 REACTION ADD
   # =====================================================
   @commands.Cog.listener()
   async def on_raw_reaction_add(self, payload):

       if payload.user_id == self.bot.user.id:
           return

       data = load_data()
       msg_id = str(payload.message_id)

       if msg_id not in data:
           return

       guild = self.bot.get_guild(payload.guild_id)
       member = guild.get_member(payload.user_id)

       emoji = str(payload.emoji)

       debug(f"Reaction added: {emoji} by {member}")

       if emoji in data[msg_id]:
           role = guild.get_role(data[msg_id][emoji])
           if role:
               await member.add_roles(role)
               debug(f"Gave role {role.name}")

   # =====================================================
   # 🔁 REACTION REMOVE
   # =====================================================
   @commands.Cog.listener()
   async def on_raw_reaction_remove(self, payload):

       data = load_data()
       msg_id = str(payload.message_id)

       if msg_id not in data:
           return

       guild = self.bot.get_guild(payload.guild_id)
       member = guild.get_member(payload.user_id)

       emoji = str(payload.emoji)

       debug(f"Reaction removed: {emoji} by {member}")

       if emoji in data[msg_id]:
           role = guild.get_role(data[msg_id][emoji])
           if role:
               await member.remove_roles(role)
               debug(f"Removed role {role.name}")


# =====================================================
# 🔧 SETUP
# =====================================================
async def setup(bot):
   await bot.add_cog(ReactionRoles(bot))