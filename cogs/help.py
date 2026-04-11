import discord
from discord.ext import commands
from discord import app_commands

OWNER_ID = 1398304429085556746


# -------------------------
# DROPDOWN SELECT
# -------------------------
class HelpSelect(discord.ui.Select):
    def __init__(self, pages):
        self.pages = pages

        options = [
            discord.SelectOption(label="Home", emoji="🏠", value="Home"),
            discord.SelectOption(label="Moderation", emoji="🔨", value="Moderation"),
            discord.SelectOption(label="Games", emoji="🎮", value="Games"),
            discord.SelectOption(label="Music", emoji="🎵", value="Music"),
        ]

        super().__init__(placeholder="Select a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        print(f"[DEBUG] Dropdown used by {interaction.user} → {self.values[0]}")

        await interaction.response.edit_message(
            embed=self.pages[self.values[0]],
            view=self.view
        )


# -------------------------
# VIEW
# -------------------------
class HelpView(discord.ui.View):
    def __init__(self, pages, author):
        super().__init__(timeout=120)
        self.pages = pages
        self.author = author

        self.add_item(HelpSelect(pages))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "❌ This menu isn't for you.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] Closed by {interaction.user}")
        await interaction.response.defer()
        await interaction.message.delete()


# -------------------------
# COG
# -------------------------
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show the help menu")
    async def help_slash(self, interaction: discord.Interaction):
        print(f"[DEBUG] /help used by {interaction.user}")

        prefix = "!"  # change if needed

        # EMBEDS
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

        moderation = discord.Embed(
            title="🔨 Moderation Commands",
            colour=discord.Colour.red()
        )
        moderation.add_field(name="🧹 Purge", value=f"{prefix}purge <amount>", inline=False)
        moderation.add_field(name="🔇 Mute", value=f"{prefix}mute <member>", inline=False)
        moderation.add_field(name="🔊 Unmute", value=f"{prefix}unmute <member>", inline=False)

        games = discord.Embed(
            title="🎮 Games Commands",
            colour=discord.Colour.green()
        )
        games.add_field(name="🃏 Blackjack", value=f"{prefix}blackjack <amount>", inline=False)

        if interaction.user.id == OWNER_ID:
            games.add_field(
                name="👑 Owner",
                value=f"{prefix}addbalance @user",
                inline=False
            )

        # 🎵 MUSIC (UPDATED)
        music = discord.Embed(
            title="🎵 Music Commands",
            description="Full music control system",
            colour=0x1DB954
        )


        # ▶ PLAYBACK
        music.add_field(
            name="▶ Playback",
            value=(
                f"{prefix}play <song>\n"
                f"{prefix}pause\n"
                f"{prefix}resume\n"
                f"{prefix}skip\n"
                f"{prefix}stop\n"
                f"{prefix}leave"
            ),
            inline=False
        )

        # 📜 QUEUE
        music.add_field(
            name="📜 Queue",
            value=(
                f"{prefix}queue\n"
                f"{prefix}clear"
            ),
            inline=False
        )

        # 🎧 NOW PLAYING
        music.add_field(
            name="🎧 Info",
            value=(
                f"{prefix}nowplaying\n"
                f"{prefix}np"
            ),
            inline=False
        )

        # 🔊 AUDIO
        music.add_field(
            name="🔊 Audio",
            value=f"{prefix}volume <0-100>",
            inline=False
        )
        # 📻 RADIO MODE
        music.add_field(
            name="📻 Radio Mode",
            value=f"{prefix}radio <genre>",
            inline=False
        )
        

        # 🎮 CONTROLS
        music.add_field(
            name="🎮 Buttons",
            value="Use the buttons on the player for quick control",
            inline=False
        )

        pages = {
            "Home": home,
            "Moderation": moderation,
            "Games": games,
            "Music": music
        }

        view = HelpView(pages, interaction.user)

        # -------------------------
        # 1. EPHEMERAL RESPONSE (SERVER)
        # -------------------------
        await interaction.response.send_message(
            "📬 Check your DMs! (also shown below)",
            embed=home,
            view=view,
            ephemeral=True
        )

        # -------------------------
        # 2. DM USER
        # -------------------------
        try:
            dm = await interaction.user.create_dm()
            await dm.send(embed=home, view=HelpView(pages, interaction.user))

            print("[DEBUG] DM sent successfully")

        except Exception as e:
            print(f"[ERROR] Could not DM user: {e}")

            await interaction.followup.send(
                "❌ I couldn't DM you. Please enable DMs.",
                ephemeral=True
            )


# -------------------------
# SETUP
# -------------------------
async def setup(bot):
    await bot.add_cog(Help(bot))