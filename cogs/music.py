
import discord
from discord.ext import commands, tasks
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

    # 🔄 RESET
    def reset(self):
        print("♻️ RESET BOT STATE")
        self.queue.clear()
        self.current = None
        self.is_playing = False
        self.loop = False
        self.start_time = None
        self.skip_votes.clear()

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
            print("✅ Connected to VC")

        return True

    # 🎧 AUTO LEAVE
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.vc or not self.vc.channel:
            return

        humans = [m for m in self.vc.channel.members if not m.bot]

        if len(humans) == 0:
            print("👋 VC empty → leaving")
            await self.vc.disconnect()
            self.vc = None
            self.reset()

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

    # 🎧 PRESENCE
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
            if error:
                print("❌ PLAYER ERROR:", error)
            asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop
            )

        self.vc.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(song["source"], **FFMPEG_OPTIONS)
            ),
            after=after
        )

        print("🎶 Playing:", song["title"])

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
        print("⏸ PAUSE")
        if self.vc:
            self.vc.pause()
            await ctx.send("⏸ Paused", delete_after=5)

    # ▶ RESUME
    @commands.command()
    async def resume(self, ctx):
        print("▶ RESUME")
        if self.vc:
            self.vc.resume()
            await ctx.send("▶ Resumed", delete_after=5)

    # ⏭ SKIP
    @commands.command()
    async def skip(self, ctx):
        print("⏭ SKIP")
        if self.vc:
            self.vc.stop()
            await ctx.send("⏭ Skipped", delete_after=5)

    # 👥 SKIP VOTE
    @commands.command()
    async def skipvote(self, ctx):
        print("🗳 SKIPVOTE")

        if not ctx.author.voice or not self.vc:
            return await ctx.send("❌ Join VC")

        if ctx.author.voice.channel != self.vc.channel:
            return await ctx.send("❌ Not same VC")

        members = [m for m in self.vc.channel.members if not m.bot]
        required = max(1, len(members) // 2)

        self.skip_votes.add(ctx.author.id)

        print(f"Votes: {len(self.skip_votes)}/{required}")

        if len(self.skip_votes) >= required:
            print("✅ Vote passed")
            self.skip_votes.clear()
            self.vc.stop()
            return await ctx.send("⏭ Vote passed!")

        await ctx.send(f"🗳 {len(self.skip_votes)}/{required} votes")

    # 🧹 CLEAR
    @commands.command()
    async def clear(self, ctx):
        print("🧹 CLEAR")

        if not self.vc:
            return await ctx.send("❌ Not connected", delete_after=5)

        if self.vc.is_playing() or self.vc.is_paused():
            self.vc.stop()

        self.reset()

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!Listening to !help",
                name="Come and play !blackjack🃏",
                name="Party with !prandom Rap🎶",
            )
        )

        await ctx.send("🧹 Queue cleared", delete_after=5)

    # ⏹ STOP
    @commands.command()
    async def stop(self, ctx):
        print("⏹ STOP")
        if self.vc:
            self.queue.clear()
            self.vc.stop()
            self.current = None
            await ctx.send("⏹ Stopped")

    # 👋 LEAVE
    @commands.command()
    async def leave(self, ctx):
        print("👋 LEAVE")

        if self.vc:
            await self.vc.disconnect()

        self.vc = None
        self.reset()

        await ctx.send("👋 Left and reset", delete_after=5)


async def setup(bot):
    await bot.add_cog(Music(bot))