import discord
from discord.ext import commands
from discord import app_commands
import difflib

# ================= SETTINGS =================
PANEL_TIMEOUT = 10  # ⏱ CHANGE TIME HERE (seconds)

# ================= SESSION STORAGE =================
active_panels = {}  # user_id : message

# ================= BASE VIEW =================
class BaseView(discord.ui.View):
    def __init__(self, timeout=PANEL_TIMEOUT):
        super().__init__(timeout=timeout)
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        try:
            if self.message:
                await self.message.edit(view=self)
        except:
            pass

# ================= DATA =================
GHOSTS = {
  "Banshee": ["Fingerprints","Orbs","DOTS"],
  "Dayan": ["EMF","Orbs","Spirit Box"],
  "Deogen": ["Writing","Spirit Box","DOTS"],
  "Demon": ["Fingerprints","Writing","Freezing"],
  "Gallu": ["EMF","Fingerprints","Spirit Box"],
  "Goryo": ["EMF","Fingerprints","DOTS"],
  "Hantu": ["Fingerprints","Orbs","Freezing"],
  "Jinn": ["EMF","Fingerprints","Freezing"],
  "Mare": ["Spirit Box","Orbs","Writing"],
  "Moroi": ["Writing","Spirit Box","Freezing"],
  "Myling": ["EMF","Fingerprints","Writing"],
  "Obake": ["EMF","Fingerprints","Orbs"],
  "Obambo": ["Fingerprints","Writing","DOTS"],
  "Oni": ["EMF","Freezing","DOTS"],
  "Onryo": ["Spirit Box","Orbs","Freezing"],
  "Phantom": ["Spirit Box","Fingerprints","DOTS"],
  "Poltergeist": ["Spirit Box","Fingerprints","Writing"],
  "Raiju": ["EMF","Orbs","DOTS"],
  "Revenant": ["Orbs","Writing","Freezing"],
  "Shade": ["EMF","Writing","Freezing"],
  "Spirit": ["EMF","Spirit Box","Writing"],
  "Thaye": ["Orbs","Writing","DOTS"],
  "The Mimic": ["Spirit Box","Fingerprints","Freezing"],
  "The Twins": ["EMF","Spirit Box","Freezing"],
  "Wraith": ["EMF","Spirit Box","DOTS"],
  "Yokai": ["Spirit Box","Orbs","DOTS"],
  "Yurei": ["Orbs","Freezing","DOTS"],
}

IDENTIFY = {
  "Banshee": ["⚡ Fast when far"],
  "Dayan": ["🚀 Very fast"],
  "Deogen": ["🚀 Very fast"],
  "Demon": ["🚀 Very fast"],
  "Gallu": ["🚀 Very fast"],
  "Goryo": ["🚀 Very fast"],
  "Hantu": ["🚀 Very fast"],
  "Jinn": ["🚀 Very fast"],
  "Mare": ["🚀 Very fast"],
  "Moroi": ["🚀 Very fast"],
  "Myling": ["🚀 Very fast"],
  "Obake": ["🚀 Very fast"],
  "Obambo": ["🚀 Very fast"],
  "Oni": ["🚀 Very fast"],
  "Onryo": ["🚀 Very fast"],
  "Phantom": ["🚀 Very fast"],
  "Poltergeist": ["🚀 Very fast"],
  "Raiju": ["🚀 Very fast"],
  "Revenant": ["🚀 Very fast"],
  "Shade": ["🚀 Very fast"],
  "Spirit": ["🚀 Very fast"],
  "Thaye": ["🚀 Very fast"],
  "The Mimic": ["🚀 Very fast"],
  "The Twins": ["🚀 Very fast"],
  "Wraith": ["🚀 Very fast"],
  "Yokai": ["🚀 Very fast"],
  "Yurei": ["🚀 Very fast"],
}

BEHAVIOR = {
  "Fast": ["Revenant","Jinn"],
  "Slow Close": ["Deogen"],
  "No Salt": ["Wraith"]
}

EVIDENCE_LIST = ["EMF","Spirit Box","DOTS","Fingerprints","Writing","Freezing","Orbs"]

# ================= SPLIT =================
ghost_list = list(GHOSTS.keys())
PAGE1 = ghost_list[:14]
PAGE2 = ghost_list[14:]

# ================= MAIN VIEW =================
class MainView(BaseView):
  def __init__(self):
      super().__init__()
      self.add_item(MainDropdown(self))

# ================= MAIN DROPDOWN =================
class MainDropdown(discord.ui.Select):
  def __init__(self, parent):
      self.parent_view = parent

      options = [
          discord.SelectOption(label="Ghost Menu", emoji="👻"),
          discord.SelectOption(label="Journal", emoji="📊"),
          discord.SelectOption(label="Behavior", emoji="🧠"),
          discord.SelectOption(label="Cursed Objects", emoji="🧿"),
      ]

      super().__init__(placeholder="Select option...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()

      choice = self.values[0]

      self.parent_view.clear_items()
      self.parent_view.add_item(MainDropdown(self.parent_view))

      if choice == "Ghost Menu":
          self.parent_view.add_item(GhostSelect(page=1))
          self.parent_view.add_item(NextPageButton())

      elif choice == "Journal":
          self.parent_view.add_item(EvidenceSelect())

      elif choice == "Behavior":
          self.parent_view.add_item(BehaviorSelect())

      await interaction.followup.edit_message(
          interaction.message.id,
          view=self.parent_view
      )

# ================= GHOST SELECT =================
class GhostSelect(discord.ui.Select):
  def __init__(self, page=1):
      ghosts = PAGE1 if page == 1 else PAGE2
      options = [discord.SelectOption(label=g) for g in ghosts]

      super().__init__(placeholder=f"Select ghost (Page {page})...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()

      name = self.values[0]

      embed = discord.Embed(title=f"👻 {name}", color=0x6C5CE7)
      embed.add_field(name="🧪 Evidence", value="\n".join(GHOSTS[name]), inline=False)
      embed.add_field(name="🧠 Identify", value="\n".join(IDENTIFY[name]), inline=False)

      await interaction.followup.edit_message(
          interaction.message.id,
          embed=embed,
          view=self.view
      )

# ================= PAGE BUTTONS =================
class NextPageButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="➡️ Next", style=discord.ButtonStyle.secondary)

  async def callback(self, interaction):
      await interaction.response.defer()
      view = self.view
      view.clear_items()
      view.add_item(MainDropdown(view))
      view.add_item(GhostSelect(page=2))
      view.add_item(PrevPageButton())

      await interaction.followup.edit_message(interaction.message.id, view=view)

class PrevPageButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="⬅️ Back", style=discord.ButtonStyle.secondary)

  async def callback(self, interaction):
      await interaction.response.defer()
      view = self.view
      view.clear_items()
      view.add_item(MainDropdown(view))
      view.add_item(GhostSelect(page=1))
      view.add_item(NextPageButton())

      await interaction.followup.edit_message(interaction.message.id, view=view)

# ================= OTHER =================
class EvidenceSelect(discord.ui.Select):
  def __init__(self):
      options = [discord.SelectOption(label=e) for e in EVIDENCE_LIST]
      super().__init__(placeholder="Select evidence...", options=options, min_values=1, max_values=3)

  async def callback(self, interaction):
      await interaction.response.defer()
      matches = [g for g, ev in GHOSTS.items() if all(e in ev for e in self.values)]
      embed = discord.Embed(title="Result", description="\n".join(matches) if matches else "None")
      await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.view)

class BehaviorSelect(discord.ui.Select):
  def __init__(self):
      options = [discord.SelectOption(label=b) for b in BEHAVIOR]
      super().__init__(placeholder="Select behavior...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()
      b = self.values[0]
      embed = discord.Embed(title=b, description="\n".join(BEHAVIOR[b]))
      await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.view)

# ================= PANEL =================
class PanelView(BaseView):
  def __init__(self):
      super().__init__()

  @discord.ui.button(label="🎛 Open Panel", style=discord.ButtonStyle.success)
  async def open_panel(self, interaction, button):

      # 🔁 REMOVE OLD PANEL (1 per user)
      old_msg = active_panels.get(interaction.user.id)
      if old_msg:
          try:
              await old_msg.delete()
          except:
              pass

      view = MainView()

      await interaction.response.send_message(
          "Select option below 👇",
          view=view,
          ephemeral=True
      )

      msg = await interaction.original_response()
      view.message = msg

      active_panels[interaction.user.id] = msg

# ================= CHANNEL =================
class ChannelSelect(discord.ui.ChannelSelect):
  def __init__(self):
      super().__init__(channel_types=[discord.ChannelType.text])

  async def callback(self, interaction):
      await interaction.response.defer(ephemeral=True)
      channel = interaction.guild.get_channel(self.values[0].id)

      embed = discord.Embed(title="👻 Phasmophobia Panel By TJ")

      view = PanelView()
      msg = await channel.send(embed=embed, view=view)
      view.message = msg

      await interaction.followup.send("✅ Sent", ephemeral=True)

class ChannelSelectView(BaseView):
  def __init__(self):
      super().__init__()
      self.add_item(ChannelSelect())

# ================= COG =================
class Phasmophobia(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @app_commands.command(name="crghostpanel")
  async def panel(self, interaction):
      view = ChannelSelectView()

      await interaction.response.send_message(
          "Select channel:",
          view=view,
          ephemeral=True
      )

      view.message = await interaction.original_response()

  @commands.Cog.listener()
  async def on_ready(self):
      self.bot.add_view(PanelView())
      self.bot.add_view(MainView())
      print("READY")

async def setup(bot):
  await bot.add_cog(Phasmophobia(bot))