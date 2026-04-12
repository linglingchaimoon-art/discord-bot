
import asyncio
import itertools
import json
import logging
import os
import threading

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from cogs.music import MusicControls
from web import run_web

logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found")


def ensure_file(file_path: str):
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
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"✅ Loaded {extension}")
            except Exception as e:
                print(f"❌ Failed {extension}: {e}")


# ✅ SINGLE on_ready (MERGED)
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Add persistent views (IMPORTANT for buttons)
    bot.add_view(MusicControls(bot.get_cog("Music")))

    # Start dashboard
    if not hasattr(bot, "web_started"):
        threading.Thread(target=run_web, args=(bot,), daemon=True).start()
        bot.web_started = True
        print("🌐 Dashboard running")

    # Start status loop
    if not change_status.is_running():
        change_status.start()

    # Sync slash commands
    if not hasattr(bot, "synced"):
        try:
            synced = await bot.tree.sync()
            print(f"🔁 Synced {len(synced)} commands")
            bot.synced = True
        except Exception as e:
            print(f"❌ Sync error: {e}")


# ✅ ERROR DEBUG (VERY IMPORTANT)
@bot.event
async def on_command_error(ctx, error):
    print(f"ERROR: {error}")
    await ctx.send(f"❌ {error}")


async def main():
    async with bot:
        await load_cogs()  # loads gambling.py automatically
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())