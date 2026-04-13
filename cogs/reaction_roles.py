import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI")
PANEL_CHANNEL_ID = 1442896372549550142  # CHANGE THIS


# ================= VIEW =================
class DynamicRoleView(discord.ui.View):
   def __init__(self, roles):
       super().__init__(timeout=None)

       for role_data in roles:
           self.add_item(RoleButton(role_data))


class RoleButton(discord.ui.Button):
   def __init__(self, data):
       super().__init__(
           label=data["label"],
           emoji=data["emoji"],
           style=discord.ButtonStyle.primary
       )
       self.role_name = data["role"]

   async def callback(self, interaction: discord.Interaction):
       role = discord.utils.get(interaction.guild.roles, name=self.role_name)

       if not role:
           return await interaction.response.send_message("❌ Role not found", ephemeral=True, delete_after=3)

       if role in interaction.user.roles:
           await interaction.user.remove_roles(role)
           await interaction.response.send_message(f"❌ Removed {role.name}", ephemeral=True, delete_after=3)
       else:
           await interaction.user.add_roles(role)
           await interaction.response.send_message(f"✅ Added {role.name}", ephemeral=True, delete_after=3)


# ================= COG =================
class PanelEditor(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.panels = self.db["panels"]

   # ================= CREATE =================
   @app_commands.command(name="panel_create", description="Create panel")
   async def panel_create(self, interaction: discord.Interaction, title: str, description: str):

       await interaction.response.defer(ephemeral=True)

       panel = {
           "guild_id": interaction.guild.id,
           "title": title,
           "description": description,
           "roles": []
       }

       result = await self.panels.insert_one(panel)

       await interaction.followup.send(f"✅ Panel created\nID: `{result.inserted_id}`")

   # ================= ADD ROLE =================
   @app_commands.command(name="panel_add", description="Add role to panel")
   async def panel_add(
       self,
       interaction: discord.Interaction,
       panel_id: str,
       role: discord.Role,
       label: str,
       emoji: str
   ):

       await interaction.response.defer(ephemeral=True)

       panel = await self.panels.find_one({"_id": panel_id})

       if not panel:
           return await interaction.followup.send("❌ Panel not found")

       panel["roles"].append({
           "role": role.name,
           "label": label,
           "emoji": emoji
       })

       await self.panels.update_one(
           {"_id": panel_id},
           {"$set": {"roles": panel["roles"]}}
       )

       await interaction.followup.send("✅ Role added")

   # ================= SEND =================
   @app_commands.command(name="panel_send", description="Send panel")
   async def panel_send(self, interaction: discord.Interaction, panel_id: str):

       await interaction.response.defer(ephemeral=True)

       panel = await self.panels.find_one({"_id": panel_id})

       if not panel:
           return await interaction.followup.send("❌ Panel not found")

       embed = discord.Embed(
           title=panel["title"],
           description=panel["description"],
           color=0x5865F2
       )

       view = DynamicRoleView(panel["roles"])

       channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

       await channel.send(embed=embed, view=view)

       await interaction.followup.send("✅ Panel sent")

   # ================= PERSIST =================
   @commands.Cog.listener()
   async def on_ready(self):
       print("Panel editor ready")

       async for panel in self.panels.find():
           self.bot.add_view(DynamicRoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelEditor(bot))