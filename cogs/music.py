import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import yt_dlp
import asyncio
import time
import random

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# ---------------- BUTTON UI ----------------
class MusicView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
        await interaction.response.defer()

    @discord.ui.button(label="⏸", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
        await interaction.response.defer()

    @discord.ui.button(label="🔁", style=discord.ButtonStyle.blurple)
    async def loop(self, interaction: discord.Interaction, button: Button):
        self.cog.loop = not self.cog.loop
        await interaction.response.send_message(f"Loop: {self.cog.loop}", ephemeral=True)

    @discord.ui.button(label="🔀", style=discord.ButtonStyle.blurple)
    async def shuffle(self, interaction: discord.Interaction, button: Button):
        random.shuffle(self.cog.queue)
        await interaction.response.send_message("Queue shuffled", ephemeral=True)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: Button):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
        await interaction.response.defer()

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            self.cog.queue.clear()
            self.cog.vc = None
        await interaction.response.defer()


# ---------------- COG ----------------
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.vc = None
        self.current = None
        self.start_time = 0
        self.volume = 0.5
        self.loop = False
        self.message = None

    # ---------------- SEARCH ----------------
    def search(self, query):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)

            if "entries" in info:
                info = info["entries"][0]

            return {
                "source": info["url"],
                "title": info["title"],
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "uploader": info.get("uploader"),
            }

    # ---------------- FORMAT ----------------
    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def progress_bar(self, position, duration, length=20):
        if duration == 0:
            return "LIVE"
        filled = int(length * position // duration)
        return "━" * filled + "🔘" + "━" * (length - filled)

    # ---------------- EMBED ----------------
    def create_embed(self, ctx):
        song = self.current
        pos = time.time() - self.start_time if song else 0

        embed = discord.Embed(
            title="Currently Playing:",
            description=f"**{song['title']}**",
            color=discord.Color.green()
        )

        embed.add_field(name="By", value=song.get("uploader"), inline=False)
        embed.add_field(name="Views", value=song.get("views"), inline=True)
        embed.add_field(name="Likes", value=song.get("likes"), inline=True)
        embed.add_field(name="Requested By", value=ctx.author.mention, inline=False)

        bar = self.progress_bar(pos, song["duration"])
        embed.add_field(
            name="Playback",
            value=f"{self.format_time(pos)} {bar} {self.format_time(song['duration'])}",
            inline=False
        )

        if self.queue:
            embed.add_field(name="Next", value=self.queue[0]["title"], inline=False)
        else:
            embed.add_field(name="Next", value="Nothing next in queue", inline=False)

        if song.get("thumbnail"):
            embed.set_thumbnail(url=song["thumbnail"])

        embed.set_footer(text="Music Bot")

        return embed

    # ---------------- LIVE UPDATE ----------------
    async def update_message(self, ctx):
        while self.current and self.vc and self.vc.is_playing():
            await asyncio.sleep(5)
            try:
                await self.message.edit(embed=self.create_embed(ctx), view=MusicView(self))
            except:
                break

    # ---------------- PLAY NEXT ----------------
    async def play_next(self, ctx):
        if self.loop and self.current:
            self.queue.insert(0, self.current)

        if not self.queue:
            self.current = None
            return

        song = self.queue.pop(0)
        self.current = song
        self.start_time = time.time()

        def after(e):
            asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song["source"], **FFMPEG_OPTIONS),
            volume=self.volume
        )

        self.vc.play(source, after=after)

        embed = self.create_embed(ctx)

        self.message = await ctx.send(embed=embed, view=MusicView(self))

        self.bot.loop.create_task(self.update_message(ctx))

    # ---------------- COMMANDS ----------------
    @commands.command()
    async def play(self, ctx, *, query):
        if not ctx.author.voice:
            return await ctx.send("Join VC first")

        if not self.vc:
            self.vc = await ctx.author.voice.channel.connect()

        song = self.search(query)
        self.queue.append(song)

        await ctx.send(f"Added: {song['title']}")

        if not self.vc.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            return await ctx.send("Queue empty")

        text = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(self.queue[:10])])
        embed = discord.Embed(title="Queue", description=text, color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if self.vc:
            self.vc.stop()

    @commands.command()
    async def pause(self, ctx):
        if self.vc:
            self.vc.pause()

    @commands.command()
    async def resume(self, ctx):
        if self.vc:
            self.vc.resume()

    @commands.command()
    async def stop(self, ctx):
        if self.vc:
            await self.vc.disconnect()
            self.queue.clear()
            self.vc = None

# ---------------- SETUP ----------------
async def setup(bot):
    await bot.add_cog(Music(bot))