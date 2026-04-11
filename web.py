from flask import Flask, render_template, request, jsonify
import asyncio

app = Flask(__name__)

bot = None


def run_web(bot_instance):
    global bot
    bot = bot_instance
    app.run(port=5000)


@app.route("/")
def index():
    return render_template("index.html")


def get_music_cog():
    return bot.get_cog("Music")


def get_active_voice_channel(guild):
    # ✅ If bot is already connected → use that channel
    if guild.voice_client and guild.voice_client.channel:
        return guild.voice_client.channel

    # ✅ Otherwise find any channel with users
    for vc in guild.voice_channels:
        if len(vc.members) > 0:
            return vc

    return None


@app.route("/play", methods=["POST"])
def play():
    data = request.json
    query = data.get("query")

    GUILD_ID = 1442896370502733898  # your server ID

    guild = bot.get_guild(GUILD_ID)
    music_cog = get_music_cog()

    if not guild or not music_cog:
        return jsonify({"error": "Bot not ready"})

    channel = get_active_voice_channel(guild)

    if not channel:
        return jsonify({"error": "No one is in a voice channel"})

    # ✅ Thread-safe async call
    asyncio.run_coroutine_threadsafe(
        music_cog.add_song(query, channel),
        bot.loop
    )

    return jsonify({
        "status": "playing",
        "channel": channel.name
    })


@app.route("/stop", methods=["POST"])
def stop():
    music_cog = get_music_cog()

    if not music_cog:
        return jsonify({"error": "Music cog not loaded"})

    asyncio.run_coroutine_threadsafe(
        music_cog.stop(),
        bot.loop
    )

    return jsonify({"status": "stopped"})


@app.route("/queue")
def queue():
    music_cog = get_music_cog()

    if not music_cog:
        return jsonify({"error": "Music cog not loaded"})

    return jsonify(music_cog.queue)