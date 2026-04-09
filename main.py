import discord
import os
import asyncio
import logging
import traceback
from discord.ext import commands

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.remove_command("help")

async def load_cogs():
   for filename in os.listdir("./cogs"):
       if filename.endswith(".py"):
           await bot.load_extension(f"cogs.{filename[:-3]}")
           print(f"✅ Loaded {filename}")

@bot.event
async def on_error(event: str, *args, **kwargs):
   logger.error(
       "Unhandled exception in event '%s'\n%s",
       event,
       traceback.format_exc(),
   )

@bot.event
async def on_ready():
   print(f"✅ Logged in as {bot.user}")
   synced = await bot.tree.sync()
   print(f"🌐 Synced {len(synced)} commands")

@bot.event
async def on_message(message):
   pass

async def main():
   async with bot:
       await load_cogs()
       try:
           await bot.start(TOKEN)
       except Exception:
           logger.error("Fatal exception during bot startup\n%s", traceback.format_exc())
           raise

asyncio.run(main())