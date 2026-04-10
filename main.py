import discord
import os
import asyncio
import json
import logging
import itertools
from discord.ext import commands, tasks
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
   raise ValueError("❌ DISCORD_TOKEN not found")

# -------------------------
# FILE CHECK
# -------------------------
def ensure_file(file):
   if not os.path.exists(file):
       with open(file, "w") as f:
           json.dump({}, f)

ensure_file("data.json")
ensure_file("tickets.json")

# -------------------------
# INTENTS
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# -------------------------
# BOT SETUP
# -------------------------
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# -------------------------
# STATUS SYSTEM 🔥
# -------------------------
statuses = itertools.cycle([
   discord.Activity(type=discord.ActivityType.listening, name="!help | !blackjack 🎰"),
])

@tasks.loop(seconds=10)
async def change_status():
   await bot.change_presence(activity=next(statuses))

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

   # 🔥 START STATUS ROTATION
   if not change_status.is_running():
       change_status.start()

   if not hasattr(bot, "synced"):
       try:
           synced = await bot.tree.sync()
           print(f"🌐 Synced {len(synced)} commands")
           bot.synced = True
       except Exception as e:
           print(f"❌ Sync error: {e}")

# -------------------------
# ERROR HANDLING
# -------------------------
@bot.event
async def on_command_error(ctx, error):
   if isinstance(error, commands.CommandNotFound):
       return
   await ctx.send(f"❌ Error: {error}")

# -------------------------
# MAIN
# -------------------------
async def main():
   async with bot:
       await load_cogs()
       await bot.start(TOKEN)

if __name__ == "__main__":
   asyncio.run(main())