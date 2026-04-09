import discord
import os
import asyncio
from discord.ext import commands
from flask import Flask
from threading import Thread

# -------------------------
# KEEP ALIVE (FIXED)
# -------------------------
app = Flask(__name__)

@app.route('/')
def home():
   return "Bot is alive!"

def run_web():
   port = int(os.environ.get("PORT"))  # 🔥 NO DEFAULT
   print(f"🌐 Flask running on port {port}")
   app.run(host="0.0.0.0", port=port)

def keep_alive():
   Thread(target=run_web).start()

# -------------------------
# TOKEN
# -------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

# -------------------------
# INTENTS
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# -------------------------
# BOT SETUP
# -------------------------
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

   try:
       synced = await bot.tree.sync()
       print(f"🌐 Synced {len(synced)} slash commands")
   except Exception as e:
       print(f"Sync error: {e}")

# -------------------------
# ERROR HANDLING
# -------------------------
@bot.event
async def on_command_error(ctx, error):
   await ctx.send(f"❌ Error: {str(error)}")

# -------------------------
# START BOT
# -------------------------
async def main():
   keep_alive()  # 🔥 MUST BE FIRST

   async with bot:
       await load_cogs()
       await bot.start(TOKEN)

asyncio.run(main())