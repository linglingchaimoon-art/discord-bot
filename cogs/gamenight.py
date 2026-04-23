import discord
from discord.ext import commands
from discord import app_commands

game_data = {}
temp_setup = {}

# ===== MODAL =====
class GameNightModal(discord.ui.Modal, title="🎮 Create Game Night"):
   time = discord.ui.TextInput(label="Time (YYYY-MM-DD HH:MM)", required=True)
   note = discord.ui.TextInput(label="Extra Note (optional)", required=False, style=discord.TextStyle.paragraph)

   async def on_submit(self, interaction: discord.Interaction):
       temp_setup[interaction.user.id] = {
           "time": self.time.value,
           "note": self.note.value,
           "host": interaction.user.id
       }

       await interaction.response.send_message("🎮 Select a game:", view=GameSelectView(), ephemeral=True)

# ===== GAME SELECT =====
class GameSelectView(discord.ui.View):
   @discord.ui.select(
       placeholder="Choose a game",
       options=[
           discord.SelectOption(label="PUBG", value="pubg"),
           discord.SelectOption(label="Minecraft", value="minecraft"),
           discord.SelectOption(label="Phasmophobia", value="phasmophobia"),
           discord.SelectOption(label="Among Us", value="amongus"),
           discord.SelectOption(label="Rocket League", value="rocketleague"),
       ]
   )
   async def select_game(self, interaction, select):
       data = temp_setup.get(interaction.user.id)
       data["game"] = select.values[0]

       await interaction.response.edit_message(content="🤝 Select a co-host:", view=CoHostView())

# ===== COHOST =====
class CoHostView(discord.ui.View):
   @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Select co-host", min_values=1, max_values=1)
   async def select_callback(self, interaction, select):
       data = temp_setup.get(interaction.user.id)

       cohost = select.values[0].id
       if cohost == interaction.user.id:
           return await interaction.response.send_message("❌ Can't pick yourself", ephemeral=True)

       data["cohost"] = cohost

       if data["game"] == "pubg":
           await interaction.response.edit_message(content="🎮 PUBG Setup:", view=PUBGView())
       elif data["game"] == "minecraft":
           await interaction.response.edit_message(content="🟩 Minecraft Setup:", view=MinecraftView())
       elif data["game"] == "phasmophobia":
           await interaction.response.edit_message(content="👻 Phasmophobia Setup:", view=PhasmophobiaView())
       elif data["game"] == "amongus":
           await interaction.response.edit_message(content="👨‍🚀 Among Us Setup:", view=AmongUsView())
       elif data["game"] == "rocketleague":
           await interaction.response.edit_message(content="🚗 Rocket League Setup:", view=RocketLeagueView())

# ===== PUBG =====
class PUBGView(discord.ui.View):

   @discord.ui.select(
       placeholder="Mode",
       options=[
           discord.SelectOption(label="Solo", value="solo"),
           discord.SelectOption(label="Duo", value="duo"),
           discord.SelectOption(label="Squad", value="squad"),
       ]
   )
   async def mode(self, interaction, select):
       temp_setup[interaction.user.id]["mode"] = select.values[0]
       await interaction.response.defer()

   @discord.ui.select(
       placeholder="Perspective",
       options=[
           discord.SelectOption(label="FPP", value="fpp"),
           discord.SelectOption(label="TPP", value="tpp"),
       ]
   )
   async def perspective(self, interaction, select):
       temp_setup[interaction.user.id]["perspective"] = select.values[0]
       await interaction.response.defer()

   @discord.ui.select(
       placeholder="Gamemode",
       options=[
           discord.SelectOption(label="Classic", value="classic"),
           discord.SelectOption(label="Ranked", value="ranked"),
           discord.SelectOption(label="Arcade", value="arcade"),
           discord.SelectOption(label="Custom", value="custom"),
       ]
   )
   async def gamemode(self, interaction, select):
       data = temp_setup.get(interaction.user.id)
       value = select.values[0]

       if value == "custom":
           return await interaction.response.send_modal(CustomModeModal())

       data["gamemode"] = value

       await interaction.response.edit_message(content="👥 Select player limit:", view=PlayerLimitView())

# ===== CUSTOM PUBG =====
class CustomModeModal(discord.ui.Modal, title="Custom Gamemode"):
   custom = discord.ui.TextInput(label="Enter custom gamemode", required=True)

   async def on_submit(self, interaction: discord.Interaction):
       data = temp_setup.get(interaction.user.id)
       data["gamemode"] = self.custom.value

       # ✅ FORCE UNLIMITED
       data["max"] = "unlimited"

       await interaction.response.edit_message(content="📢 Select ping:", view=PingView())

# ===== PLAYER LIMIT =====
class PlayerLimitView(discord.ui.View):

   @discord.ui.select(
       placeholder="Player limit",
       options=[
           discord.SelectOption(label="Unlimited", value="unlimited"),
           discord.SelectOption(label="Use Game Default", value="default"),
       ]
   )
   async def select_limit(self, interaction, select):
       data = temp_setup.get(interaction.user.id)

       if select.values[0] == "unlimited":
           data["max"] = "unlimited"
       else:
           data["max"] = get_default_max(data)

       await interaction.response.edit_message(content="📢 Select ping:", view=PingView())

# ===== DEFAULT LIMITS =====
def get_default_max(data):
   if data.get("game") == "pubg":
       return {"solo": 1, "duo": 2}.get(data.get("mode"), 4)
   if data.get("game") == "amongus":
       return 15
   if data.get("game") == "phasmophobia":
       return 4
   return 4

# ===== OTHER GAME VIEWS =====
class MinecraftView(discord.ui.View):
   @discord.ui.button(label="Set Server IP")
   async def ip(self, interaction, button):
       modal = discord.ui.Modal(title="Server IP")
       ip = discord.ui.TextInput(label="IP")
       modal.add_item(ip)

       async def callback(i):
           data = temp_setup.get(interaction.user.id)
           data["server"] = ip.value
           await interaction.response.edit_message(content="👥 Select player limit:", view=PlayerLimitView())

       modal.on_submit = callback
       await interaction.response.send_modal(modal)

class PhasmophobiaView(discord.ui.View):
   @discord.ui.select(placeholder="Difficulty", options=[
       discord.SelectOption(label="Amateur", value="amateur"),
       discord.SelectOption(label="Professional", value="pro"),
       discord.SelectOption(label="Nightmare", value="nightmare"),
   ])
   async def difficulty(self, interaction, select):
       temp_setup[interaction.user.id]["difficulty"] = select.values[0]
       await interaction.response.edit_message(content="👥 Select player limit:", view=PlayerLimitView())

class AmongUsView(discord.ui.View):
   @discord.ui.select(placeholder="Players", options=[
       discord.SelectOption(label="10", value="10"),
       discord.SelectOption(label="15", value="15"),
   ])
   async def players(self, interaction, select):
       data = temp_setup.get(interaction.user.id)
       data["max"] = int(select.values[0])
       await interaction.response.edit_message(content="📢 Select ping:", view=PingView())

class RocketLeagueView(discord.ui.View):
   @discord.ui.select(placeholder="Mode", options=[
       discord.SelectOption(label="2v2", value="2"),
       discord.SelectOption(label="3v3", value="3"),
   ])
   async def mode(self, interaction, select):
       temp_setup[interaction.user.id]["max"] = int(select.values[0]) * 2
       await interaction.response.edit_message(content="📢 Select ping:", view=PingView())

# ===== PING =====
class PingView(discord.ui.View):
   @discord.ui.select(placeholder="Ping option", options=[
       discord.SelectOption(label="No Ping", value="none"),
       discord.SelectOption(label="@here", value="here"),
       discord.SelectOption(label="@everyone", value="everyone"),
   ])
   async def ping(self, interaction, select):
       data = temp_setup.get(interaction.user.id)

       if select.values[0] == "everyone" and not interaction.user.guild_permissions.administrator:
           return await interaction.response.send_message("❌ Admin only", ephemeral=True)

       data["ping"] = "" if select.values[0] == "none" else f"@{select.values[0]}"
       await create_event(interaction, data)

# ===== EMBED =====
def build_embed(data):
   players = data["players"]
   max_players = data.get("max")

   text = f"{len(players)}/∞" if max_players == "unlimited" else f"{len(players)}/{max_players}"

   embed = discord.Embed(title=f"🎮 {data['game'].title()} Game Night")

   embed.add_field(name="👤 Host", value=f"<@{data['host']}>")
   embed.add_field(name="🤝 Co-host", value=f"<@{data['cohost']}>")
   embed.add_field(name="⏰ Time", value=data["time"])

   if data.get("note"):
       embed.add_field(name="📝 Note", value=data["note"], inline=False)

   if data.get("gamemode"):
       embed.add_field(name="🏆 Gamemode", value=data["gamemode"])

   embed.add_field(
       name=f"👥 Players ({text})",
       value="\n".join(f"<@{p}>" for p in players) if players else "No one yet",
       inline=False
   )

   return embed

# ===== BUTTONS =====
class EventView(discord.ui.View):

   @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
   async def join(self, interaction, button):
       event = game_data[interaction.message.id]

       if event.get("max") != "unlimited":
           if len(event["players"]) >= event["max"]:
               return await interaction.response.send_message("❌ Full", ephemeral=True)

       if interaction.user.id not in event["players"]:
           event["players"].append(interaction.user.id)

       await interaction.response.edit_message(embed=build_embed(event))

   @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
   async def leave(self, interaction, button):
       event = game_data[interaction.message.id]

       if interaction.user.id in event["players"]:
           event["players"].remove(interaction.user.id)

       await interaction.response.edit_message(embed=build_embed(event))

# ===== CREATE =====
async def create_event(interaction, data):
   data["players"] = []

   msg = await interaction.channel.send(
       content=data.get("ping"),
       embed=build_embed(data),
       view=EventView()
   )

   game_data[msg.id] = data
   await interaction.response.edit_message(content="✅ Event created!", view=None)

# ===== COG =====
class GameNight(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   @app_commands.command(name="gamenight", description="Create a game night")
   async def gamenight(self, interaction: discord.Interaction):
       await interaction.response.send_modal(GameNightModal())

async def setup(bot):
   await bot.add_cog(GameNight(bot))