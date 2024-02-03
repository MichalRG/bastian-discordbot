import asyncio
import logging
import random
from typing import List

import discord
import os

from discord.ext import commands

from games.eye import EyeGame
from sections.DevTest import DevTestCommands
from sections.Rupella import RupellaGuard
from sections.welcome import Welcome
from services.config import Config

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
rupella_manager = None
admins = []

channels_allowed_to_use = []
admin_channel_allowed_tou_use = []
roles_allowed_to_process = []

"""
This methods require to adds new legit guilds handling if such will appear it require to add variables and assignem to them proper channels
"""
def __get_guilds_and_text_channels(current_client_guilds):
    legit_guilds = config.get_legit_guilds()
    AWANTURNICY_text_channels = []
    AWANTURNICY = None
    TEST_text_channels = []
    TEST = None
    TESCIOR_2_text_channels = []
    TESCIOR_2 = None

    for guild in current_client_guilds:
        if guild.name in legit_guilds:
            if guild.name == legit_guilds[0]:
                AWANTURNICY_text_channels = guild.text_channels
                AWANTURNICY = guild
            elif guild.name == legit_guilds[1]:
                TEST_text_channels = guild.text_channels
                TEST = guild
            elif guild.name == legit_guilds[2]:
                TESCIOR_2_text_channels = guild.text_channels
                TESCIOR_2 = guild

    return AWANTURNICY_text_channels, AWANTURNICY, TEST_text_channels, TEST, TESCIOR_2_text_channels, TESCIOR_2


def __get_allowed_channels(text_channels_to_check, guild) -> [List, List]:
    legit_channels = config.get_legit_channels()
    admin_legit_channels = config.get_config_key("legit.admin_channels")
    channels_to_use = []
    admin_channels = []

    for channel in text_channels_to_check:
        if channel.name in legit_channels and channel.permissions_for(guild.me).send_messages:
            channels_to_use.append(channel)
        if channel.name in admin_legit_channels and channel.permissions_for(guild.me).send_messages:
            admin_channels.append(channel)

    return channels_to_use, admin_channels


def __set_allowed_channels():
    global channels_allowed_to_use
    global admin_channel_allowed_tou_use

    permissions_access_guild = config.get_permissions_access_for_guilds()

    current_client_guilds = client.guilds

    AWANTURNICY_text_channels, AWANTURNICY, TEST_text_channels, TEST, TEST_2_text_channels, TEST_2 = \
        __get_guilds_and_text_channels(current_client_guilds)

    if permissions_access_guild.get('awanturnicy'):
        channels_allowed_to_use, admin_channel_allowed_tou_use = __get_allowed_channels(AWANTURNICY_text_channels, AWANTURNICY)
    if permissions_access_guild.get('test'):
        channels_allowed_to_use, admin_channel_allowed_tou_use = __get_allowed_channels(TEST_text_channels, TEST)
    if permissions_access_guild.get('testcior-2'):
        channels_allowed_to_use, admin_channel_allowed_tou_use = __get_allowed_channels(TEST_2_text_channels, TEST_2)

    if channels_allowed_to_use == []:
        exit('[Self exit]: No privileges for channels')

def __set_admins() -> List[str]:
    global admins
    admins = config.get_config_key("ADMIN_IDS")

def __get_allowed_roles_for_eye():
    return config.get_config_key("games.eye.roles")


async def keep_alive():
    while True:
        logger.info(f'Current bot latency: {client.latency*1000:.2f}ms')
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again

# @client.event
# async def on_connect():
#     if client.auto_sync_commands:
#         await client.sync_commands()
#         print(f"{client.user.name} synchronized.")
#     print(f"{client.user.name} connected.")

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id}). Ready event called.')
    client.loop.create_task(keep_alive())

    global rupella_manager
    __set_allowed_channels()
    __set_admins()

    if config.get_process_permissions_for_section('welcome'):
        welcome = Welcome(config=config)

        await welcome.welcome_guests(random.choice(channels_allowed_to_use))

    if config.get_process_permissions_for_section('games.eye') and not hasattr(client, 'eye_game_initialized'):
        client.eye_game_initialized = True

        roles = __get_allowed_roles_for_eye()

        try:
            client.add_cog(EyeGame(config, None, roles, channels_allowed_to_use, admins, admin_channel_allowed_tou_use))
        except Exception as error:
            print("Adding Eye Game has failed", error)
    if config.get_process_permissions_for_section('actions.rupella') and not hasattr(client, 'rupella_action_initialized'):
        client.rupella_action_initialized = True

        roles = config.get_config_key("actions.rupella.roles")

        try:
            rupella_manager = RupellaGuard(config, None, roles, channels_allowed_to_use, admins, admin_channel_allowed_tou_use)
            client.add_cog(rupella_manager)
        except Exception as error:
            print("Adding Rupella Actions has failed", error)

    if config.get_process_permissions_for_section('devmode') and not hasattr(client, 'devmode_initialized'):
        client.devmode_initialized = True
        client.add_cog(DevTestCommands())

    await client.sync_commands(guild_ids=['1198002006481178805'])  # Sync commands


@client.event
async def on_message(message):
    global rupella_manager
    role_names = [role.name for role in message.author.roles]
    approved_user = False

    for name in role_names:
        if name in __get_allowed_roles_for_eye():
            approved_user = True
            break

    if message.author == client.user or not approved_user:
        return

    if rupella_manager is not None:
        await rupella_manager.rupella_actions_check(message)


def __get_user_name_roles(message):
    return [role.name for role in message.author.roles]


def __validate_if_eye_allowed_to_process(roles, channel):
    return config.get_process_permissions_for_section('games.eye') and bool(
        set(roles) & set(roles_allowed_to_process)) and channel in channels_allowed_to_use


# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#
#     roles = __get_user_name_roles(message)
#
#     if __validate_if_eye_allowed_to_process(roles, message.channel):
#         await eye_game.process_eye_commands(message)

# await client.sync_commands()  # Sync commands
# async def main():
#     await client.sync_commands()  # Sync commands
#     await client.start(token)

client.run(token)

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())