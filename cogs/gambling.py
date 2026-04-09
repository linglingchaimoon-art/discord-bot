import discord
import random
import json
import time
import os
from discord.ext import commands
from PIL import Image, ImageOps

DATA_FILE = "data.json"
OWNER_ID = 1398304429085556746

DAILY_REWARD = 500
BLACKJACK_MULTIPLIER = 1.5
STEAL_COOLDOWN = 18000


# -------------------------
# DATA
# -------------------------
def load_data():
   try:
       with open(DATA_FILE, "r") as f:
           return json.load(f)
   except:
       return {}

def save_data(data):
   with open(DATA_FILE, "w") as f:
       json.dump(data, f, indent=4)

def fix_user(user):
   defaults = {
       "balance": 1000,
       "last_daily": 0,
       "last_steal": 0
   }
   for k, v in defaults.items():
       if k not in user:
           user[k] = v
   return user


# -------------------------
# CARDS
# -------------------------
SUITS = ["♠","♥","♦","♣"]
VALUES = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

def draw_card():
   return f"{random.choice(VALUES)}{random.choice(SUITS)}"

def card_to_filename(card):
   suit_map = {"♠":"S","♥":"H","♦":"D","♣":"C"}
   return f"{card[:-1]}{suit_map[card[-1]]}.png"

def load_card(card):
   path = f"cards/{card_to_filename(card)}"
   if not os.path.exists(path):
       return None
   return Image.open(path).convert("RGBA").resize((120,180))


# -------------------------
# UI
# -------------------------
def prepare(img):
   bg = Image.new("RGBA", img.size, (255,255,255,255))
   bg.paste(img, (0,0), img)
   return ImageOps.expand(bg, border=2, fill=(200,200,200))

def generate_table(player, dealer, hide=True):
   card_w, spacing = 120, 20

   player_imgs = [prepare(load_card(c)) for c in player if load_card(c)]

   dealer_imgs = []
   for i, c in enumerate(dealer):
       if i == 1 and hide:
           img = Image.open("cards/back.png").convert("RGBA").resize((120,180))
       else:
           img = load_card(c)
       if img:
           dealer_imgs.append(prepare(img))

   width = max(len(player_imgs), len(dealer_imgs)) * (card_w + spacing) + 60
   canvas = Image.new("RGBA", (width, 450), (47,49,54,255))

   x = 30
   for img in dealer_imgs:
       canvas.paste(img, (x, 20))
       x += card_w + spacing

   x = 30
   for img in player_imgs:
       canvas.paste(img, (x, 240))
       x += card_w + spacing

   canvas.save("game.png")
   return "game.png"


def value(hand):
   total, aces = 0, 0
   for c in hand:
       v = c[:-1]
       if v in ["J","Q","K"]:
           total += 10
       elif v == "A":
           total += 11
           aces += 1
       else:
           total += int(v)

   while total > 21 and aces:
       total -= 10
       aces -= 1

   return total


# -------------------------
# PAY CONFIRM
# -------------------------
class PayView(discord.ui.View):
   def __init__(self, ctx, member, amount, cog):
       super().__init__(timeout=None)
       self.ctx = ctx
       self.member = member
       self.amount = amount
       self.cog = cog

   async def interaction_check(self, interaction):
       return interaction.user == self.ctx.author

   @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
   async def confirm(self, interaction, _):
       sender = self.cog.get_user(self.ctx.author.id)
       receiver = self.cog.get_user(self.member.id)

       if sender["balance"] < self.amount:
           return await interaction.response.edit_message(content="❌ Not enough money.", view=None)

       sender["balance"] -= self.amount
       receiver["balance"] += self.amount
       save_data(self.cog.data)

       await interaction.response.edit_message(
           content=f"💸 Sent **{self.amount}** to {self.member.mention}",
           view=None
       )

   @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
   async def cancel(self, interaction, _):
       await interaction.response.edit_message(content="❌ Cancelled.", view=None)


# -------------------------
# BLACKJACK
# -------------------------
class BlackjackView(discord.ui.View):
   def __init__(self, ctx, player, dealer, bet, cog):
       super().__init__(timeout=None)
       self.ctx = ctx
       self.player = player
       self.dealer = dealer
       self.bet = bet
       self.cog = cog

   async def interaction_check(self, interaction):
       if interaction.user != self.ctx.author:
           await interaction.response.send_message("❌ Not your game!", ephemeral=True)
           return False
       return True

   async def send_start(self):
       file = discord.File(generate_table(self.player, self.dealer, True), filename="game.png")

       embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.dark_theme())
       embed.description = f"{self.ctx.author.mention}\n💸 Bet: {self.bet}"
       embed.add_field(name="Your Total", value=value(self.player))
       embed.add_field(name="Dealer", value="Hidden")

       embed.set_image(url="attachment://game.png")

       msg = await self.ctx.send(embed=embed, file=file)
       await msg.edit(view=self)

   async def update(self, interaction, result=None, winnings=None, end=False):
       file = discord.File(generate_table(self.player, self.dealer, not end), filename="game.png")

       embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.dark_theme())
       embed.description = f"{self.ctx.author.mention}\n💸 Bet: {self.bet}"

       embed.add_field(name="Your Total", value=value(self.player))
       embed.add_field(name="Dealer Total", value=value(self.dealer))

       if result:
           embed.add_field(name="Result", value=result)

       if winnings is not None:
           embed.add_field(name="💰 Winnings", value=winnings)

       embed.set_image(url="attachment://game.png")

       if end:
           self.cog.active_games.pop(self.ctx.author.id, None)

       await interaction.response.edit_message(
           embed=embed,
           attachments=[file],
           view=None if end else self
       )

   @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
   async def hit(self, interaction, _):
       self.player.append(draw_card())

       if value(self.player) > 21:
           user = self.cog.get_user(self.ctx.author.id)
           user["balance"] -= self.bet
           save_data(self.cog.data)
           return await self.update(interaction, "❌ Bust!", -self.bet, True)

       await self.update(interaction)

   @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger)
   async def stand(self, interaction, _):
       while value(self.dealer) < 17:
           self.dealer.append(draw_card())

       user = self.cog.get_user(self.ctx.author.id)

       if value(self.dealer) > 21 or value(self.player) > value(self.dealer):
           winnings = int(self.bet * BLACKJACK_MULTIPLIER)
           user["balance"] += winnings
           result = "✅ You Win!"
       else:
           winnings = -self.bet
           user["balance"] -= self.bet
           result = "❌ You Lose!"

       save_data(self.cog.data)
       await self.update(interaction, result, winnings, True)


# -------------------------
# COG
# -------------------------
class Gambling(commands.Cog):
   def __init__(self, bot):
       self.bot = bot
       self.data = load_data()
       self.active_games = {}

   def get_user(self, uid):
       uid = str(uid)
       if uid not in self.data:
           self.data[uid] = {}
       return fix_user(self.data[uid])

   # 💰 BALANCE
   @commands.command()
   async def balance(self, ctx, member: discord.Member = None):
       member = member or ctx.author
       user = self.get_user(member.id)
       await ctx.send(f"💰 {member.mention}: **{user['balance']}**")

   # 🎁 DAILY
   @commands.command()
   async def daily(self, ctx):
       user = self.get_user(ctx.author.id)
       now = int(time.time())

       if now - user["last_daily"] < 86400:
           return await ctx.send("⏳ You already claimed daily!")

       user["balance"] += DAILY_REWARD
       user["last_daily"] = now
       save_data(self.data)

       await ctx.send(f"🎁 You received **{DAILY_REWARD}**!")

   # 💸 ADD MONEY (OWNER)
   @commands.command()
   async def addmoney(self, ctx, member: discord.Member, amount: int):
       if ctx.author.id != OWNER_ID:
           return await ctx.send("❌ Not allowed")

       user = self.get_user(member.id)
       user["balance"] += amount
       save_data(self.data)

       await ctx.send(f"💰 Added **{amount}** to {member.mention}")

   # 💸 REMOVE MONEY
   @commands.command()
   async def removemoney(self, ctx, member: discord.Member, amount: int):
       if ctx.author.id != OWNER_ID:
           return await ctx.send("❌ Not allowed")

       user = self.get_user(member.id)
       user["balance"] = max(0, user["balance"] - amount)
       save_data(self.data)

       await ctx.send(f"💸 Removed **{amount}** from {member.mention}")

   # 💸 PAY
   @commands.command()
   async def pay(self, ctx, member: discord.Member, amount: int):
       await ctx.send(
           f"💸 Send **{amount}** to {member.mention}?",
           view=PayView(ctx, member, amount, self)
       )

   # 🕵️ STEAL
   @commands.command()
   async def steal(self, ctx, member: discord.Member):
       thief = self.get_user(ctx.author.id)
       victim = self.get_user(member.id)

       now = int(time.time())

       if now - thief["last_steal"] < STEAL_COOLDOWN:
           return await ctx.send("⏳ Wait before stealing again")

       if random.randint(1, 100) <= 40:
           amount = int(victim["balance"] * 0.2)
           victim["balance"] -= amount
           thief["balance"] += amount
           result = f"🕵️ You stole **{amount}** from {member.mention}"
       else:
           amount = int(thief["balance"] * 0.1)
           thief["balance"] -= amount
           result = f"🚔 Failed! Lost **{amount}**"

       thief["last_steal"] = now
       save_data(self.data)

       await ctx.send(result)

   # 🎮 BLACKJACK
   @commands.command()
   async def blackjack(self, ctx, bet):
       user = self.get_user(ctx.author.id)

       if ctx.author.id in self.active_games:
           return await ctx.send("❌ You already have an active game!")

       if isinstance(bet, str) and bet.lower() in ["all", "allin", "all-in"]:
           bet = user["balance"]
       else:
           try:
               bet = int(bet)
           except:
               return await ctx.send("❌ Invalid bet")

       if bet <= 0 or bet > user["balance"]:
           return await ctx.send("❌ Invalid bet")

       view = BlackjackView(ctx, [draw_card(), draw_card()], [draw_card(), draw_card()], bet, self)
       self.active_games[ctx.author.id] = view

       await view.send_start()


async def setup(bot):
   await bot.add_cog(Gambling(bot))