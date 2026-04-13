import asyncio
import itertools
import json
import logging
import os

import discord
from discord.ext.commands import CommandNotFound
from discord.ext import commands, tasks
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
GUILD_ID = 1442896370502733898  # 🔥 PUT YOUR SERVER ID

# ---------------- LOGGING ----------------
logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO)

# ---------------- TOKEN ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# ---------------- STATUS ----------------
STATUS_LIST = [
   (discord.ActivityType.listening, "Listening to /help"),
   (discord.ActivityType.playing, "Playing !blackjack"),
   (discord.ActivityType.listening, "Partying with !join"),
]

@tasks.loop(minutes=5)
async def change_status():
   t, txt = next(change_status.cycle)
   await bot.change_presence(activity=discord.Activity(type=t, name=txt))

change_status.cycle = itertools.cycle(STATUS_LIST)

# ---------------- LOAD COGS ----------------
async def load_cogs():
   for file in os.listdir("./cogs"):
       if file.endswith(".py"):
           await bot.load_extension(f"cogs.{file[:-3]}")
           print(f"✅ Loaded {file}")

# ---------------- READY ----------------
@bot.event
async def on_ready():
   print(f"✅ Logged in as {bot.user}")

   if not change_status.is_running():
       change_status.start()

   # 🔥 FORCE CLEAN SYNC
   guild = discord.Object(id=GUILD_ID)

   bot.tree.clear_commands(guild=guild)
   bot.tree.copy_global_to(guild=guild)

   synced = await bot.tree.sync(guild=guild)
   print(f"🔥 Synced {len(synced)} commands")

# ---------------- ERROR ----------------
@bot.event
async def on_command_error(ctx, error):
   if isinstance(error, CommandNotFound):
       return
   print(error)

# ---------------- MAIN ----------------
async def main():
   async with bot:
       await load_cogs()
       await bot.start(TOKEN)

if __name__ == "__main__":
   asyncio.run(main())