import asyncio
import logging
import random
from typing import List, Optional

import discord
import os

from discord.ext import commands

from src.games.eye import EyeGame
from src.sections.Admin import AdminCommands
from src.sections.DevTest import DevTestCommands
from src.sections.Rupella import RupellaGuard
from src.sections.WelcomeCommends import WelcomeCommends
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
RUPELLA_MANAGER = None
admins = []

channels_allowed_to_use = []
admin_channel_allowed_to_use = []
roles_allowed_to_process = []

"""
This methods require to adds new legit guilds handling if such will appear it require to add variables 
and assignem to them proper channels
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
        if guild.id == legit_guilds[0]:
            AWANTURNICY_text_channels = guild.text_channels
            AWANTURNICY = guild
        elif guild.id == legit_guilds[1]:
            TEST_text_channels = guild.text_channels
            TEST = guild
        elif guild.id == legit_guilds[2]:
            TESCIOR_2_text_channels = guild.text_channels
            TESCIOR_2 = guild

    return AWANTURNICY_text_channels, AWANTURNICY, TEST_text_channels, TEST, TESCIOR_2_text_channels, TESCIOR_2


async def setup_section_if_permitted(section_name: Optional[str], setup_function: callable):
    if config.get_process_permissions_for_section(section_name):
        await setup_function()


def __get_allowed_channels(text_channels_to_check, guild) -> [List, List]:
    legit_channels = config.get_legit_channels()
    admin_legit_channels = config.get_config_key("legit.admin_channels")
    channels_to_use = []
    admin_channels = []

    for channel in text_channels_to_check:
        if channel.id in legit_channels and channel.permissions_for(guild.me).send_messages:
            channels_to_use.append(channel)
        if channel.id in admin_legit_channels and channel.permissions_for(guild.me).send_messages:
            admin_channels.append(channel)

    return channels_to_use, admin_channels


def __set_allowed_channels():
    global channels_allowed_to_use
    global admin_channel_allowed_to_use

    permissions_access_guild = config.get_permissions_access_for_guilds()

    current_client_guilds = client.guilds

    AWANTURNICY_text_channels, AWANTURNICY, TEST_text_channels, TEST, TEST_2_text_channels, TEST_2 = \
        __get_guilds_and_text_channels(current_client_guilds)

    if permissions_access_guild.get('awanturnicy'):
        channels_allowed_to_use, admin_channel_allowed_to_use = __get_allowed_channels(AWANTURNICY_text_channels, AWANTURNICY)
    if permissions_access_guild.get('test'):
        channels_allowed_to_use, admin_channel_allowed_to_use = __get_allowed_channels(TEST_text_channels, TEST)
    if permissions_access_guild.get('testcior-2'):
        channels_allowed_to_use, admin_channel_allowed_to_use = __get_allowed_channels(TEST_2_text_channels, TEST_2)

    if channels_allowed_to_use == []:
        exit('[Self exit]: No privileges for channels')

def __set_admins() -> List[str]:
    global admins
    admins = config.get_config_key("ADMIN_IDS")

def __get_allowed_roles_for_eye():
    return config.get_config_key("games.eye.roles")


async def set_latency_log():
    while True:
        logger.info(f'Current bot latency: {client.latency*1000:.2f}ms')
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again


def set_up_admin_commends():
    admin_roles = config.get_config_key("legit.admin_roles")
    admin_channels = config.get_config_key("legit.admin_roles")

    client.add_cog(AdminCommands(client, admin_channels, admin_roles))


def setup_dev_commands():
    client.devmode_initialized = True
    client.add_cog(DevTestCommands())


def setup_rupella_commands():
    global RUPELLA_MANAGER

    client.rupella_action_initialized = True

    roles = config.get_config_key("actions.rupella.roles")

    try:
        RUPELLA_MANAGER = \
            RupellaGuard(config, None, roles, channels_allowed_to_use, admins, admin_channel_allowed_to_use)
        client.add_cog(RUPELLA_MANAGER)
    except Exception as error:
        print("Adding Rupella Actions has failed", error)


def setup_eyes_commands():
    client.eye_game_initialized = True

    roles = __get_allowed_roles_for_eye()

    try:
        client.add_cog(EyeGame(config, None, roles, channels_allowed_to_use, admins, admin_channel_allowed_to_use))
    except Exception as error:
        print("Adding Eye Game has failed", error)


async def setup_welcome_section():
    welcome = WelcomeCommends(config=config)

    await welcome.welcome_guests(random.choice(channels_allowed_to_use))


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id}). Ready event called.')
    client.loop.create_task(set_latency_log())

    try:
        __set_allowed_channels()
        __set_admins()

        await setup_section_if_permitted('welcome', setup_welcome_section)
        await setup_section_if_permitted('games.eye', setup_eyes_commands)
        await setup_section_if_permitted('actions.rupella', setup_rupella_commands)
        await setup_section_if_permitted('devmode', setup_dev_commands)
        await setup_section_if_permitted(None, set_up_admin_commends)
    except Exception as ex:
        print(f"Something went wrong during settingup sections: {ex}")


@client.event
async def on_message(message):
    global RUPELLA_MANAGER
    role_ids = [role.id for role in message.author.roles]
    approved_user = False

    for id in role_ids:
        if id in __get_allowed_roles_for_eye():
            approved_user = True
            break

    if message.author == client.user or not approved_user:
        return

    if RUPELLA_MANAGER is not None:
        await RUPELLA_MANAGER.rupella_actions_check(message)


def __get_user_name_roles(message):
    return [role.name for role in message.author.roles]


def __validate_if_eye_allowed_to_process(roles, channel):
    return config.get_process_permissions_for_section('games.eye') and bool(
        set(roles) & set(roles_allowed_to_process)) and channel in channels_allowed_to_use

client.run(token)
