import discord
from discord.ext import commands
from discord import app_commands
import json, os

# =====================================================
# ⚙️ CONFIG (EDIT THIS)
# =====================================================

FILE = "reaction_roles.json"

# 🔥 PUT YOUR CHANNEL ID HERE
ALLOWED_CHANNEL_ID = 1493012783942598819


# =====================================================
# 🐛 DEBUG
# =====================================================
def debug(msg):
   print(f"[RR DEBUG] {msg}")


# =====================================================
# 📂 JSON
# =====================================================
def load_data():
   if not os.path.exists(FILE):
       return {}
   with open(FILE, "r") as f:
       return json.load(f)

def save_data(data):
   with open(FILE, "w") as f:
       json.dump(data, f, indent=4)


# =====================================================
# 🎛 MAIN SYSTEM
# =====================================================
class ReactionRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   def is_admin(self, user):
       return user.guild_permissions.manage_messages

   def check_channel(self, interaction):
       return interaction.channel.id == ALLOWED_CHANNEL_ID

   # =====================================================
   # 🎨 CREATE PANEL (FIXED DOUBLE MESSAGE)
   # =====================================================
   @app_commands.command(name="rr_create", description="Create premium role panel")
   async def rr_create(self, interaction: discord.Interaction, title: str, description: str):

       debug(f"rr_create by {interaction.user}")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Wrong channel", ephemeral=True)

       # 🎨 PREMIUM EMBED
       embed = discord.Embed(
           title=f"🎮 {title.upper()}",
           description=f"━━━━━━━━━━━━━━━━━━━━━━\n{description}\n━━━━━━━━━━━━━━━━━━━━━━",
           color=0x2b2d31
       )

       embed.set_footer(text="✨ React to get roles • Remove to remove")

       # ✅ FIX: NO DOUBLE MESSAGE
       await interaction.response.send_message(embed=embed)
       msg = await interaction.original_response()

       # Save panel
       data = load_data()
       data[str(msg.id)] = {}
       save_data(data)

       debug(f"Panel created: {msg.id}")

       await interaction.followup.send(
           f"✅ Panel created\n📌 ID: `{msg.id}`",
           ephemeral=True
       )

   # =====================================================
   # ➕ ADD ROLE
   # =====================================================
   @app_commands.command(name="rr_add", description="Add emoji role")
   async def rr_add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):

       debug(f"rr_add used")

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Wrong channel", ephemeral=True)

       data = load_data()

       if message_id not in data:
           debug("Panel not found error")
           return await interaction.response.send_message("❌ Panel not found", ephemeral=True)

       data[message_id][emoji] = role.id
       save_data(data)

       try:
           msg = await interaction.channel.fetch_message(int(message_id))
           await msg.add_reaction(emoji)

           embed = msg.embeds[0]
           desc = embed.description

           desc += f"\n{emoji} **{role.name}**"

           embed.description = desc

           await msg.edit(embed=embed)

           debug(f"Added {emoji} -> {role.name}")

       except Exception as e:
           debug(f"Error: {e}")
           return await interaction.response.send_message("❌ Failed to update message", ephemeral=True)

       await interaction.response.send_message("✅ Role added", ephemeral=True)

   # =====================================================
   # ➖ REMOVE ROLE
   # =====================================================
   @app_commands.command(name="rr_remove", description="Remove emoji role")
   async def rr_remove(self, interaction: discord.Interaction, message_id: str, emoji: str):

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       data = load_data()

       if message_id not in data or emoji not in data[message_id]:
           return await interaction.response.send_message("❌ Not found", ephemeral=True)

       del data[message_id][emoji]
       save_data(data)

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

       if emoji in data[msg_id]:
           role = guild.get_role(data[msg_id][emoji])
           if role:
               await member.add_roles(role)
               debug(f"Added role {role.name}")

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