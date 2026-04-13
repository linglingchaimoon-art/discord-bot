import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI")


# ===== PARSE ROLES =====
def parse_roles(text):
   roles = []
   for part in text.split(","):
       part = part.strip()

       emoji = None
       if " " in part:
           *name_parts, emoji = part.split(" ")
           name = " ".join(name_parts)
       else:
           name = part

       roles.append({
           "name": name,
           "emoji": emoji
       })

   return roles


# ===== BUTTON =====
class RoleButton(discord.ui.Button):
   def __init__(self, data):
       super().__init__(
           label=data["name"],
           emoji=data["emoji"],
           style=discord.ButtonStyle.primary
       )
       self.role_name = data["name"]

   async def callback(self, interaction: discord.Interaction):
       role = discord.utils.get(interaction.guild.roles, name=self.role_name)

       if not role:
           return await interaction.response.send_message(
               "❌ Role not found",
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


# ===== VIEW =====
class RoleView(discord.ui.View):
   def __init__(self, roles):
       super().__init__(timeout=None)
       for r in roles:
           self.add_item(RoleButton(r))


# ===== CHANNEL SELECT =====
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
       await interaction.response.defer(ephemeral=True)

       try:
           raw = self.values[0]
           channel = interaction.guild.get_channel(raw.id)

           embed = discord.Embed(
               title=self.data["title"],
               description=self.data["description"] +
                           "\n\n━━━━━━━━━━━━━━━━━━\n✨ Click to get role\n❌ Click again to remove",
               color=0x5865F2
           )

           view = RoleView(self.data["roles"])

           # ===== PING =====
           ping = self.data["ping"]
           content = None

           if ping == "here":
               content = "@here"
           elif ping == "everyone":
               content = "@everyone"

           allowed = discord.AllowedMentions(everyone=True)

           msg = await channel.send(
               content=content,
               embed=embed,
               view=view,
               allowed_mentions=allowed
           )

           cog = interaction.client.get_cog("PanelGUI")

           await cog.collection.insert_one({
               "guild_id": interaction.guild.id,
               "channel_id": channel.id,
               "message_id": msg.id,
               "roles": self.data["roles"],
               "title": self.data["title"],
               "description": self.data["description"],
               "ping": ping
           })

           await interaction.followup.send(
               f"✅ Panel created in #{channel.name}",
               delete_after=3
           )

       except Exception as e:
           print("[ERROR]", e)
           await interaction.followup.send(
               f"❌ Error: {e}",
               delete_after=5
           )


class ChannelView(discord.ui.View):
   def __init__(self, data):
       super().__init__(timeout=60)
       self.add_item(ChannelSelect(data))


# ===== MODAL =====
class PanelModal(discord.ui.Modal, title="Create Panel"):

   title_input = discord.ui.TextInput(
       label="Title",
       placeholder="🎮 Gaming Roles"
   )

   description_input = discord.ui.TextInput(
       label="Description",
       style=discord.TextStyle.paragraph,
       placeholder="Choose your roles!"
   )

   roles_input = discord.ui.TextInput(
       label="Roles + Emoji",
       placeholder="Minecraft ⛏️, Staff ⭐"
   )

   ping_input = discord.ui.TextInput(
       label="Ping (here / everyone / none)",
       placeholder="here"
   )

   async def on_submit(self, interaction: discord.Interaction):
       roles = parse_roles(self.roles_input.value)

       ping = self.ping_input.value.lower()
       if ping not in ["here", "everyone", "none"]:
           return await interaction.response.send_message(
               "❌ Use: here / everyone / none",
               ephemeral=True
           )

       data = {
           "title": self.title_input.value,
           "description": self.description_input.value,
           "roles": roles,
           "ping": ping
       }

       await interaction.response.send_message(
           "📍 Select channel:",
           view=ChannelView(data),
           ephemeral=True
       )


# ===== COG =====
class PanelGUI(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["panels"]

   @app_commands.command(name="createpanel", description="Create panel")
   async def createpanel(self, interaction: discord.Interaction):
       await interaction.response.send_modal(PanelModal())

   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ PANEL SYSTEM READY")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelGUI(bot))