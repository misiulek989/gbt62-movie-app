import eventlet
eventlet.monkey_patch()

import os
import asyncio
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import discord
from discord.ext import commands

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Discord Configuration
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
latest_discord_channel = None

# Setup Discord Bot client
intents = discord.Intents.default()
intents.message_content = True
discord_client = commands.Bot(command_prefix="!", intents=intents)

@discord_client.event
async def on_ready():
    print(f'Discord bot logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    global latest_discord_channel
    # Ignore messages sent by the bot itself
    if message.author == discord_client.user:
        return
    
    latest_discord_channel = message.channel
    user_text = message.content

    # Beam the Discord message to your Secret Operator Dashboard in real-time!
    socketio.emit('new_prompt_for_operator', {'message': f"[Discord @{message.author.name}]: {user_text}"})

# Run the Discord bot in a background thread so it doesn't block Flask
def run_discord_bot():
    try:
        asyncio.run(discord_client.start(DISCORD_TOKEN))
    except Exception as e:
        print(f"Discord bot error: {e}")

threading.Thread(target=run_discord_bot, daemon=True).start()

# Flask Routes
@app.route('/')
def user_view():
    return render_template('user_chat.html')

@app.route('/operator-secret-dashboard')
def operator_view():
    return render_template('operator.html')

@socketio.on('send_from_user')
def handle_user_message(data):
    emit('new_prompt_for_operator', {'message': f"[Web User]: {data['message']}"}, broadcast=True)

@socketio.on('send_from_operator')
def handle_operator_message(data):
    operator_text = data['message']
    
    # Send back to web users
    emit('new_response_to_user', {'message': operator_text}, broadcast=True)
    
    # Also send back to Discord if someone recently messaged the bot
    global latest_discord_channel
    if latest_discord_channel:
        future = asyncio.run_coroutine_threadsafe(
            latest_discord_channel.send(operator_text), 
            discord_client.loop
        )
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Failed to send to Discord: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)