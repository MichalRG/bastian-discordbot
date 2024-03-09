import asyncio
import logging
import traceback

import discord
import os

from discord.ext import commands

from src.BotState import BotState
from src.services.config import Config

token = os.environ['bastian']


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='/', intents=intents)

config = Config()
bot_state = None

async def set_latency_log():
    while True:
        logger.info(f'Current bot latency: {client.latency*1000:.2f}ms')
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again

@client.event
async def on_ready():
    global bot_state
    logger.info(f'Logged in as {client.user} (ID: {client.user.id}). Ready event called.')
    bot_state = BotState(client)
    client.loop.create_task(set_latency_log())

    try:
        await bot_state.setup_sections()
        await client.sync_commands(guild_ids=['1109232371666014310'])  # Sync commands
    except Exception as ex:
        print(f"Something went wrong during settingup sections: {ex}")
        traceback.print_exc()

@client.event
async def on_message(message):
    global bot_state
    role_ids = [role.id for role in message.author.roles]
    approved_user = False

    for id in role_ids:
        if id in config.get_config_key("games.eye.roles"):
            approved_user = True
            break

    if message.author == client.user or not approved_user:
        return

    if bot_state and bot_state.rupella_manager is not None:
        await bot_state.rupella_manager.rupella_actions_check(message)


client.run(token)
