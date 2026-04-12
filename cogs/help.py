import discord
from discord.ext import commands, tasks
from discord import app_commands
import itertools

OWNER_ID = 1398304429085556746

colors = itertools.cycle([
   0x1DB954,
   0x5865F2,
   0xFF5555,
   0x00FFFF
])

# -------------------------
# DROPDOWN
# -------------------------
class HelpSelect(discord.ui.Select):
   def __init__(self, pages, user):
       self.pages = pages
    
       options = [
           discord.SelectOption(label="Home", emoji="🏠", value="Home"),
           discord.SelectOption(label="Games", emoji="🎮", value="Games"),
           discord.SelectOption(label="Music", emoji="🎵", value="Music"),
       ]

       # 🔒 ONLY SHOW MODERATION IF USER HAS PERMISSION
       if user.guild_permissions.manage_messages:
           options.insert(1, discord.SelectOption(label="Moderation", emoji="🔨", value="Moderation"))

       super().__init__(placeholder="Select a category...", options=options)

   async def callback(self, interaction: discord.Interaction):
       selected = self.values[0]

       if selected == "Moderation" and not interaction.user.guild_permissions.manage_messages:
           return await interaction.response.send_message("❌ No permission", ephemeral=True)

       self.view.current = selected
       self.view.cog.active_messages[interaction.message]["page"] = selected

       await interaction.response.edit_message(
           embed=self.pages[selected],
           view=self.view
       )

# -------------------------
# VIEW
# -------------------------
class HelpView(discord.ui.View):
   def __init__(self, pages, author, cog):
       super().__init__(timeout=None)
       self.pages = pages
       self.author = author
       self.cog = cog
       self.current = "Home"

       self.add_item(HelpSelect(pages, author))

   async def interaction_check(self, interaction: discord.Interaction):
       if interaction.user != self.author:
           await interaction.response.send_message("❌ This menu isn't for you.", ephemeral=True)
           return False
       return True

   @discord.ui.button(label="Home", style=discord.ButtonStyle.secondary, emoji="🏠")
   async def home_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
       self.current = "Home"
       self.cog.active_messages[interaction.message]["page"] = "Home"

       await interaction.response.edit_message(
           embed=self.pages["Home"],
           view=self
       )

   @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
   async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
       await interaction.message.delete()

# -------------------------
# COG
# -------------------------
class Help(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.active_messages = {}

       self.animate.start()

   # 🎨 ANIMATION
   @tasks.loop(seconds=5)
   async def animate(self):
       for message, data in list(self.active_messages.items()):
           try:
               page = data["page"]
               embed = data["pages"][page]

               embed.color = next(colors)

               await message.edit(embed=embed, view=data["view"])
           except:
               self.active_messages.pop(message, None)

   # -------------------------
   # /help
   # -------------------------
   @app_commands.command(name="help", description="Show the help menu")
   async def help_slash(self, interaction: discord.Interaction):

       prefix = "!"

       # 🏠 HOME
       home = discord.Embed(
           title="📖 Help Menu",
           description="Select a category below",
           colour=next(colors)
       )

       home.add_field(
           name="Categories",
           value="🏠 Home\n🔨 Moderation\n🎮 Games\n🎵 Music",
           inline=False
       )

       # 🔨 MODERATION
       moderation = discord.Embed(
           title="🔨 Moderation Commands",
           description="Admin tools & dashboard",
           colour=next(colors)
       )

       moderation.add_field(name="🎛 Dashboard", value="!modpanel @user", inline=False)
       moderation.add_field(name="🔨 Actions", value="/ban\n/kick\n/mute\n/unmute", inline=False)
       moderation.add_field(name="🔓 Unban", value="/unban user_id:<id>", inline=False)
       moderation.add_field(name="🔍 Ban List", value="/banlist", inline=False)
       moderation.add_field(name="📊 Cases", value="/case <id>\n/cases @user", inline=False)
       moderation.add_field(name="👤 User", value="/user @user", inline=False)

       # 🎮 BLACKJACK
       games = discord.Embed(
           title="🎮 Blackjack",
           description="Casino-style blackjack system",
           colour=next(colors)
       )

       games.add_field(
           name="🃏 Commands",
           value=(
               "`!blackjack <amount>`\n"
               "`!blackjack all`\n"
               "`!balance`\n"
               "`!balance @user`\n"
               "`!daily`"
           ),
           inline=False
       )

       games.add_field(
           name="💸 Economy",
           value="`!pay`\n`!steal`",
           inline=False
       )

       if interaction.user.id == OWNER_ID:
           games.add_field(
               name="👑 Owner",
               value="`!addbalance`\n`!removebalance`",
               inline=False
           )

       games.add_field(
           name="✨ Features",
           value="Economy 💰\nRisk 🎲\nCooldowns ⏱",
           inline=False
       )

       # 🎵 MUSIC
       music = discord.Embed(
           title="🎵 Music Bot",
           description="Spotify-style music system",
           colour=next(colors)
       )

       music.add_field(
           name="🎶 Commands",
           value=(
               "`!play <song>`\n"
               "`!pause`\n"
               "`!resume`\n"
               "`!skip`\n"
               "`!stop`\n"
               "`!queue`"
           ),
           inline=False
       )

       music.add_field(
           name="🎮 Controls",
           value="▶ ⏸ 🔁 🔀 ⏭ ⏹",
           inline=False
       )

       music.add_field(
           name="✨ Features",
           value="Progress bar 🔴\nQueue 📜\nLoop 🔁\nShuffle 🔀",
           inline=False
       )

       # -------------------------
       # PAGES
       # -------------------------
       pages = {
           "Home": home,
           "Moderation": moderation,
           "Games": games,
           "Music": music
       }

       view = HelpView(pages, interaction.user, self)

       await interaction.response.send_message(
           embed=home,
           view=view
       )

       msg = await interaction.original_response()

       self.active_messages[msg] = {
           "pages": pages,
           "page": "Home",
           "view": view
       }

# -------------------------
# SETUP
# -------------------------
async def setup(bot):
   await bot.add_cog(Help(bot))