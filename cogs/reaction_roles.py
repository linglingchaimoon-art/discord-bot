import discord
from discord.ext import commands
from discord import app_commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI")


# ================= BUTTON =================
class RoleButton(discord.ui.Button):
   def __init__(self, role_name):
       super().__init__(
           label=role_name,
           style=discord.ButtonStyle.primary
       )
       self.role_name = role_name

   async def callback(self, interaction: discord.Interaction):
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


# ================= VIEW =================
class RoleView(discord.ui.View):
   def __init__(self, roles):
       super().__init__(timeout=None)

       for role_name in roles:
           self.add_item(RoleButton(role_name))


# ================= MODAL =================
class PanelModal(discord.ui.Modal, title="Create Role Panel"):

   title_input = discord.ui.TextInput(
       label="Panel Title",
       placeholder="Gaming Roles",
       required=True
   )

   description_input = discord.ui.TextInput(
       label="Description",
       style=discord.TextStyle.paragraph,
       placeholder="Choose your roles...",
       required=True
   )

   channel_input = discord.ui.TextInput(
       label="Channel ID",
       placeholder="Paste channel ID",
       required=True
   )

   roles_input = discord.ui.TextInput(
       label="Roles (comma separated)",
       placeholder="Minecraft, Valorant, Fortnite",
       required=True
   )

   async def on_submit(self, interaction: discord.Interaction):

       await interaction.response.defer(ephemeral=True)

       try:
           channel_id = int(self.channel_input.value)
           channel = interaction.guild.get_channel(channel_id)

           if not channel:
               return await interaction.followup.send("❌ Invalid channel", delete_after=5)

           # 🔥 PARSE ROLES
           roles = [r.strip() for r in self.roles_input.value.split(",")]

           embed = discord.Embed(
               title=self.title_input.value,
               description=(
                   self.description_input.value
                   + "\n\n━━━━━━━━━━━━━━━━━━\n"
                   + "✨ Click to get role\n❌ Click again to remove"
               ),
               color=0x5865F2
           )

           view = RoleView(roles)

           msg = await channel.send(embed=embed, view=view)

           # 🔥 SAVE TO MONGO
           cog = interaction.client.get_cog("PanelGUI")
           await cog.collection.insert_one({
               "guild_id": interaction.guild.id,
               "message_id": msg.id,
               "channel_id": channel.id,
               "roles": roles
           })

           await interaction.followup.send("✅ Panel created", delete_after=3)

       except Exception as e:
           print("ERROR:", e)
           await interaction.followup.send("❌ Failed to create panel", delete_after=5)


# ================= COG =================
class PanelGUI(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

       self.client = AsyncIOMotorClient(MONGO_URI)
       self.db = self.client["discord_bot"]
       self.collection = self.db["panels"]

   @app_commands.command(name="createpanel", description="Create panel with GUI")
   async def createpanel(self, interaction: discord.Interaction):
       await interaction.response.send_modal(PanelModal())

   @commands.Cog.listener()
   async def on_ready(self):
       print("✅ Custom GUI system ready")

       async for panel in self.collection.find():
           self.bot.add_view(RoleView(panel["roles"]))


async def setup(bot):
   await bot.add_cog(PanelGUI(bot))