from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

bot = None
music_cog = None

def run_web(bot_instance):
   global bot, music_cog
   bot = bot_instance

   # get music cog from your bot
   music_cog = bot.get_cog("Music")

   app.run(port=5000)


@app.route("/")
def index():
   return render_template("index.html")


@app.route("/play", methods=["POST"])
def play():
   data = request.json
   query = data.get("query")

   GUILD_ID = 123456789
   VOICE_CHANNEL_ID = 123456789

   guild = bot.get_guild(GUILD_ID)
   channel = guild.get_channel(VOICE_CHANNEL_ID)

   bot.loop.create_task(
       music_cog.add_song(query, channel)
   )

   return jsonify({"status": "playing"})


@app.route("/stop", methods=["POST"])
def stop():
   music_cog.stop()
   return jsonify({"status": "stopped"})


@app.route("/queue")
def queue():
   return jsonify(music_cog.queue)