import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI")
ALLOWED_CHANNEL_ID = 1442896372260016276  # CHANGE THIS


# ================= BUTTON VIEW =================
class RoleView(discord.ui.View):
   def __init__(self, roles):
       super().__init__(timeout=None)
       self.roles = roles

   async def handle_role(self, interaction: discord.Interaction, role_id):
       role = interaction.guild.get_role(role_id)

       if not role:
           return await interaction.response.send_message("❌ Role not found", ephemeral=True)

       if role in interaction.user.roles:
           await interaction.user.remove_roles(role)
           await interaction.response.send_message(f"❌ Removed {role.name}", ephemeral=True)
       else:
           await interaction.user.add_roles(role)
           await interaction.response.send_message(f"✅ Added {role.name}", ephemeral=True)

   # ================= BUTTONS =================

   @discord.ui.button(label="Phasmophobia", emoji="👻", style=discord.ButtonStyle.primary)
   async def phasmo(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.roles["👻"])

   @discord.ui.button(label="PUBG", emoji="🔫", style=discord.ButtonStyle.success)
   async def pubg(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.roles["🔫"])

   @discord.ui.button(label="Rocket League", emoji="🚗", style=discord.ButtonStyle.danger)
   async def rl(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.roles["🚗"])

   @discord.ui.button(label="Minecraft", emoji="⛏️", style=discord.ButtonStyle.secondary)
   async def mc(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.handle_role(interaction, self.roles["⛏️"])


# ================= COG =================
class ButtonRoles(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["button_roles"]

   # ================= CREATE PANEL =================
   @app_commands.command(name="panel", description="Create button role panel")
   async def panel(self, interaction: discord.Interaction):

       await interaction.response.defer()

       if interaction.channel.id != ALLOWED_CHANNEL_ID:
           return await interaction.followup.send("❌ Wrong channel", ephemeral=True)

       embed = discord.Embed(
           title="🎮 HEAVEN GAMING ROLES",
           description=(
               "━━━━━━━━━━━━━━━━━━━━━━\n\n"
               "👻 Phasmophobia\n"
               "🔫 PUBG\n"
               "🚗 Rocket League\n"
               "⛏️ Minecraft\n\n"
               "━━━━━━━━━━━━━━━━━━━━━━\n"
               "✨ Click buttons to get roles\n"
               "❌ Click again to remove"
           ),
           color=0x5865F2
       )

       # 🔥 YOU MUST EDIT THESE ROLE IDS
       roles = {
           "👻": 111111111111111111,
           "🔫": 222222222222222222,
           "🚗": 333333333333333333,
           "⛏️": 444444444444444444
       }

       view = RoleView(roles)

       msg = await interaction.followup.send(embed=embed, view=view)

       # SAVE FOR PERSIST
       await self.collection.insert_one({
           "message_id": msg.id,
           "roles": roles
       })

   # ================= PERSIST BUTTONS =================
   @commands.Cog.listener()
   async def on_ready(self):
       print("Button system ready")

       # Reload all panels
       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(ButtonRoles(bot))