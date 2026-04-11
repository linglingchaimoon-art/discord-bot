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
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


# 🎮 BUTTONS
class MusicControls(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="▶", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: Button):
        print("▶ BUTTON")
        if self.cog.vc:
            self.cog.vc.resume()
        await interaction.response.defer()

    @discord.ui.button(label="⏸", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: Button):
        print("⏸ BUTTON")
        if self.cog.vc:
            self.cog.vc.pause()
        await interaction.response.defer()

    @discord.ui.button(label="🔁", style=discord.ButtonStyle.blurple)
    async def loop(self, interaction: discord.Interaction, button: Button):
        self.cog.loop = not self.cog.loop
        print("🔁 LOOP:", self.cog.loop)
        await interaction.response.send_message(f"Loop: {self.cog.loop}", ephemeral=True)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: Button):
        print("⏭ BUTTON")
        if self.cog.vc:
            self.cog.vc.stop()
        await interaction.response.defer()

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: Button):
        print("⏹ BUTTON")
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
        self.skip_votes = set()

        print("🎵 Music cog loaded")

        self.update_presence_loop.start()
    # 🔍 SEARCH
    def search_yt(self, query):
        print("🔍 Searching:", query)
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
        }

    # 📻 PLAYLIST
    def search_playlist(self, query, limit=10):
        print("📻 Playlist:", query)
        ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
        info = ydl.extract_info(f"{query} playlist", download=False)

        songs = []
        if "entries" in info:
            for e in info["entries"][:limit]:
                if e:
                    songs.append({
                        "source": e["url"],
                        "title": e["title"],
                        "duration": e.get("duration", 0),
                        "views": e.get("view_count", 0),
                        "likes": e.get("like_count", 0),
                        "uploader": e.get("uploader", "Unknown"),
                        "thumbnail": e.get("thumbnail"),
                    })
        return songs

    # 🔌 JOIN
    async def join(self, ctx):
        print("🔌 JOIN")
        if not ctx.author.voice:
            await ctx.send("❌ Join VC first")
            return False

        if not self.vc or not self.vc.is_connected():
            self.vc = await ctx.author.voice.channel.connect()

        return True

    # ⏱ TIME
    def format_time(self, s):
        return time.strftime("%M:%S", time.gmtime(s))

    def progress_bar(self):
        if not self.current or not self.start_time:
            return "00:00 ───────── 00:00"

        elapsed = int(time.time() - self.start_time)
        duration = self.current["duration"]

        progress = int((elapsed / duration) * 20) if duration else 0
        bar = "─" * progress + "●" + "─" * (20 - progress)

        return f"{self.format_time(elapsed)} {bar} {self.format_time(duration)}"

    # 🎵 EMBED
    def create_embed(self, ctx):
        embed = discord.Embed(
            title="Currently Playing",
            description=f"**{self.current['title']}**",
            color=0x1DB954
        )

        embed.add_field(name="By", value=self.current["uploader"], inline=False)
        embed.add_field(name="Views", value=f"{self.current['views']:,}", inline=True)
        embed.add_field(name="Likes", value=f"{self.current['likes']:,}", inline=True)
        embed.add_field(name="Requested", value=ctx.author.mention, inline=False)
        embed.add_field(name="Playback", value=self.progress_bar(), inline=False)

        next_song = self.queue[0]["title"] if self.queue else "Nothing next"
        embed.add_field(name="Next", value=next_song, inline=False)

        embed.set_thumbnail(url=self.current["thumbnail"])
        return embed

    # 🎧 PRESENCE (music)
    @tasks.loop(seconds=5)
    async def update_presence_loop(self):
        if not self.current:
            return

        elapsed = int(time.time() - self.start_time)
        duration = self.current["duration"]

        text = f"{self.format_time(elapsed)}/{self.format_time(duration)}"

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.current['title'][:60]} | {text}"
            )
        )

    # 😴 IDLE STATUS
    @tasks.loop(seconds=10)
    async def idle_status(self):
        if self.current:
            return

        statuses = [
            "!help | music",
            "!prandom phonk",
            "Serving music 🎵"
        ]

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=random.choice(statuses)
            )
        )

    # ▶ PLAY NEXT
    async def play_next(self, ctx):
        print("⏭ PLAY NEXT")

        if not self.queue and not self.loop:
            self.is_playing = False
            self.current = None
            return

        self.skip_votes.clear()

        song = self.current if self.loop else self.queue.pop(0)
        self.current = song
        self.start_time = time.time()

        def after(error):
            asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop
            )

        self.vc.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(song["source"], **FFMPEG_OPTIONS)
            ),
            after=after
        )

        await ctx.send(embed=self.create_embed(ctx), view=MusicControls(self))

    # ▶ PLAY
    @commands.command()
    async def play(self, ctx, *, query):
        print("🎤 !play")

        if not await self.join(ctx):
            return

        msg = await ctx.send("🔍 Searching...")
        await asyncio.sleep(3)
        await msg.delete()

        song = self.search_yt(query)
        self.queue.append(song)

        await ctx.send(f"✅ Added: {song['title']}", delete_after=5)

        if not self.is_playing:
            self.is_playing = True
            await self.play_next(ctx)

    # 📻 RANDOM
    @commands.command()
    async def prandom(self, ctx, *, genre):
        print("📻 !prandom", genre)

        if not await self.join(ctx):
            return

        msg = await ctx.send(f"🎧 Loading {genre}...")
        await asyncio.sleep(3)
        await msg.delete()

        songs = self.search_playlist(genre, 10)
        self.queue.extend(songs)

        if not self.is_playing:
            self.is_playing = True
            await self.play_next(ctx)

    # ⏸ PAUSE
    @commands.command()
    async def pause(self, ctx):
        if self.vc:
            self.vc.pause()
            await ctx.send("⏸ Paused", delete_after=5)

    # ▶ RESUME
    @commands.command()
    async def resume(self, ctx):
        if self.vc:
            self.vc.resume()
            await ctx.send("▶ Resumed", delete_after=5)

    # ⏭ SKIP
    @commands.command()
    async def skip(self, ctx):
        if self.vc:
            self.vc.stop()
            await ctx.send("⏭ Skipped", delete_after=5)

    # 👥 SKIP VOTE
    @commands.command()
    async def skipvote(self, ctx):
        if not ctx.author.voice or not self.vc:
            return await ctx.send("❌ Join VC")

        members = [m for m in ctx.author.voice.channel.members if not m.bot]
        required = max(1, len(members) // 2)

        self.skip_votes.add(ctx.author.id)

        if len(self.skip_votes) >= required:
            self.skip_votes.clear()
            self.vc.stop()
            return await ctx.send("⏭ Vote passed!")

        await ctx.send(f"🗳 {len(self.skip_votes)}/{required} votes")

    # ⏹ STOP
    @commands.command()
    async def stop(self, ctx):
        if self.vc:
            self.queue.clear()
            self.vc.stop()
            self.current = None
            await ctx.send("⏹ Stopped")

    # 👋 LEAVE
    @commands.command()
    async def leave(self, ctx):
        if self.vc:
            await self.vc.disconnect()
            self.vc = None
            self.current = None 
            await ctx.send("👋 Left")


async def setup(bot):
    await bot.add_cog(Music(bot))