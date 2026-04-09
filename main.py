import discord
import os
import asyncio
from discord.ext import commands

# -------------------------
# GET TOKEN
# -------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
   raise ValueError("❌ DISCORD_TOKEN is not set!")

print("TOKEN LOADED:", TOKEN)  # debug


# -------------------------
# INTENTS
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# -------------------------
# BOT SETUP
# -------------------------
bot = commands.Bot(
   command_prefix="!",
   intents=intents
)

bot.remove_command("help")


# -------------------------
# LOAD COGS
# -------------------------
async def load_cogs():
   for filename in os.listdir("./cogs"):
       if filename.endswith(".py"):
           try:
               await bot.load_extension(f"cogs.{filename[:-3]}")
               print(f"✅ Loaded {filename}")
           except Exception as e:
               print(f"❌ Failed to load {filename}: {e}")


# -------------------------
# READY EVENT
# -------------------------
@bot.event
async def on_ready():
   print(f"✅ Logged in as {bot.user}")

   try:
       synced = await bot.tree.sync()
       print(f"🌐 Synced {len(synced)} slash commands")
   except Exception as e:
       print(f"❌ Sync error: {e}")


# -------------------------
# ERROR HANDLING
# -------------------------
@bot.event
async def on_command_error(ctx, error):
   await ctx.send(f"❌ Error: {str(error)}")


# -------------------------
# START BOT (FIXED)
# -------------------------
async def main():
   await load_cogs()

   # Start bot in backround
   asyncio.create_task(bot.start(TOKEN))

   # KEEP PROGRAM ALIVE FOREVER
   while True:
       await asyncio.sleep(3600)


if __name__ == "__main__":
   asyncio.run(main())