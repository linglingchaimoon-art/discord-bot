import discord
from discord.ext import commands
import yt_dlp
import asyncio

ytdl = yt_dlp.YoutubeDL({
   "format": "bestaudio/best",
   "quiet": True
})

ffmpeg_options = {
   "options": "-vn"
}

class Music(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.queue = {}

   def get_queue(self, guild):
       if guild.id not in self.queue:
           self.queue[guild.id] = []
       return self.queue[guild.id]

   async def search_yt(self, query):
       loop = asyncio.get_event_loop()
       data = await loop.run_in_executor(
           None,
           lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
       )
       return data["entries"][0]

   async def play_next(self, ctx):
       queue = self.get_queue(ctx.guild)

       if queue:
           song = queue.pop(0)
           await self.start_song(ctx, song)
       else:
           await ctx.send("📭 Queue finished")

   async def start_song(self, ctx, song):
       url = song["url"]

       source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)

       ctx.voice_client.play(
           source,
           after=lambda e: asyncio.run_coroutine_threadsafe(
               self.play_next(ctx), self.bot.loop
           )
       )

       embed = discord.Embed(
           title="🎵 Now Playing",
           description=f"**{song['title']}**",
           color=discord.Color.green()
       )
       embed.set_footer(text="Rythm-style music 🎧")

       await ctx.send(embed=embed)

   # =====================
   # COMMANDS
   # =====================

   @commands.command()
   async def join(self, ctx):
       if ctx.author.voice:
           await ctx.author.voice.channel.connect()
       else:
           await ctx.send("❌ Join a voice channel first")

   @commands.command()
   async def play(self, ctx, *, query):
       if not ctx.voice_client:
           await ctx.invoke(self.join)

       await ctx.send("🔎 Searching...")

       song = await self.search_yt(query)

       if ctx.voice_client.is_playing():
           queue = self.get_queue(ctx.guild)
           queue.append(song)
           await ctx.send(f"➕ Added to queue: **{song['title']}**")
       else:
           await self.start_song(ctx, song)

   @commands.command()
   async def skip(self, ctx):
       if ctx.voice_client:
           ctx.voice_client.stop()
           await ctx.send("⏭️ Skipped")

   @commands.command()
   async def pause(self, ctx):
       if ctx.voice_client:
           ctx.voice_client.pause()
           await ctx.send("⏸️ Paused")

   @commands.command()
   async def resume(self, ctx):
       if ctx.voice_client:
           ctx.voice_client.resume()
           await ctx.send("▶️ Resumed")

   @commands.command()
   async def stop(self, ctx):
       if ctx.voice_client:
           self.queue[ctx.guild.id] = []
           ctx.voice_client.stop()
           await ctx.send("⏹️ Stopped & cleared queue")

   @commands.command()
   async def queue(self, ctx):
       queue = self.get_queue(ctx.guild)

       if not queue:
           await ctx.send("📭 Queue empty")
       else:
           msg = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(queue[:10])])
           await ctx.send(f"📜 Queue:\n{msg}")

   @commands.command()
   async def leave(self, ctx):
       if ctx.voice_client:
           await ctx.voice_client.disconnect()

async def setup(bot):
   await bot.add_cog(Music(bot))