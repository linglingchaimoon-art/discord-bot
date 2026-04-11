import discord
from discord.ext import commands

OWNER_ID = 1398304429085556746  # your ID


# -------------------------
# DROPDOWN SELECT
# -------------------------
class HelpSelect(discord.ui.Select):
    def __init__(self, pages):
        options = [
            discord.SelectOption(label="Home", emoji="🏠", value="Home"),
            discord.SelectOption(label="Moderation", emoji="🔨", value="Moderation"),
            discord.SelectOption(label="Games", emoji="🎮", value="Games"),
            discord.SelectOption(label="Music", emoji="🎵", value="Music"),  # ✅ NEW
        ]

        super().__init__(placeholder="Select a category...", options=options)
        self.pages = pages

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.pages[self.values[0]],
            view=self.view
        )


# -------------------------
# VIEW
# -------------------------
class HelpView(discord.ui.View):
    def __init__(self, pages, author):
        super().__init__(timeout=60)
        self.pages = pages
        self.author = author
        self.add_item(HelpSelect(pages))

    async def interaction_check(self, interaction):
        return interaction.user == self.author

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        await interaction.message.delete()


# -------------------------
# COG
# -------------------------
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        prefix = ctx.prefix

        # -------------------------
        # HOME
        # -------------------------
        home = discord.Embed(
            title="📖 Help Menu",
            description="Select a category below",
            colour=discord.Colour.blurple()
        )

        home.add_field(
            name="Categories",
            value="🏠 Home\n🔨 Moderation\n🎮 Games\n🎵 Music",
            inline=False
        )

        # -------------------------
        # MODERATION
        # -------------------------
        moderation = discord.Embed(
            title="🔨 Moderation Commands",
            colour=discord.Colour.red()
        )

        moderation.add_field(name="🧹 Purge", value=f"{prefix}purge <amount>", inline=False)
        moderation.add_field(name="🔇 Mute", value=f"{prefix}mute <member>", inline=False)
        moderation.add_field(name="🔊 Unmute", value=f"{prefix}unmute <member>", inline=False)
        moderation.add_field(name="⏳ TempMute", value=f"{prefix}tempmute <member> <time>", inline=False)
        moderation.add_field(name="👢 Kick", value=f"{prefix}kick <member>", inline=False)
        moderation.add_field(name="🔨 Ban", value=f"{prefix}ban <member>", inline=False)
        moderation.add_field(name="♻️ Unban", value=f"{prefix}unban <member>", inline=False)
        moderation.add_field(name="⏱ TempBan", value=f"{prefix}tempban <member> <time>", inline=False)

        # -------------------------
        # GAMES
        # -------------------------
        games = discord.Embed(
            title="🎮 Games Commands",
            description="Casino & fun commands",
            colour=discord.Colour.green()
        )

        games.add_field(
            name="🃏 Blackjack",
            value=f"{prefix}blackjack <amount>\n{prefix}blackjack all",
            inline=False
        )

        games.add_field(
            name="💰 Economy",
            value=f"{prefix}balance\n{prefix}balance @user\n{prefix}daily",
            inline=False
        )

        games.add_field(
            name="💸 Transfer",
            value=f"{prefix}pay @user <amount>",
            inline=False
        )

        games.add_field(
            name="🕵 Steal",
            value=f"{prefix}steal @user (every 5h)",
            inline=False
        )

        # 👑 OWNER COMMANDS
        if ctx.author.id == OWNER_ID:
            games.add_field(
                name="👑 Owner Commands",
                value=f"{prefix}addbalance @user <amount>\n{prefix}removebalance @user <amount>",
                inline=False
            )

        # -------------------------
        # 🎵 MUSIC (FINAL)
        # -------------------------
        music = discord.Embed(
            title="🎵 Music Commands",
            description="Control the music bot",
            colour=0x1DB954
        )

        music.add_field(
            name="▶ Playback",
            value=f"""
{prefix}play <song>
{prefix}pause
{prefix}resume
{prefix}skip
{prefix}stop
{prefix}leave
""",
            inline=False
        )

        music.add_field(
            name="👥 Voting",
            value=f"""
{prefix}skipvote
Vote to skip the current song
""",
            inline=False
        )

        music.add_field(
            name="📻 Radio Mode",
            value=f"""
{prefix}prandom <genre>
Play a playlist based on genre
""",
            inline=False
        )

        music.add_field(
            name="🔥 Popular Genres",
            value="""
phonk • drill • lofi • edm
techno • house • trap
gym • sad • anime • 90s
""",
            inline=False
        )

        music.add_field(
            name="💡 Pro Tips",
            value="""
Use better searches:
• aggressive gym rap
• dark phonk drift
• chill lofi beats
""",
            inline=False
        )

        # -------------------------
        # PAGES
        # -------------------------
        pages = {
            "Home": home,
            "Moderation": moderation,
            "Games": games,
            "Music": music
        }

        view = HelpView(pages, ctx.author)

        # -------------------------
        # SEND
        # -------------------------
        try:
            await ctx.author.send(embed=home, view=view)
            await ctx.reply("📩 Check your DMs!", delete_after=5)
        except:
            await ctx.reply("❌ I can't DM you. Enable DMs!", delete_after=5)


# -------------------------
# SETUP
# -------------------------
async def setup(bot):
    await bot.add_cog(Help(bot))