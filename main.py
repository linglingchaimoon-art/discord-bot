import discord
import os
import asyncio
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

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


# -------------------------
# FORCE KEEP ALIVE LOOP
# -------------------------
async def keep_alive():
   while True:
       await asyncio.sleep(60)


# -------------------------
# MAIN
# -------------------------
async def main():
   await load_cogs()
   asyncio.create_task(keep_alive())  # 🔥 prevents shutdown
   await bot.start(TOKEN)


asyncio.run(main())