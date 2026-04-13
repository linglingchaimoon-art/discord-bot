import discord
from discord.ext import commands
import difflib  # 🔥 used for smart suggestions

# 🔥 CHANGE THIS
ALLOWED_CHANNEL_ID = 1493062544863264869


# ================= GHOST DATABASE =================
GHOSTS = {
   "jhinn": {
       "description": "A territorial ghost that becomes faster when far away.",
       "evidence": ["EMF Level 5", "Freezing Temperatures", "Fingerprints"],
       "strength": "Moves faster when far away from players.",
       "weakness": "Turning off the breaker slows it down.",
       "identify": "Speed increases at distance, normal speed up close."
   },

   "revenant": {
       "description": "A slow but extremely fast hunter when it sees you.",
       "evidence": ["Ghost Writing", "Freezing Temperatures", "Ghost Orbs"],
       "strength": "Moves VERY fast when it has line of sight.",
       "weakness": "Very slow when not chasing.",
       "identify": "Huge speed change when it sees you."
   },
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

       ghost_name = message.content[1:].lower()

       # ===== EXACT MATCH =====
       if ghost_name in GHOSTS:
           ghost = GHOSTS[ghost_name]

           embed = discord.Embed(
               title=f"👻 {ghost_name.capitalize()}",
               description=ghost["description"],
               color=0x9b59b6
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

           embed.set_footer(text="Phasmophobia Guide")

           await message.channel.send(embed=embed)
           return

       # ===== SMART SUGGESTION =====
       matches = difflib.get_close_matches(ghost_name, GHOSTS.keys(), n=1, cutoff=0.6)

       if matches:
           suggestion = matches[0]

           await message.channel.send(
               f"❌ Ghost not found.\nDid you mean: **{suggestion.capitalize()}**?"
           )


async def setup(bot):
   await bot.add_cog(Phasmophobia(bot))