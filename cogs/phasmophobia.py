import discord
from discord.ext import commands
from discord import app_commands

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

print(f"[DEBUG] Ghost count: {len(GHOSTS)}")

# ================= MAIN VIEW =================
class MainView(discord.ui.View):
  def __init__(self):
      super().__init__(timeout=None)
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

      super().__init__(placeholder="Select option...", options=options, custom_id="main_dropdown")

  async def callback(self, interaction):
      print(f"[DEBUG] Menu: {self.values[0]}")
      await interaction.response.defer()

      choice = self.values[0]

      self.parent_view.clear_items()
      self.parent_view.add_item(MainDropdown(self.parent_view))

      if choice == "Ghost Menu":
          self.parent_view.add_item(GhostSelect(page=1))
          self.parent_view.add_item(NextPageButton())
          self.parent_view.add_item(SearchButton())  # ✅ ADDED

      elif choice == "Journal":
          self.parent_view.add_item(EvidenceSelect())

      elif choice == "Behavior":
          self.parent_view.add_item(BehaviorSelect())

      elif choice == "Cursed Objects":
          embed = discord.Embed(
              title="🧿 Cursed Objects",
              description="Ouija Board\nTarot Cards\nMirror\nMusic Box\nSummoning Circle",
              color=0x9b59b6
          )
          return await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.parent_view)

      await interaction.followup.edit_message(interaction.message.id, view=self.parent_view)

# ================= GHOST SELECT =================
class GhostSelect(discord.ui.Select):
  def __init__(self, page=1):
      ghosts = PAGE1 if page == 1 else PAGE2
      options = [discord.SelectOption(label=g) for g in ghosts]

      super().__init__(placeholder=f"Select ghost (Page {page})...", options=options, custom_id=f"ghost_{page}")

  async def callback(self, interaction):
      await interaction.response.defer()
      name = self.values[0]

      embed = discord.Embed(title=f"👻 {name}", color=0x6C5CE7)
      embed.add_field(name="🧪 Evidence", value="\n".join(GHOSTS[name]), inline=False)
      embed.add_field(name="🧠 Identify", value="\n".join(IDENTIFY[name]), inline=False)

      await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.view)

# ================= PAGE BUTTONS =================
class NextPageButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="➡️ Next", style=discord.ButtonStyle.secondary, custom_id="next")

  async def callback(self, interaction):
      await interaction.response.defer()
      view = self.view
      view.clear_items()
      view.add_item(MainDropdown(view))
      view.add_item(GhostSelect(page=2))
      view.add_item(PrevPageButton())
      view.add_item(SearchButton())
      await interaction.followup.edit_message(interaction.message.id, view=view)

class PrevPageButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="⬅️ Back", style=discord.ButtonStyle.secondary, custom_id="prev")

  async def callback(self, interaction):
      await interaction.response.defer()
      view = self.view
      view.clear_items()
      view.add_item(MainDropdown(view))
      view.add_item(GhostSelect(page=1))
      view.add_item(NextPageButton())
      view.add_item(SearchButton())
      await interaction.followup.edit_message(interaction.message.id, view=view)

# ================= SEARCH =================
class SearchButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="🔍 Search", style=discord.ButtonStyle.primary)

  async def callback(self, interaction):
      await interaction.response.send_modal(GhostSearchModal())

class GhostSearchModal(discord.ui.Modal, title="Search Ghost"):
  search = discord.ui.TextInput(label="Name", placeholder="Type ghost...")

  async def on_submit(self, interaction):
      query = self.search.value.lower()
      results = [g for g in GHOSTS if query in g.lower()][:25]

      if not results:
          return await interaction.response.send_message("❌ Not found", ephemeral=True)

      view = discord.ui.View()
      view.add_item(SearchResultSelect(results))

      await interaction.response.send_message("Results:", view=view, ephemeral=True)

class SearchResultSelect(discord.ui.Select):
  def __init__(self, results):
      options = [discord.SelectOption(label=g) for g in results]
      super().__init__(placeholder="Select ghost...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()
      name = self.values[0]

      embed = discord.Embed(title=f"👻 {name}", color=0x6C5CE7)
      embed.add_field(name="🧪 Evidence", value="\n".join(GHOSTS[name]), inline=False)
      embed.add_field(name="🧠 Identify", value="\n".join(IDENTIFY[name]), inline=False)

      await interaction.followup.send(embed=embed, ephemeral=True)

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
class PanelView(discord.ui.View):
  def __init__(self):
      super().__init__(timeout=None)

  @discord.ui.button(label="🎛 Open Panel", style=discord.ButtonStyle.success)
  async def open_panel(self, interaction, button):
      await interaction.response.send_message("Select option below 👇", view=MainView(), ephemeral=True)

# ================= CHANNEL =================
class ChannelSelect(discord.ui.ChannelSelect):
  def __init__(self):
      super().__init__(channel_types=[discord.ChannelType.text])

  async def callback(self, interaction):
      await interaction.response.defer(ephemeral=True)
      channel = interaction.guild.get_channel(self.values[0].id)

      embed = discord.Embed(title="👻 Phasmophobia Panel By TJ", description="This panel is designed to assist investigators in locating and identifying ghosts. Use the buttons below :point_down:")
      await channel.send(embed=embed, view=PanelView())
      await interaction.followup.send("✅ Sent", ephemeral=True)

class ChannelSelectView(discord.ui.View):
  def __init__(self):
      super().__init__()
      self.add_item(ChannelSelect())

# ================= COG =================
class Phasmophobia(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @app_commands.command(name="crghostpanel")
  async def panel(self, interaction):
      await interaction.response.send_message("Select channel:", view=ChannelSelectView(), ephemeral=True)

  @commands.Cog.listener()
  async def on_ready(self):
      self.bot.add_view(PanelView())
      self.bot.add_view(MainView())
      print("READY")

async def setup(bot):
  await bot.add_cog(Phasmophobia(bot))