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
       role = discord.utils.get(interaction.guild.roles, name=self.role_name)

       if not role:
           return await interaction.response.send_message("❌ Role not found", ephemeral=True, delete_after=3)

       if role in interaction.user.roles:
           await interaction.user.remove_roles(role)
           await interaction.response.send_message(f"❌ Removed {role.name}", ephemeral=True, delete_after=3)
       else:
           await interaction.user.add_roles(role)
           await interaction.response.send_message(f"✅ Added {role.name}", ephemeral=True, delete_after=3)


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
           placeholder="Select channel",
           min_values=1,
           max_values=1,
           channel_types=[discord.ChannelType.text]
       )
       self.data = data

   async def callback(self, interaction: discord.Interaction):
       channel = self.values[0]

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

       await interaction.response.send_message("✅ Panel created", ephemeral=True, delete_after=3)


class ChannelSelectView(discord.ui.View):
   def __init__(self, data):
       super().__init__(timeout=60)
       self.add_item(ChannelSelect(data))


# ================= CREATE MODAL =================
class PanelModal(discord.ui.Modal, title="Create Panel"):
   title_input = discord.ui.TextInput(label="Title", required=True)
   description_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)
   roles_input = discord.ui.TextInput(label="Roles (comma separated)", required=True)

   async def on_submit(self, interaction: discord.Interaction):
       roles = [r.strip() for r in self.roles_input.value.split(",")]

       data = {
           "title": self.title_input.value,
           "description": self.description_input.value,
           "roles": roles
       }

       await interaction.response.send_message(
           "📍 Select channel:",
           view=ChannelSelectView(data),
           ephemeral=True
       )


# ================= EDIT =================
class EditPanelModal(discord.ui.Modal, title="Edit Panel"):
   roles_input = discord.ui.TextInput(label="New roles (comma separated)", required=True)

   def __init__(self, panel_id):
       super().__init__()
       self.panel_id = panel_id

   async def on_submit(self, interaction: discord.Interaction):
       roles = [r.strip() for r in self.roles_input.value.split(",")]

       cog = interaction.client.get_cog("PanelGUI")
       panel = await cog.collection.find_one({"_id": ObjectId(self.panel_id)})

       await cog.collection.update_one(
           {"_id": ObjectId(self.panel_id)},
           {"$set": {"roles": roles}}
       )

       # 🔥 LIVE UPDATE
       channel = interaction.guild.get_channel(panel["channel_id"])
       message = await channel.fetch_message(panel["message_id"])

       embed = message.embeds[0]

       await message.edit(embed=embed, view=RoleView(roles))

       await interaction.response.send_message("✅ Panel updated", ephemeral=True, delete_after=3)


class EditPanelSelect(discord.ui.Select):
   def __init__(self, panels):
       options = [
           discord.SelectOption(label=str(p["_id"]), description="Edit panel")
           for p in panels
       ]
       super().__init__(placeholder="Select panel", options=options)

   async def callback(self, interaction: discord.Interaction):
       await interaction.response.send_modal(EditPanelModal(self.values[0]))


class EditPanelView(discord.ui.View):
   def __init__(self, panels):
       super().__init__()
       self.add_item(EditPanelSelect(panels))


# ================= DELETE =================
class DeletePanelSelect(discord.ui.Select):
   def __init__(self, panels):
       options = [
           discord.SelectOption(label=str(p["_id"]), description="Delete panel")
           for p in panels
       ]
       super().__init__(placeholder="Select panel", options=options)

   async def callback(self, interaction: discord.Interaction):
       panel_id = self.values[0]

       cog = interaction.client.get_cog("PanelGUI")
       panel = await cog.collection.find_one({"_id": ObjectId(panel_id)})

       channel = interaction.guild.get_channel(panel["channel_id"])
       message = await channel.fetch_message(panel["message_id"])

       await message.delete()
       await cog.collection.delete_one({"_id": ObjectId(panel_id)})

       await interaction.response.send_message("🗑 Panel deleted", ephemeral=True, delete_after=3)


class DeletePanelView(discord.ui.View):
   def __init__(self, panels):
       super().__init__()
       self.add_item(DeletePanelSelect(panels))


# ================= COG =================
class PanelGUI(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["panels"]

   # CREATE
   @app_commands.command(name="createpanel", description="Create panel")
   async def createpanel(self, interaction: discord.Interaction):
       await interaction.response.send_modal(PanelModal())

   # EDIT
   @app_commands.command(name="editpanel", description="Edit panel")
   async def editpanel(self, interaction: discord.Interaction):
       panels = []
       async for p in self.collection.find({"guild_id": interaction.guild.id}):
           panels.append(p)

       if not panels:
           return await interaction.response.send_message("❌ No panels found", ephemeral=True)

       await interaction.response.send_message(
           "Select panel:",
           view=EditPanelView(panels),
           ephemeral=True
       )

   # DELETE
   @app_commands.command(name="deletepanel", description="Delete panel")
   async def deletepanel(self, interaction: discord.Interaction):
       panels = []
       async for p in self.collection.find({"guild_id": interaction.guild.id}):
           panels.append(p)

       if not panels:
           return await interaction.response.send_message("❌ No panels found", ephemeral=True)

       await interaction.response.send_message(
           "Select panel to delete:",
           view=DeletePanelView(panels),
           ephemeral=True
       )

   # PERSIST
   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ FULL GUI SYSTEM READY")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelGUI(bot))