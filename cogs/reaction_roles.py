import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

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
   def __init__(self, data, edit_id=None):
       super().__init__(
           placeholder="Select channel",
           min_values=1,
           max_values=1,
           channel_types=[discord.ChannelType.text]
       )
       self.data = data
       self.edit_id = edit_id

   async def callback(self, interaction: discord.Interaction):
       print("[DEBUG] Channel selected")

       await interaction.response.defer(ephemeral=True)

       try:
           raw = self.values[0]

           # 🔥 FIX
           channel = interaction.guild.get_channel(raw.id)

           if not channel:
               raise Exception("Channel not found")

           print(f"[DEBUG] Using channel: {channel.name}")

           cog = interaction.client.get_cog("PanelGUI")

           embed = discord.Embed(
               title=self.data["title"],
               description=self.data["description"] +
                           "\n\n━━━━━━━━━━━━━━━━━━\n✨ Click to get role\n❌ Click again to remove",
               color=0x5865F2
           )

           view = RoleView(self.data["roles"])

           # ===== CREATE NEW PANEL =====
           if not self.edit_id:
               msg = await channel.send(embed=embed, view=view)

               await cog.collection.insert_one({
                   "guild_id": interaction.guild.id,
                   "channel_id": channel.id,
                   "message_id": msg.id,
                   "roles": self.data["roles"],
                   "title": self.data["title"],
                   "description": self.data["description"]
               })

               await interaction.followup.send(
                   f"✅ Panel created in #{channel.name}",
                   delete_after=3
               )

           # ===== EDIT PANEL =====
           else:
               panel = await cog.collection.find_one({"_id": self.edit_id})

               old_channel = interaction.guild.get_channel(panel["channel_id"])
               message = await old_channel.fetch_message(panel["message_id"])

               # delete old
               await message.delete()

               # send new
               msg = await channel.send(embed=embed, view=view)

               await cog.collection.update_one(
                   {"_id": self.edit_id},
                   {"$set": {
                       "channel_id": channel.id,
                       "message_id": msg.id,
                       "roles": self.data["roles"],
                       "title": self.data["title"],
                       "description": self.data["description"]
                   }}
               )

               await interaction.followup.send(
                   f"✏️ Panel updated & moved to #{channel.name}",
                   delete_after=3
               )

       except Exception as e:
           print("[ERROR]", e)
           await interaction.followup.send(f"❌ Error: {e}", delete_after=5)


class ChannelView(discord.ui.View):
   def __init__(self, data, edit_id=None):
       super().__init__(timeout=60)
       self.add_item(ChannelSelect(data, edit_id))


# ================= MODAL =================
class PanelModal(discord.ui.Modal, title="Create / Edit Panel"):

   title_input = discord.ui.TextInput(
       label="Title",
       placeholder="Example: 🎮 Gaming Roles",
       required=True
   )

   description_input = discord.ui.TextInput(
       label="Description",
       style=discord.TextStyle.paragraph,
       placeholder="Example:\nChoose your roles below!",
       required=True
   )

   roles_input = discord.ui.TextInput(
       label="Roles (comma separated)",
       placeholder="Example: Minecraft, Valorant, Staff",
       required=True
   )

   def __init__(self, edit_id=None):
       super().__init__()
       self.edit_id = edit_id

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
           view=ChannelView(data, self.edit_id),
           ephemeral=True
       )


# ================= COG =================
class PanelGUI(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       print("[DEBUG] Connecting Mongo...")
       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["panels"]

   # ===== CREATE =====
   @app_commands.command(name="createpanel", description="Create panel GUI")
   async def createpanel(self, interaction: discord.Interaction):
       print("[DEBUG] /createpanel")
       await interaction.response.send_modal(PanelModal())

   # ===== EDIT =====
   @app_commands.command(name="editpanel", description="Edit panel")
   async def editpanel(self, interaction: discord.Interaction):
       print("[DEBUG] /editpanel")

       panels = []
       async for p in self.collection.find({"guild_id": interaction.guild.id}):
           panels.append(p)

       if not panels:
           return await interaction.response.send_message(
               "❌ No panels found",
               ephemeral=True
           )

       options = [
           discord.SelectOption(
               label=f"{p['title']} ({p['message_id']})",
               value=str(p["_id"])
           ) for p in panels
       ]

       class Select(discord.ui.Select):
           def __init__(self):
               super().__init__(placeholder="Select panel", options=options)

           async def callback(self, interaction2):
               panel_id = self.values[0]
               print(f"[DEBUG] Editing panel {panel_id}")

               await interaction2.response.send_modal(
                   PanelModal(edit_id=panel_id)
               )

       view = discord.ui.View()
       view.add_item(Select())

       await interaction.response.send_message(
           "Select panel to edit:",
           view=view,
           ephemeral=True
       )

   # ===== LOAD VIEWS =====
   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ PANEL SYSTEM READY")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelGUI(bot))