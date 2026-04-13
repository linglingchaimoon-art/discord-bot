import discord
from discord.ext import commands
import difflib

ALLOWED_CHANNEL_ID = 123456789012345678  # 🔥 CHANGE THIS

print("[DEBUG] Phasmo system loaded")


# ================= DATABASE =================
GHOSTS = {
   "spirit": {"evidence": ["emf", "spirit box", "writing"]},
   "wraith": {"evidence": ["emf", "spirit box", "dots"]},
   "phantom": {"evidence": ["spirit box", "fingerprints", "dots"]},
   "poltergeist": {"evidence": ["spirit box", "fingerprints", "writing"]},
   "banshee": {"evidence": ["fingerprints", "orbs", "dots"]},
   "jinn": {"evidence": ["emf", "freezing", "fingerprints"]},
   "mare": {"evidence": ["spirit box", "orbs", "writing"]},
   "revenant": {"evidence": ["writing", "freezing", "orbs"]},
   "shade": {"evidence": ["emf", "writing", "freezing"]},
   "demon": {"evidence": ["freezing", "writing", "fingerprints"]},
   "yurei": {"evidence": ["freezing", "orbs", "dots"]},
   "oni": {"evidence": ["emf", "freezing", "dots"]},
   "yokai": {"evidence": ["spirit box", "orbs", "dots"]},
   "hantu": {"evidence": ["fingerprints", "orbs", "freezing"]},
   "goryo": {"evidence": ["emf", "fingerprints", "dots"]},
   "myling": {"evidence": ["emf", "fingerprints", "writing"]},
   "onryo": {"evidence": ["spirit box", "orbs", "freezing"]},
   "twins": {"evidence": ["emf", "spirit box", "freezing"]},
   "raiju": {"evidence": ["emf", "orbs", "dots"]},
   "obake": {"evidence": ["emf", "fingerprints", "orbs"]},
   "mimic": {"evidence": ["spirit box", "fingerprints", "freezing"]},
   "moroi": {"evidence": ["spirit box", "writing", "freezing"]},
   "deogen": {"evidence": ["spirit box", "writing", "dots"]},
   "thaye": {"evidence": ["writing", "orbs", "dots"]}
}


# ================= COG =================
class Phasmophobia(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       print("[DEBUG] Cog initialized")

   @commands.Cog.listener()
   async def on_message(self, message):

       if message.author.bot:
           return

       if message.channel.id != ALLOWED_CHANNEL_ID:
           return

       if not message.content.startswith("!"):
           return

       print(f"[DEBUG] Command: {message.content}")

       # 🔥 ANTI DUPLICATE
       if hasattr(message, "_handled"):
           return
       message._handled = True

       args = message.content.lower().split()

       # ================= EVIDENCE COMMAND =================
       if args[0] == "!evidence":

           if len(args) < 2:
               await message.channel.send("❌ Usage: !evidence emf freezing")
               return

           search = args[1:]
           print(f"[DEBUG] Searching evidence: {search}")

           matches = []

           for ghost, data in GHOSTS.items():
               if all(e in data["evidence"] for e in search):
                   matches.append(ghost.capitalize())

           if not matches:
               await message.channel.send("❌ No ghosts found with that evidence")
               return

           embed = discord.Embed(
               title="🔍 Possible Ghosts",
               description="\n".join(f"👻 {g}" for g in matches),
               color=0x3498db
           )

           await message.channel.send(embed=embed)
           return

       # ================= GHOST LOOKUP =================
       ghost_input = args[0][1:]

       if ghost_input in GHOSTS:
           ghost_name = ghost_input
       else:
           matches = difflib.get_close_matches(ghost_input, GHOSTS.keys(), n=1, cutoff=0.5)
           if not matches:
               return
           ghost_name = matches[0]

       ghost = GHOSTS[ghost_name]

       embed = discord.Embed(
           title=f"👻 {ghost_name.capitalize()}",
           color=0x9b59b6
       )

       embed.add_field(
           name="🧪 Evidence",
           value="\n".join(f"• {e}" for e in ghost["evidence"]),
           inline=False
       )

       await message.channel.send(embed=embed)


async def setup(bot):
   await bot.add_cog(Phasmophobia(bot))