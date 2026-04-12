import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

# =====================================================
# ⚙️ CONFIG (EDIT THIS)
# =====================================================
ALLOWED_CHANNEL_ID = 1493012783942598819  # 🔥 CHANGE THIS
MONGO_URI = os.getenv("MONGO_URI")


# =====================================================
# 🎛 MAIN SYSTEM
# =====================================================
class ReactionRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       # 🔥 DATABASE
       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["reaction_roles"]

   def is_admin(self, user):
       return user.guild_permissions.manage_messages

   def check_channel(self, interaction):
       return interaction.channel.id == ALLOWED_CHANNEL_ID

   # =====================================================
   # 🎨 CREATE PANEL
   # =====================================================
   @app_commands.command(name="rr_create", description="Create role panel")
   async def rr_create(self, interaction: discord.Interaction):

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       if not self.check_channel(interaction):
           return await interaction.response.send_message("❌ Wrong channel", ephemeral=True)

       description = (
           "━━━━━━━━━━━━━━━━━━━━━━\n\n"
           "👻 **Phasmophobia**\n"
           "🔫 **PUBG**\n"
           "🚗 **Rocket League**\n"
           "⛏️ **Minecraft**\n\n"
           "━━━━━━━━━━━━━━━━━━━━━━\n"
           "✨ React to get roles\n"
           "❌ Remove reaction to remove"
       )

       embed = discord.Embed(
           title="🎮 HEAVEN GAMING ROLES",
           description=description,
           color=0x5865F2
       )

       embed.set_footer(text="Powered by HeavenBot")

       # ✅ SEND PANEL
       await interaction.response.send_message(embed=embed)

       msg = await interaction.original_response()

       # ✅ SAVE PANEL
       await self.collection.insert_one({
           "message_id": str(msg.id),
           "roles": {}
       })

       # ✅ SEND ID
       await interaction.followup.send(
           f"✅ Panel created\n📌 ID: `{msg.id}`",
           ephemeral=True
       )

   # =====================================================
   # ➕ ADD ROLE
   # =====================================================
   @app_commands.command(name="rr_add", description="Add emoji role")
   async def rr_add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       data = await self.collection.find_one({"message_id": message_id})

       # 🔥 AUTO FIX
       if not data:
           await self.collection.insert_one({
               "message_id": message_id,
               "roles": {}
           })
           data = {"roles": {}}

       roles = data["roles"]
       roles[emoji] = role.id

       await self.collection.update_one(
           {"message_id": message_id},
           {"$set": {"roles": roles}}
       )

       try:
           msg = await interaction.channel.fetch_message(int(message_id))
           await msg.add_reaction(emoji)
       except Exception as e:
           return await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

       await interaction.response.send_message("✅ Role added", ephemeral=True)

   # =====================================================
   # ➖ REMOVE ROLE
   # =====================================================
   @app_commands.command(name="rr_remove", description="Remove emoji role")
   async def rr_remove(self, interaction: discord.Interaction, message_id: str, emoji: str):

       if not self.is_admin(interaction.user):
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       data = await self.collection.find_one({"message_id": message_id})

       if not data:
           return await interaction.response.send_message("❌ Panel not found", ephemeral=True)

       roles = data["roles"]

       if emoji in roles:
           del roles[emoji]

       await self.collection.update_one(
           {"message_id": message_id},
           {"$set": {"roles": roles}}
       )

       await interaction.response.send_message("✅ Removed", ephemeral=True)

   # =====================================================
   # 🔁 REACTION ADD
   # =====================================================
   @commands.Cog.listener()
   async def on_raw_reaction_add(self, payload):

       if payload.user_id == self.bot.user.id:
           return

       data = await self.collection.find_one({"message_id": str(payload.message_id)})

       if not data:
           return

       guild = self.bot.get_guild(payload.guild_id)
       member = guild.get_member(payload.user_id)

       emoji = str(payload.emoji)

       if emoji in data["roles"]:
           role = guild.get_role(data["roles"][emoji])
           if role:
               await member.add_roles(role)

   # =====================================================
   # 🔁 REACTION REMOVE
   # =====================================================
   @commands.Cog.listener()
   async def on_raw_reaction_remove(self, payload):

       data = await self.collection.find_one({"message_id": str(payload.message_id)})

       if not data:
           return

       guild = self.bot.get_guild(payload.guild_id)
       member = guild.get_member(payload.user_id)

       emoji = str(payload.emoji)

       if emoji in data["roles"]:
           role = guild.get_role(data["roles"][emoji])
           if role:
               await member.remove_roles(role)


# =====================================================
# 🔧 SETUP
# =====================================================
async def setup(bot):
   await bot.add_cog(ReactionRoles(bot))