import discord
import os
import asyncio
from discord.ext import commands

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
async def on_ready():
   print(f"✅ Logged in as {bot.user}")
   synced = await bot.tree.sync()
   print(f"🌐 Synced {len(synced)} commands")

async def main():
   async with bot:
       await load_cogs()
       await bot.start(TOKEN)

asyncio.run(main())