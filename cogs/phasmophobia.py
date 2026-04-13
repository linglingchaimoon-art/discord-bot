import discord
from discord.ext import commands
import difflib

ALLOWED_CHANNEL_ID = 1493062544863264869  # 🔥 CHANGE THIS


# ================= FULL GHOST DATABASE =================
GHOSTS = {
   "spirit": {
       "evidence": ["EMF Level 5", "Spirit Box", "Ghost Writing"],
       "strength": "None",
       "weakness": "Smudge sticks stop it longer",
       "identify": "Long delay between hunts after smudge"
   },
   "wraith": {
       "evidence": ["EMF Level 5", "Spirit Box", "DOTS"],
       "strength": "Can teleport to players",
       "weakness": "Does not step in salt",
       "identify": "No footprints in salt"
   },
   "phantom": {
       "evidence": ["Spirit Box", "Fingerprints", "DOTS"],
       "strength": "Looking at it reduces sanity faster",
       "weakness": "Disappears in photos",
       "identify": "Invisible in ghost photo"
   },
   "poltergeist": {
       "evidence": ["Spirit Box", "Fingerprints", "Ghost Writing"],
       "strength": "Throws many objects",
       "weakness": "Useless in empty rooms",
       "identify": "Multi-object throws"
   },
   "banshee": {
       "evidence": ["Fingerprints", "Ghost Orbs", "DOTS"],
       "strength": "Targets one player",
       "weakness": "Afraid of crucifix",
       "identify": "Only hunts one player"
   },
   "jinn": {
       "evidence": ["EMF Level 5", "Freezing Temps", "Fingerprints"],
       "strength": "Fast when far away",
       "weakness": "Breaker off = slower",
       "identify": "Speed depends on breaker"
   },
   "mare": {
       "evidence": ["Spirit Box", "Ghost Orbs", "Ghost Writing"],
       "strength": "More active in dark",
       "weakness": "Less active in light",
       "identify": "Turns lights off often"
   },
   "revenant": {
       "evidence": ["Ghost Writing", "Freezing Temps", "Ghost Orbs"],
       "strength": "Very fast when chasing",
       "weakness": "Very slow otherwise",
       "identify": "Huge speed difference"
   },
   "shade": {
       "evidence": ["EMF Level 5", "Ghost Writing", "Freezing Temps"],
       "strength": "Hard to find",
       "weakness": "Won’t hunt with players nearby",
       "identify": "Very shy behavior"
   },
   "demon": {
       "evidence": ["Freezing Temps", "Ghost Writing", "Fingerprints"],
       "strength": "Hunts often",
       "weakness": "Crucifix range increased",
       "identify": "Early hunts"
   },
   "yokai": {
       "evidence": ["Spirit Box", "Ghost Orbs", "DOTS"],
       "strength": "Triggered by voice",
       "weakness": "Short hearing range",
       "identify": "Talking causes hunts"
   },
   "hantu": {
       "evidence": ["Fingerprints", "Ghost Orbs", "Freezing Temps"],
       "strength": "Fast in cold",
       "weakness": "Slow in warm",
       "identify": "Speed tied to temp"
   },
   "raiju": {
       "evidence": ["EMF Level 5", "Ghost Orbs", "DOTS"],
       "strength": "Faster near electronics",
       "weakness": "Disrupts electronics",
       "identify": "Fast near devices"
   },
   "obake": {
       "evidence": ["EMF Level 5", "Fingerprints", "Ghost Orbs"],
       "strength": "Leaves rare prints",
       "weakness": "Fingerprints change",
       "identify": "Unique fingerprints"
   },
   "mimic": {
       "evidence": ["Spirit Box", "Fingerprints", "Freezing Temps"],
       "strength": "Copies other ghosts",
       "weakness": "Always shows ghost orbs",
       "identify": "Extra fake evidence"
   },
   "moroi": {
       "evidence": ["Spirit Box", "Ghost Writing", "Freezing Temps"],
       "strength": "Gets faster over time",
       "weakness": "Weak to smudge",
       "identify": "Speed increases"
   },
   "deogen": {
       "evidence": ["Spirit Box", "Ghost Writing", "DOTS"],
       "strength": "Always finds you",
       "weakness": "Very slow close",
       "identify": "Knows location always"
   },
   "thaye": {
       "evidence": ["Ghost Writing", "Ghost Orbs", "DOTS"],
       "strength": "Fast when young",
       "weakness": "Gets weaker over time",
       "identify": "Slows with age"
   }
}


# ================= COG =================
class Phasmophobia(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   @commands.Cog.listener()
   async def on_message(self, message):

       if message.author.bot:
           return

       if message.channel.id != ALLOWED_CHANNEL_ID:
           return

       if not message.content.startswith("!"):
           return

       ghost_input = message.content[1:].lower()

       # ===== AUTO MATCH =====
       if ghost_input in GHOSTS:
           ghost_name = ghost_input
       else:
           matches = difflib.get_close_matches(ghost_input, GHOSTS.keys(), n=1, cutoff=0.5)
           if not matches:
               return
           ghost_name = matches[0]

       ghost = GHOSTS[ghost_name]

       # ===== NICE EMBED =====
       embed = discord.Embed(
           title=f"👻 {ghost_name.capitalize()}",
           description="━━━━━━━━━━━━━━━━━━",
           color=0x8e44ad
       )

       embed.add_field(
           name="🧪 Evidence",
           value="\n".join(f"• {e}" for e in ghost["evidence"]),
           inline=False
       )

       embed.add_field(
           name="💪 Strength",
           value=ghost["strength"],
           inline=False
       )

       embed.add_field(
           name="⚠️ Weakness",
           value=ghost["weakness"],
           inline=False
       )

       embed.add_field(
           name="🔍 How to Identify",
           value=ghost["identify"],
           inline=False
       )

       embed.set_footer(text="Phasmophobia Ghost Guide 👻")

       await message.channel.send(embed=embed)


async def setup(bot):
   await bot.add_cog(Phasmophobia(bot))