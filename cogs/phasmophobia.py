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

      super().__init__(placeholder="Select option...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()

      choice = self.values[0]

      self.parent_view.clear_items()
      self.parent_view.add_item(MainDropdown(self.parent_view))

      if choice == "Ghost Menu":
          self.parent_view.add_item(GhostSelect(page=1))
          self.parent_view.add_item(NextPageButton())
          self.parent_view.add_item(SearchButton())  # modal search
          self.parent_view.add_item(GhostSearchDropdown())  # live search

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

# ================= LIVE SEARCH DROPDOWN =================
class GhostSearchDropdown(discord.ui.Select):
  def __init__(self):
      options = [discord.SelectOption(label=g) for g in list(GHOSTS.keys())[:25]]

      super().__init__(placeholder="🔍 Search ghost...", options=options)

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
      view.add_item(SearchButton())
      view.add_item(GhostSearchDropdown())

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
      view.add_item(SearchButton())
      view.add_item(GhostSearchDropdown())

      await interaction.followup.edit_message(interaction.message.id, view=view)

# ================= MODAL SEARCH =================
class SearchButton(discord.ui.Button):
  def __init__(self):
      super().__init__(label="🔍 Search", style=discord.ButtonStyle.primary)

  async def callback(self, interaction):
      await interaction.response.send_modal(GhostSearchModal())

class GhostSearchModal(discord.ui.Modal, title="Search Ghost"):
  search = discord.ui.TextInput(label="Ghost name")

  async def on_submit(self, interaction):
      query = self.search.value.lower()

      results = [g for g in GHOSTS if query in g.lower()]

      if not results:
          return await interaction.response.send_message("❌ No ghost found", ephemeral=True)

      exact = [g for g in GHOSTS if g.lower() == query]
      name = exact[0] if exact else results[0]

      embed = discord.Embed(title=f"👻 {name}", color=0x6C5CE7)
      embed.add_field(name="🧪 Evidence", value="\n".join(GHOSTS[name]), inline=False)
      embed.add_field(name="🧠 Identify", value="\n".join(IDENTIFY[name]), inline=False)

      await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=20)

# ================= KEEP OLD =================
class SearchResultSelect(discord.ui.Select):
  def __init__(self, results):
      options = [discord.SelectOption(label=g) for g in results]
      super().__init__(placeholder="Select ghost...", options=options)

  async def callback(self, interaction):
      await interaction.response.defer()