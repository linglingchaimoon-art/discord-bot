import discord
from discord.ext import commands
import datetime
import asyncio
import json
import os

# 🔧 CONFIG
CATEGORY_ID = 1491595300903719126
HELP_ROLE_ID = 1491598088534753400
SUPPORT_ROLE_ID = 1491590021633937654

PING_DELAY = 60  # seconds

TICKET_FILE = "tickets.json"


# -------------------------
# 💾 LOAD COUNTER
# -------------------------
def load_counter():
   if not os.path.exists(TICKET_FILE):
       with open(TICKET_FILE, "w") as f:
           json.dump({"count": 0}, f)

   with open(TICKET_FILE, "r") as f:
       return json.load(f)["count"]


def save_counter(count):
   with open(TICKET_FILE, "w") as f:
       json.dump({"count": count}, f)


ticket_counter = load_counter()


# -------------------------
# 👤 CLAIM + CLOSE
# -------------------------
class TicketControls(discord.ui.View):
   def __init__(self, bot, user):
       super().__init__(timeout=None)
       self.bot = bot
       self.user = user
       self.claimed_by = None

   @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="👤")
   async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

       if self.claimed_by:
           return await interaction.response.send_message(
               f"❌ Already claimed by {self.claimed_by.mention}",
               ephemeral=True
           )

       self.claimed_by = interaction.user
       button.label = f"Claimed by {interaction.user.name}"
       button.disabled = True

       await interaction.response.edit_message(view=self)
       await interaction.channel.send(f"👤 {interaction.user.mention} claimed this ticket")

   @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
   async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

       guild = interaction.guild
       help_role = guild.get_role(HELP_ROLE_ID)

       # 🔥 REMOVE HELP ROLE
       if help_role:
           try:
               await self.user.remove_roles(help_role)
           except:
               pass

       await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
       await interaction.channel.delete()


# -------------------------
# 🎫 CREATE BUTTON
# -------------------------
class TicketView(discord.ui.View):
   def __init__(self, bot):
       super().__init__(timeout=None)
       self.bot = bot

   @discord.ui.button(label="Create ticket", style=discord.ButtonStyle.secondary, emoji="📩")
   async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

       global ticket_counter

       guild = interaction.guild
       user = interaction.user

       # 🚫 Prevent duplicate
       for channel in guild.channels:
           if channel.name.startswith("ticket-") and user.name in channel.name:
               return await interaction.response.send_message(
                   "❌ You already have an open ticket!",
                   ephemeral=True
               )

       # 🎯 Roles
       help_role = guild.get_role(HELP_ROLE_ID)
       support_role = guild.get_role(SUPPORT_ROLE_ID)

       # ✅ Give Help role
       if help_role:
           try:
               await user.add_roles(help_role)
           except:
               pass

       # 🔢 Ticket number
       ticket_counter += 1
       save_counter(ticket_counter)

       ticket_number = str(ticket_counter).zfill(4)

       category = guild.get_channel(CATEGORY_ID)

       overwrites = {
           guild.default_role: discord.PermissionOverwrite(view_channel=False),
           user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
       }

       if support_role:
           overwrites[support_role] = discord.PermissionOverwrite(view_channel=True)

       # 🎫 Create channel
       channel = await guild.create_text_channel(
           name=f"ticket-{ticket_number}",
           category=category,
           overwrites=overwrites
       )

       embed = discord.Embed(
           title=f"🎫 Ticket #{ticket_number}",
           description="Support will be with you shortly.\nUse the buttons below.",
           colour=discord.Colour.green(),
           timestamp=datetime.datetime.utcnow()
       )

       view = TicketControls(self.bot, user)

       # 🔔 Ping support ONLY
       await channel.send(
           content=f"<@&{SUPPORT_ROLE_ID}>",
           embed=embed,
           view=view
       )

       await interaction.response.send_message(
           f"✅ Ticket created: {channel.mention}",
           ephemeral=True
       )

       # ⏱️ Start reminder loop
       self.bot.loop.create_task(self.reminder_ping(channel, view))

   # -------------------------
   # ⏱️ REMINDER SYSTEM
   # -------------------------
   async def reminder_ping(self, channel, view):
       while view.claimed_by is None:
           await asyncio.sleep(PING_DELAY)

           try:
               await channel.send(
                   f"⏰ <@&{SUPPORT_ROLE_ID}> this ticket is still unclaimed!"
               )
           except:
               break


# -------------------------
# 📌 PANEL
# -------------------------
class Ticket(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   @commands.command()
   async def ticketpanel(self, ctx):

       embed = discord.Embed(
           title="Support Tickets",
           description=(
               "To create a ticket use the Create ticket button\n\n"
           ),
           colour=discord.Colour.green()
       )

       await ctx.send(embed=embed, view=TicketView(self.bot))


# -------------------------
# ✅ SETUP
# -------------------------
async def setup(bot):
   await bot.add_cog(Ticket(bot))