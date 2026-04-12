
import asyncio
import json
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

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


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"✅ Loaded {extension}")
            except Exception as e:
                print(f"❌ Failed {extension}: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    if not hasattr(bot, "synced"):
        try:
            synced = await bot.tree.sync()
            print(f"🔁 Synced {len(synced)} commands")
            bot.synced = True
        except Exception as e:
            print(f"❌ Sync error: {e}")


@bot.event
async def on_command_error(ctx, error):
    print(f"ERROR: {error}")
    await ctx.send(f"❌ {error}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
