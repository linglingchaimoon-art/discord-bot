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

    GUILD_ID = 1442896370502733898       # ⚠️ your server ID
    USER_ID = 1398304429085556746        # ⚠️ your Discord user ID

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(USER_ID)

    if not member or not member.voice:
        return jsonify({"error": "You are not in a voice channel"})

    channel = member.voice.channel

    bot.loop.create_task(
        music_cog.add_song(query, channel)
    )

    return jsonify({"status": "playing", "channel": str(channel)})


@app.route("/stop", methods=["POST"])
def stop():
    music_cog.stop()
    return jsonify({"status": "stopped"})


@app.route("/queue")
def queue():
    return jsonify(music_cog.queue)