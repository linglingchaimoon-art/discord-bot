import discord
import os
import json
import logging
from discord.ext import commands
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN not found")

def ensure_file(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

ensure_file("data.json")
ensure_file("tickets.json")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

bot.setup_hook = load_cogs

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    if not hasattr(bot, "synced"):
        try:
            synced = await bot.tree.sync()
            print(f"🌐 Synced {len(synced)} commands")
            bot.synced = True
        except Exception as e:
            print(f"❌ Sync error: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Error: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
