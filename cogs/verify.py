import discord
from discord.ext import commands

VERIFY_ROLE_NAME = "HEAVEN"


# -------------------------
# VERIFY BUTTON
# -------------------------
class VerifyView(discord.ui.View):
   def __init__(self):
       super().__init__(timeout=None)

   @discord.ui.button(
       label="Verify",
       emoji="✅",
       style=discord.ButtonStyle.success,
       custom_id="verify_button"
   )
   async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

       role = discord.utils.get(interaction.guild.roles, name=VERIFY_ROLE_NAME)

       if role is None:
           return await interaction.response.send_message(
               "❌ Role not found.",
               ephemeral=True
           )

       if role in interaction.user.roles:
           return await interaction.response.send_message(
               "⚠️ You are already verified.",
               ephemeral=True
           )

       await interaction.user.add_roles(role)

       await interaction.response.send_message(
           "✅ You are now verified! Welcome to the server.",
           ephemeral=True
       )


# -------------------------
# COG
# -------------------------
class Verify(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.bot.add_view(VerifyView())

   @commands.command()
   @commands.has_permissions(administrator=True)
   async def setupverify(self, ctx):
       """Creates the rules GUI with verify button"""

       embed = discord.Embed(
           title="📜 Server Rules",
           description=(
               "**Welcome to the server!**\n\n"
               "We’re glad you’re here. Please read the rules below:\n\n"
               "➡️ **1. Respect everyone**\n"
               "Treat all members with respect, even if you disagree with their opinions. Harassment, hate speech, and discriminatory language will not be tolerated.\n\n"
               "➡️ **2. Keep it clean (PG-13)**\n"
               "Avoid sharing NSFW content and keep the language clean to ensure a safe and inclusive environment for everyone.\n\n"
               "➡️ **3. No spamming**\n"
               "Do not flood the chat with repetitive messages, emojis, or excessive use of caps lock. This can disrupt the flow of conversation and make it difficult for others to participate.\n\n"
               "➡️ **4. No self-promotion**\n"
               "Avoid promoting personal content or products without permission from the server owner or moderators. This includes advertising your own social media, YouTube channel, or Discord server.\n\n"
               "➡️ **5. No trolling or harassment**\n"
               "Do not engage in any behavior that is meant to provoke or harass others.\n\n"
               "➡️ **6. No sharing personal information**\n"
               "Do not share personal information about yourself or others, such as phone numbers, addresses, or passwords.\n\n"
               "➡️ **7. Follow Discord’s Community Guidelines**\n"
               "Stick to Discord’s Community Guidelines to ensure a respectful community. You can read them in full here: https://discord.com/guidelines\n\n"
               "━━━━━━━━━━━━━━━━━━\n"
               "✅ **Click the button below to verify and gain access**"
           ),
           colour=discord.Colour.blurple()
       )

       # Optional image/banner (replace with your own if you want)
       embed.set_image(
           url="https://i.pinimg.com/736x/a0/9a/4a/a09a4a73dbd67daa71c1b874146ee29d.jpg"  # you can replace this
       )

       embed.set_footer(text="Verification System")

       await ctx.send(
           content="@here",
           embed=embed,
           view=VerifyView()
       )


# -------------------------
# SETUP
# -------------------------
async def setup(bot):
   await bot.add_cog(Verify(bot))