import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI")


# ================= BUTTON =================
class RoleButton(discord.ui.Button):
   def __init__(self, role_name):
       super().__init__(label=role_name, style=discord.ButtonStyle.primary)
       self.role_name = role_name

   async def callback(self, interaction: discord.Interaction):
       print(f"[DEBUG] Button clicked: {self.role_name}")

       role = discord.utils.get(interaction.guild.roles, name=self.role_name)

       if not role:
           return await interaction.response.send_message(
               f"❌ Role '{self.role_name}' not found",
               ephemeral=True,
               delete_after=3
           )

       if role in interaction.user.roles:
           await interaction.user.remove_roles(role)
           await interaction.response.send_message(
               f"❌ Removed {role.name}",
               ephemeral=True,
               delete_after=3
           )
       else:
           await interaction.user.add_roles(role)
           await interaction.response.send_message(
               f"✅ Added {role.name}",
               ephemeral=True,
               delete_after=3
           )


# ================= VIEW =================
class RoleView(discord.ui.View):
   def __init__(self, roles):
       super().__init__(timeout=None)
       for role in roles:
           self.add_item(RoleButton(role))


# ================= CHANNEL SELECT =================
class ChannelSelect(discord.ui.ChannelSelect):
   def __init__(self, data):
       super().__init__(
           placeholder="Select a channel to send panel",
           min_values=1,
           max_values=1,
           channel_types=[discord.ChannelType.text]
       )
       self.data = data

   async def callback(self, interaction: discord.Interaction):
       print("[DEBUG] Channel selected")

       # 🔥 FIX: RESPOND IMMEDIATELY
       await interaction.response.defer(ephemeral=True)

       try:
           channel = self.values[0]
           print(f"[DEBUG] Channel: {channel.name}")

           embed = discord.Embed(
               title=self.data["title"],
               description=self.data["description"] +
                           "\n\n━━━━━━━━━━━━━━━━━━\n✨ Click to get role\n❌ Click again to remove",
               color=0x5865F2
           )

           view = RoleView(self.data["roles"])

           msg = await channel.send(embed=embed, view=view)

           cog = interaction.client.get_cog("PanelGUI")

           await cog.collection.insert_one({
               "guild_id": interaction.guild.id,
               "channel_id": channel.id,
               "message_id": msg.id,
               "roles": self.data["roles"]
           })

           await interaction.followup.send(
               f"✅ Panel sent to #{channel.name}",
               delete_after=3
           )

       except Exception as e:
           print("[ERROR] ChannelSelect:", e)

           await interaction.followup.send(
               f"❌ Error: {e}",
               delete_after=5
           )


class ChannelSelectView(discord.ui.View):
   def __init__(self, data):
       super().__init__(timeout=60)
       self.add_item(ChannelSelect(data))


# ================= MODAL =================
class PanelModal(discord.ui.Modal, title="Create Panel"):

   title_input = discord.ui.TextInput(
       label="Title",
       placeholder="Example: 🎮 Gaming Roles",
       required=True
   )

   description_input = discord.ui.TextInput(
       label="Description",
       style=discord.TextStyle.paragraph,
       placeholder="Example:\nChoose your favorite games!",
       required=True
   )

   roles_input = discord.ui.TextInput(
       label="Roles (comma separated)",
       placeholder="Example: Minecraft, Valorant, Staff",
       required=True
   )

   async def on_submit(self, interaction: discord.Interaction):
       print("[DEBUG] Modal submitted")

       roles = [r.strip() for r in self.roles_input.value.split(",")]

       data = {
           "title": self.title_input.value,
           "description": self.description_input.value,
           "roles": roles
       }

       await interaction.response.send_message(
           "📍 Select a channel:",
           view=ChannelSelectView(data),
           ephemeral=True
       )


# ================= COG =================
class PanelGUI(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       print("[DEBUG] Connecting to Mongo...")
       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["panels"]

   @app_commands.command(name="createpanel", description="Create panel with GUI")
   async def createpanel(self, interaction: discord.Interaction):
       print("[DEBUG] /createpanel used")
       await interaction.response.send_modal(PanelModal())

   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ GUI SYSTEM READY")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelGUI(bot))