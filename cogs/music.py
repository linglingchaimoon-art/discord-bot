import discord
from discord.ext import commands
from discord.ui import View, Button
import yt_dlp
import asyncio
import time

YDL_OPTIONS = {
   "format": "bestaudio/best",
   "quiet": True,
   "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
   "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
   "options": "-vn"
}


# 🎮 BUTTON CONTROLS
class MusicControls(View):
   def __init__(self, cog):
       super().__init__(timeout=None)
       self.cog = cog

   @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
   async def resume(self, interaction: discord.Interaction, button: Button):
       print(f"[DEBUG] Resume button by {interaction.user}")
       if self.cog.vc:
           self.cog.vc.resume()
       await interaction.response.defer()

   @discord.ui.button(label="⏸", style=discord.ButtonStyle.gray)
   async def pause(self, interaction: discord.Interaction, button: Button):
       print(f"[DEBUG] Pause button by {interaction.user}")
       if self.cog.vc:
           self.cog.vc.pause()
       await interaction.response.defer()

   @discord.ui.button(label="🔁", style=discord.ButtonStyle.blurple)
   async def loop(self, interaction: discord.Interaction, button: Button):
       self.cog.loop = not self.cog.loop
       print(f"[DEBUG] Loop toggled → {self.cog.loop}")
       await interaction.response.send_message(f"🔁 Loop: {self.cog.loop}", ephemeral=True)

   @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
   async def skip(self, interaction: discord.Interaction, button: Button):
       print(f"[DEBUG] Skip button by {interaction.user}")
       if self.cog.vc:
           self.cog.vc.stop()
       await interaction.response.defer()

   @discord.ui.button(label="⏹", style=discord.ButtonStyle.red)
   async def stop(self, interaction: discord.Interaction, button: Button):
       print(f"[DEBUG] Stop button by {interaction.user}")
       if self.cog.vc:
           self.cog.queue.clear()
           self.cog.vc.stop()
       await interaction.response.defer()


class Music(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.queue = []
       self.is_playing = False
       self.vc = None
       self.current = None
       self.loop = False
       self.start_time = None

   # ---------------- SEARCH ----------------
   def search_yt(self, query):
       print(f"[DEBUG] Searching YouTube: {query}")

       try:
           ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
           info = ydl.extract_info(query, download=False)

           if "entries" in info:
               info = info["entries"][0]

           return {
               "source": info["url"],
               "title": info["title"],
               "duration": info.get("duration", 0),
               "views": info.get("view_count", 0),
               "likes": info.get("like_count", 0),
               "uploader": info.get("uploader", "Unknown"),
               "thumbnail": info.get("thumbnail"),
               "upload_date": info.get("upload_date", "Unknown")
           }

       except Exception as e:
           print(f"[ERROR] search_yt failed: {e}")
           return None

   # ---------------- JOIN ----------------
   async def join(self, ctx):
       print(f"[DEBUG] Join attempt by {ctx.author}")

       if not ctx.author.voice:
           await ctx.send("❌ Join a VC first")
           return False

       channel = ctx.author.voice.channel

       if not self.vc or not self.vc.is_connected():
           self.vc = await channel.connect()

       return True

   # ---------------- PROGRESS BAR ----------------
   def progress_bar(self):
       if not self.start_time or not self.current:
           return "▶️ 00:00 ───────── 00:00"

       elapsed = int(time.time() - self.start_time)
       duration = self.current["duration"]

       if duration == 0:
           return "Live"

       progress = int((elapsed / duration) * 20)
       bar = "─" * progress + "●" + "─" * (20 - progress)

       return f"{self.format_time(elapsed)} {bar} {self.format_time(duration)}"

   def format_time(self, seconds):
       return time.strftime("%M:%S", time.gmtime(seconds))

   # ---------------- EMBED ----------------
   def create_embed(self, ctx):
       song = self.current

       embed = discord.Embed(
           title="Currently Playing:",
           description=f"**{song['title']}**",
           color=0x1DB954
       )

       embed.add_field(name="By", value=song["uploader"], inline=False)
       embed.add_field(name="Views", value=f"{song['views']:,}", inline=True)
       embed.add_field(name="Likes", value=f"{song['likes']:,}", inline=True)
       embed.add_field(name="Requested By", value=ctx.author.mention, inline=False)
       embed.add_field(name="Playback", value=self.progress_bar(), inline=False)

       if len(self.queue) == 0:
           embed.add_field(name="Next", value="Nothing next in queue", inline=False)
       else:
           embed.add_field(name="Next", value=self.queue[0]["title"], inline=False)

       embed.set_thumbnail(url=song["thumbnail"])
       return embed

   # ---------------- PLAY NEXT ----------------
   async def play_next(self, ctx):
       print("[DEBUG] play_next triggered")

       if len(self.queue) == 0:
           self.is_playing = False
           print("[DEBUG] Queue empty")
           return

       if not self.vc:
           print("[ERROR] No voice client")
           return

       if self.loop and self.current:
           song = self.current
       else:
           song = self.queue.pop(0)

       self.current = song
       self.start_time = time.time()

       def after(error):
           if error:
               print(f"[ERROR] Player error: {error}")

           asyncio.run_coroutine_threadsafe(
               self.play_next(ctx), self.bot.loop
           )

       source = discord.PCMVolumeTransformer(
           discord.FFmpegPCMAudio(song["source"], **FFMPEG_OPTIONS),
           volume=0.5
       )

       self.vc.play(source, after=after)

       embed = self.create_embed(ctx)
       view = MusicControls(self)

       print("[DEBUG] Sending player UI")

       try:
           await ctx.send(embed=embed, view=view)
       except Exception as e:
           print(f"[ERROR] Failed to send player UI: {e}")

   # ---------------- PLAY ----------------
   @commands.command()
   async def play(self, ctx, *, query):
       print(f"[DEBUG] Play command → {query}")

       if not await self.join(ctx):
           return

       await ctx.send("🔍 Searching...")

       song = self.search_yt(query)

       if not song:
           await ctx.send("❌ Failed to find song")
           return

       self.queue.append(song)
       await ctx.send(f"✅ Added: {song['title']}")

       if not self.is_playing:
           self.is_playing = True
           await self.play_next(ctx)

   # ---------------- PRANDOM ----------------
   @commands.command()
   async def prandom(self, ctx, *, genre):
       print(f"[DEBUG] prandom → {genre}")

       if not await self.join(ctx):
           return

       await ctx.send(f"🎶 Loading **{genre}** playlist...")

       try:
           ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
           info = ydl.extract_info(f"ytsearch20:{genre} music", download=False)

           if "entries" not in info:
               await ctx.send("❌ No songs found")
               return

           added = 0

           for entry in info["entries"]:
               if not entry:
                   continue

               song = {
                   "source": entry["url"],
                   "title": entry["title"],
                   "duration": entry.get("duration", 0),
                   "views": entry.get("view_count", 0),
                   "likes": entry.get("like_count", 0),
                   "uploader": entry.get("uploader", "Unknown"),
                   "thumbnail": entry.get("thumbnail"),
                   "upload_date": entry.get("upload_date", "Unknown")
               }

               self.queue.append(song)
               added += 1

           await ctx.send(f"✅ Queued {added} songs")

           if not self.is_playing:
               self.is_playing = True
               await self.play_next(ctx)

       except Exception as e:
           print(f"[ERROR] prandom failed: {e}")
           await ctx.send("❌ Failed to load playlist")


# ---------------- SETUP ----------------
async def setup(bot):
   await bot.add_cog(Music(bot))