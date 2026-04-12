import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

ALLOWED_CHANNEL_ID = 1442896372260016276
MONGO_URI = os.getenv("MONGO_URI")


class ReactionRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["reaction_roles"]

   # ================= CREATE =================
   @app_commands.command(name="rr_create", description="Create panel")
   async def rr_create(self, interaction: discord.Interaction):

       await interaction.response.defer()  # ✅ ALWAYS FIRST

       try:
           embed = discord.Embed(
               title="🎮 HEAVEN GAMING ROLES",
               description=(
                   "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                   "👻 Phasmophobia\n"
                   "🔫 PUBG\n"
                   "🚗 Rocket League\n"
                   "⛏️ Minecraft\n\n"
                   "━━━━━━━━━━━━━━━━━━━━━━\n"
                   "✨ React to get roles\n"
                   "❌ Remove reaction to remove"
               ),
               color=0x5865F2
           )

           msg = await interaction.followup.send(embed=embed)

           await self.collection.insert_one({
               "channel_id": str(interaction.channel.id),
               "message_id": str(msg.id),
               "roles": {}
           })

       except Exception as e:
           print("CREATE ERROR:", e)
           await interaction.followup.send(f"❌ {e}")

   # ================= ADD =================
   @app_commands.command(name="rr_add", description="Add role")
   async def rr_add(self, interaction: discord.Interaction, emoji: str, role: discord.Role):

       await interaction.response.defer(ephemeral=True)

       try:
           data = await self.collection.find_one(
               {"channel_id": str(interaction.channel.id)},
               sort=[("_id", -1)]
           )

           if not data:
               return await interaction.followup.send("❌ Create panel first")

           roles = data.get("roles", {})
           roles[emoji] = role.id

           await self.collection.update_one(
               {"_id": data["_id"]},
               {"$set": {"roles": roles}}
           )

           msg = await interaction.channel.fetch_message(int(data["message_id"]))
           await msg.add_reaction(emoji)

           await interaction.followup.send("✅ Added")

       except Exception as e:
           print("ADD ERROR:", e)
           await interaction.followup.send(f"❌ {e}")

   # ================= REACTION ADD =================
   @commands.Cog.listener()
   async def on_raw_reaction_add(self, payload):

       try:
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

       except Exception as e:
           print("REACTION ERROR:", e)


async def setup(bot):
   await bot.add_cog(ReactionRoles(bot))