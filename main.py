import asyncio
import itertools
import json
import logging
import os
import threading  # ✅ NEW

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from cogs.music import MusicControls
from web import run_web  # ✅ NEW

logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
   raise ValueError("DISCORD_TOKEN not found")


def ensure_file(file_path: str) -> None:
   if not os.path.exists(file_path):
       with open(file_path, "w", encoding="utf-8") as f:
           json.dump({}, f)


ensure_file("data.json")
ensure_file("tickets.json")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

statuses = itertools.cycle([
   discord.Activity(type=discord.ActivityType.listening, name="!help | !blackjack"),
])


@tasks.loop(seconds=10)
async def change_status():
   await bot.change_presence(activity=next(statuses))


async def load_cogs():
   if not os.path.isdir("./cogs"):
       print("No cogs folder found.")
       return

   for filename in os.listdir("./cogs"):
       if not filename.endswith(".py") or filename.startswith("_"):
           continue

       extension = f"cogs.{filename[:-3]}"
       try:
           await bot.load_extension(extension)
           print(f"Loaded {extension}")
       except Exception as e:
           print(f"Failed to load {extension}: {e}")


@bot.event
async def on_ready():
   print(f"Logged in as {bot.user}")

   print("MUSIC COMMANDS:")
   for command in bot.commands:
       if command.callback.__module__ == "cogs.music":
           print(f"{command.name} -> {command.callback.__module__}")

   # ✅ START DASHBOARD HERE
   if not hasattr(bot, "web_started"):
       threading.Thread(target=run_web, args=(bot,), daemon=True).start()
       bot.web_started = True
       print("🌐 Dashboard running on http://localhost:5000")

   if not change_status.is_running():
       change_status.start()

   if not hasattr(bot, "synced"):
       try:
           synced = await bot.tree.sync()
           print(f"Synced {len(synced)} commands")
           bot.synced = True
       except Exception as e:
           print(f"Sync error: {e}")


           
@bot.event
async def on_ready():
    bot.add_view(MusicControls(bot.get.cog("Music")))  # ✅ NEW
    print(f"Logged in as {bot.user}")


async def main():
   try:
       async with bot:
           await load_cogs()
           await bot.start(TOKEN)
   finally:
       for vc in bot.voice_clients:
           try:
               await vc.disconnect(force=True)
           except Exception:
               pass


if __name__ == "__main__":
   asyncio.run(main())