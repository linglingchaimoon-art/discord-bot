import asyncio
import itertools
import json
import logging
import os

import discord
from discord.ext.commands import CommandNotFound
from discord.ext import commands, tasks
from dotenv import load_dotenv

# ---------------- LOGGING ----------------
logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO)

# ---------------- LOAD TOKEN ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
   raise ValueError("❌ DISCORD_TOKEN not found in .env")

print("[DEBUG] Token loaded successfully")

# ---------------- FILE SAFETY ----------------
def ensure_file(file_path: str):
   if not os.path.exists(file_path):
       print(f"[DEBUG] Creating missing file: {file_path}")
       with open(file_path, "w", encoding="utf-8") as f:
           json.dump({}, f)

ensure_file("data.json")
ensure_file("tickets.json")

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

print("[DEBUG] Intents configured")

# ---------------- BOT SETUP ----------------
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

print("[DEBUG] Bot initialized")

# ---------------- STATUS ROTATION ----------------
STATUS_LIST = [
   (discord.ActivityType.listening, "/help"),
   (discord.ActivityType.listening, "!blackjack"),
   (discord.ActivityType.listening, "!join"),
]

@tasks.loop(minutes=5)
async def change_status():
   activity_type, text = next(change_status.status_cycle)

   activity = discord.Activity(
       type=activity_type,
       name=text
   )

   await bot.change_presence(activity=activity)

# 🔁 CREATE CYCLE
change_status.status_cycle = itertools.cycle(STATUS_LIST)

# ---------------- LOAD COGS ----------------
async def load_cogs():
   print("[DEBUG] Loading cogs...")

   for filename in os.listdir("./cogs"):
       if filename.endswith(".py") and not filename.startswith("_"):
           extension = f"cogs.{filename[:-3]}"
           try:
               await bot.load_extension(extension)
               print(f"✅ Loaded {extension}")
           except Exception as e:
               print(f"❌ Failed {extension}: {e}")

   print("[DEBUG] Cog loading complete")

# ---------------- READY EVENT ----------------
@bot.event
async def on_ready():
   print("\n==============================")
   print(f"✅ Logged in as {bot.user}")
   print("==============================")

   print("📜 Prefix commands loaded:")
   for cmd in bot.commands:
       print(f" - {cmd.name}")

   # 🔄 START STATUS LOOP
   if not change_status.is_running():
       change_status.start()
       print("[DEBUG] Status loop started")

   # ⚡ CLEAN + INSTANT SLASH COMMAND SYNC
   GUILD_ID = 1442896370502733898  # 🔥 PUT YOUR SERVER ID HERE

   if not hasattr(bot, "synced"):
       try:
           guild = discord.Object(id=GUILD_ID)

           # 🧹 CLEAR OLD COMMANDS (FIX DUPLICATES)
           bot.tree.clear_commands(guild=guild)

           # 🔄 COPY GLOBAL → GUILD
           bot.tree.copy_global_to(guild=guild)

           # ⚡ SYNC
           synced = await bot.tree.sync(guild=guild)

           print(f"✅ Clean synced {len(synced)} commands")

           bot.synced = True

       except Exception as e:
           print(f"❌ Sync error: {e}")

# ---------------- ERROR HANDLER ----------------
@bot.event
async def on_command_error(ctx, error):
   if isinstance(error, CommandNotFound):
       return

   print(f"[ERROR] {error}")
   await ctx.send(f"❌ Error: {error}")

# ---------------- MAIN ----------------
async def main():
   print("[DEBUG] Bot starting...")

   async with bot:
       await load_cogs()
       print("[DEBUG] Connecting to Discord...")
       await bot.start(TOKEN)

# ---------------- RUN ----------------
if __name__ == "__main__":
   asyncio.run(main())