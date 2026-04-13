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
   "Jinn": ["⚡ Fast when far"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   "Revenant": ["🚀 Very fast"],
   }

BEHAVIOR = {
   "Fast": ["Revenant","Jinn"],
   "Slow Close": ["Deogen"],
   "No Salt": ["Wraith"]
}

EVIDENCE_LIST = ["EMF","Spirit Box","DOTS","Fingerprints","Writing","Freezing","Orbs"]

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

   async def callback(self, interaction: discord.Interaction):
       choice = self.values[0]

       # Clear everything
       self.parent_view.clear_items()

       # Always re-add main dropdown
       self.parent_view.add_item(MainDropdown(self.parent_view))

       # 👻 GHOST
       if choice == "Ghost Menu":
           self.parent_view.add_item(GhostSelect())

       # 📊 JOURNAL
       elif choice == "Journal":
           self.parent_view.add_item(EvidenceSelect())

       # 🧠 BEHAVIOR
       elif choice == "Behavior":
           self.parent_view.add_item(BehaviorSelect())

       # 🧿 CURSED
       elif choice == "Cursed Objects":
           embed = discord.Embed(
               title="🧿 Cursed Objects",
               description="Ouija Board\nTarot Cards\nMirror\nMusic Box\nSummoning Circle",
               color=0x9b59b6
           )

           return await interaction.response.edit_message(embed=embed, view=self.parent_view)

       await interaction.response.edit_message(
           content=f"🔄 Switched to **{choice}**",
           view=self.parent_view
       )

# ================= GHOST SELECT =================
class GhostSelect(discord.ui.Select):
   def __init__(self):
       options = [discord.SelectOption(label=g) for g in GHOSTS]
       super().__init__(placeholder="Select ghost...", options=options)

   async def callback(self, interaction):
       name = self.values[0]

       embed = discord.Embed(title=f"👻 {name}", color=0x6C5CE7)
       embed.add_field(name="🧪 Evidence", value="\n".join(GHOSTS[name]), inline=False)
       embed.add_field(name="🧠 Identify", value="\n".join(IDENTIFY[name]), inline=False)

       await interaction.response.edit_message(embed=embed)

# ================= JOURNAL =================
class EvidenceSelect(discord.ui.Select):
   def __init__(self):
       options = [discord.SelectOption(label=e) for e in EVIDENCE_LIST]
       super().__init__(placeholder="Select evidence...", options=options, min_values=1, max_values=3)

   async def callback(self, interaction):
       matches = [g for g, ev in GHOSTS.items() if all(e in ev for e in self.values)]

       text = "❌ No ghosts" if not matches else "\n".join(matches)

       embed = discord.Embed(title="📊 Result", description=text)

       await interaction.response.edit_message(embed=embed)

# ================= BEHAVIOR =================
class BehaviorSelect(discord.ui.Select):
   def __init__(self):
       options = [discord.SelectOption(label=b) for b in BEHAVIOR]
       super().__init__(placeholder="Select behavior...", options=options)

   async def callback(self, interaction):
       behavior = self.values[0]
       ghosts = BEHAVIOR[behavior]

       embed = discord.Embed(
           title=f"🧠 Behavior: {behavior}",
           description="\n".join(ghosts),
           color=0x00b894
       )

       await interaction.response.edit_message(embed=embed)

# ================= PANEL =================
class PanelView(discord.ui.View):
   def __init__(self):
       super().__init__(timeout=None)

   @discord.ui.button(label="🎛 Open Panel", style=discord.ButtonStyle.success)
   async def open_panel(self, interaction, button):
       await interaction.response.send_message(
           "Select option below 👇",
           view=MainView(),
           ephemeral=True
       )

# ================= CHANNEL SELECT =================
class ChannelSelect(discord.ui.ChannelSelect):
   def __init__(self):
       super().__init__(channel_types=[discord.ChannelType.text])

   async def callback(self, interaction):
       await interaction.response.defer(ephemeral=True)

       channel = interaction.guild.get_channel(self.values[0].id)

       embed = discord.Embed(
           title="👻 Phasmophobia Panel",
           description="Use button below 👇",
           color=0x5865F2
       )

       await channel.send(embed=embed, view=PanelView())
       await interaction.followup.send(f"✅ Sent to {channel.mention}", ephemeral=True)

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
       await interaction.response.send_message(
           "Select channel:",
           view=ChannelSelectView(),
           ephemeral=True
       )

   @commands.Cog.listener()
   async def on_ready(self):
       self.bot.add_view(PanelView())
       self.bot.add_view(MainView())
       print("✅ FINAL SYSTEM READY")

async def setup(bot):
   await bot.add_cog(Phasmophobia(bot))