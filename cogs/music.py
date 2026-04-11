import asyncio
import discord
from discord.ext import commands
import yt_dlp

# =====================
# CONFIG
# =====================

YTDL_OPTIONS = {
   "format": "bestaudio/best",
   "noplaylist": True,
   "quiet": True,
   "default_search": "ytsearch1",
}

FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"


class GuildPlayer:
   def __init__(self):
       self.queue = asyncio.Queue()
       self.task = None


class Music(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.players = {}

   def get_player(self, guild_id):
       if guild_id not in self.players:
           self.players[guild_id] = GuildPlayer()
       return self.players[guild_id]

   # =====================
   # YOUTUBE
   # =====================

   async def extract_track(self, query):
       loop = asyncio.get_running_loop()

       def run():
           with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
               return ytdl.extract_info(query, download=False)

       data = await loop.run_in_executor(None, run)

       if not data:
           return None

       if "entries" in data:
           data = data["entries"][0]

       return {
           "title": data.get("title"),
           "url": data.get("url"),
           "duration": data.get("duration", 0),
           "thumbnail": data.get("thumbnail"),
           "webpage_url": data.get("webpage_url"),
       }

   # =====================
   # PLAYER LOOP
   # =====================

   async def player_loop(self, guild, channel):
       print("PLAYER LOOP STARTED")

       player = self.get_player(guild.id)

       while True:
           track = await player.queue.get()
           print("Playing:", track["title"])

           # Wait until connected
           while True:
               vc = guild.voice_client
               if vc and vc.is_connected():
                   break
               await asyncio.sleep(1)

           try:
               source = await discord.FFmpegOpusAudio.from_probe(
                   track["url"],
                   method="fallback",
                   before_options=FFMPEG_BEFORE_OPTIONS,
                   options=FFMPEG_OPTIONS,
               )
           except Exception as e:
               print("FFmpeg error:", e)
               await channel.send(f"❌ FFmpeg error: {e}")
               continue

           done = asyncio.Event()

           def after_playing(err):
               if err:
                   print(f"[ERROR] {err}")

               # ✅ CLEANUP (IMPORTANT)
               if guild.voice_client and guild.voice_client.source:
                   guild.voice_client.source.cleanup()

               self.bot.loop.call_soon_threadsafe(done.set)

           vc.play(source, after=after_playing)

           # 🎧 EMBED
           embed = discord.Embed(
               title="🎶 Now Playing",
               description=f"[{track['title']}]({track['webpage_url']})",
               color=discord.Color.green()
           )

           if track.get("duration"):
               m, s = divmod(track["duration"], 60)
               embed.add_field(name="⏱ Duration", value=f"{m}:{s:02d}")

           if track.get("thumbnail"):
               embed.set_thumbnail(url=track["thumbnail"])

           await channel.send(embed=embed)

           await done.wait()
           await asyncio.sleep(0.5)

   # =====================
   # VOICE
   # =====================

   async def ensure_voice(self, ctx):
       vc = ctx.guild.voice_client

       if vc and vc.is_connected():
           return vc

       if not ctx.author.voice:
           await ctx.send("❌ Join a voice channel first.")
           return None

       try:
           return await ctx.author.voice.channel.connect(timeout=10, reconnect=True)
       except Exception as e:
           await ctx.send(f"❌ Voice connect failed: {e}")
           return None

   # =====================
   # COMMANDS
   # =====================

   @commands.command()
   async def join(self, ctx):
       if not ctx.author.voice:
           await ctx.send("❌ You must be in a voice channel.")
           return

       try:
           if ctx.guild.voice_client:
               await ctx.guild.voice_client.disconnect()

           vc = await ctx.author.voice.channel.connect(timeout=10, reconnect=True)

           if not vc or not vc.is_connected():
               await ctx.send("❌ Failed to connect.")
               return

           await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**")

       except Exception as e:
           await ctx.send(f"❌ Join error: {e}")

   @commands.command()
   async def play(self, ctx, *, query):
       vc = await self.ensure_voice(ctx)
       if not vc:
           return

       await ctx.send("🔎 Searching...")

       track = await self.extract_track(query)

       if not track:
           await ctx.send("❌ No results.")
           return

       player = self.get_player(ctx.guild.id)
       await player.queue.put(track)

       embed = discord.Embed(
           title="➕ Added to Queue",
           description=f"**{track['title']}**",
           color=discord.Color.blue()
       )

       await ctx.send(embed=embed)

       if player.task is None or player.task.done():
           player.task = asyncio.create_task(
               self.player_loop(ctx.guild, ctx.channel)
           )

   @commands.command()
   async def skip(self, ctx):
       vc = ctx.guild.voice_client
       if vc and vc.is_playing():
           vc.stop()
           await ctx.send("⏭️ Skipped.")
       else:
           await ctx.send("Nothing playing.")

   @commands.command()
   async def stop(self, ctx):
       player = self.get_player(ctx.guild.id)

       while not player.queue.empty():
           player.queue.get_nowait()

       vc = ctx.guild.voice_client
       if vc:
           if vc.source:
               vc.source.cleanup()
           vc.stop()

       await ctx.send("⏹️ Stopped.")

   @commands.command()
   async def leave(self, ctx):
       player = self.get_player(ctx.guild.id)

       while not player.queue.empty():
           player.queue.get_nowait()

       vc = ctx.guild.voice_client
       if vc:
           if vc.source:
               vc.source.cleanup()
           await vc.disconnect()

       await ctx.send("👋 Disconnected.")

   @commands.command(name="queue")
   async def show_queue(self, ctx):
       player = self.get_player(ctx.guild.id)
       items = list(player.queue._queue)

       if not items:
           await ctx.send("📭 Queue empty.")
           return

       msg = "\n".join(f"{i+1}. {t['title']}" for i, t in enumerate(items[:10]))
       await ctx.send(f"📜 Queue:\n{msg}")

   @commands.command()
   async def pause(self, ctx):
       vc = ctx.guild.voice_client
       if vc and vc.is_playing():
           vc.pause()
           await ctx.send("⏸️ Paused.")
       else:
           await ctx.send("Nothing playing.")

   @commands.command()
   async def resume(self, ctx):
       vc = ctx.guild.voice_client
       if vc and vc.is_paused():
           vc.resume()
           await ctx.send("▶️ Resumed.")
       else:
           await ctx.send("Nothing paused.")


async def setup(bot):
   await bot.add_cog(Music(bot))