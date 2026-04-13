import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI")

# 🔥 PANEL CHANNEL (CHANGE THIS)
PANEL_CHANNEL_ID = 1493012783942598819


# ================= ROLE VIEW =================
class RoleView(discord.ui.View):
   def __init__(self, role_names):
       super().__init__(timeout=None)
       self.role_names = role_names

   async def handle_role(self, interaction, role_name):
       role = discord.utils.get(interaction.guild.roles, name=role_name)

       if not role:
           return await interaction.response.send_message(
               f"❌ Role '{role_name}' not found",
               ephemeral=True,
               delete_after=3
           )

       if role in interaction.user.roles:
           await interaction.user.remove_roles(role)
           await interaction.response.send_message(
               f"❌ Removed **{role.name}**",
               ephemeral=True,
               delete_after=3
           )
       else:
           await interaction.user.add_roles(role)
           await interaction.response.send_message(
               f"✅ Added **{role.name}**",
               ephemeral=True,
               delete_after=3
           )

   # ================= BUTTONS =================

   @discord.ui.button(label="Phasmophobia", emoji="👻", style=discord.ButtonStyle.primary)
   async def phasmo(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.role_names["👻"])

   @discord.ui.button(label="PUBG", emoji="🔫", style=discord.ButtonStyle.success)
   async def pubg(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.role_names["🔫"])

   @discord.ui.button(label="Rocket League", emoji="🚗", style=discord.ButtonStyle.danger)
   async def rl(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.role_names["🚗"])

   @discord.ui.button(label="Minecraft", emoji="⛏️", style=discord.ButtonStyle.secondary)
   async def mc(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.role_names["⛏️"])


# ================= COG =================
class ButtonRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["button_roles"]

   # ================= CREATE PANEL =================
   @app_commands.command(name="panel", description="Create clean role panel")
   async def panel(self, interaction: discord.Interaction):

       await interaction.response.defer(ephemeral=True)

       channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

       if not channel:
           return await interaction.followup.send("❌ Panel channel not found")

       embed = discord.Embed(
           title="🎮 Gaming Roles",
           description=(
               "Choose your games below:\n\n"
               "👻 Phasmophobia\n"
               "🔫 PUBG\n"
               "🚗 Rocket League\n"
               "⛏️ Minecraft\n\n"
               "━━━━━━━━━━━━━━━━━━━━━━\n"
               "✨ Click to get role\n"
               "❌ Click again to remove"
           ),
           color=0x5865F2
       )

       # 🧠 AUTO ROLE NAMES (NO IDS)
       roles = {
           "👻": "Phasmophobia",
           "🔫": "PUBG",
           "🚗": "Rocket League",
           "⛏️": "Minecraft"
       }

       view = RoleView(roles)

       msg = await channel.send(embed=embed, view=view)

       await self.collection.insert_one({
           "message_id": msg.id,
           "roles": roles
       })

       await interaction.followup.send("✅ Panel created", ephemeral=True, delete_after=3)

   # ================= PERSIST =================
   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ Button UI Loaded")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


# ================= SETUP =================
async def setup(bot):
   await bot.add_cog(ButtonRoles(bot))