import random
from typing import List, Optional

from discord import SlashCommandGroup, Option

from src.games.character import Character
from src.games.eye import EyeGame
from src.sections.Admin import AdminCommands
from src.sections.DevTest import DevTestCommands
from src.sections.Rupella import RupellaGuard
from src.sections.WelcomeCommands import WelcomeCommands
from src.services.config import Config


class BotState:
    def __init__(self, client):
        self.client = client
        self.config = Config()
        self.rupella_manager = None
        self.admins = []
        self.channels_allowed_to_use = []
        self.admin_channel_allowed_to_use = []
        self.roles = self.config.get_config_key("games.eye.roles")
        self.admin_roles = []
        self.__load_config()

    def __load_config(self):
        self.__setup_admin_config()

        permissions_access_guild = self.config.get_permissions_access_for_guilds()

        current_client_guilds = self.client.guilds

        AWANTURNICY_text_channels, AWANTURNICY, TEST_text_channels, TEST, TEST_2_text_channels, TEST_2 = \
            self.__get_guilds_and_text_channels(current_client_guilds)

        if permissions_access_guild.get('awanturnicy'):
            self.channels_allowed_to_use, self.admin_channel_allowed_to_use = self.__get_allowed_channels(
                AWANTURNICY_text_channels,
                AWANTURNICY
            )
        if permissions_access_guild.get('test'):
            self.channels_allowed_to_use, self.admin_channel_allowed_to_use = self.__get_allowed_channels(
                TEST_text_channels,
                TEST
            )
        if permissions_access_guild.get('testcior-2'):
            self.channels_allowed_to_use, self.admin_channel_allowed_to_use = self.__get_allowed_channels(
                TEST_2_text_channels,
                TEST_2
            )

        if not self.channels_allowed_to_use:
            exit('[Self exit]: No privileges for channels')

    async def setup_sections(self):
        await self.__setup_section_if_permitted('welcome', self.__setup_and_run_welcome_section)
        await self.__setup_section_if_permitted('games.eye', self.__setup_eyes_commands)
        await self.__setup_section_if_permitted('actions.rupella', self.__setup_rupella_commands)
        await self.__setup_section_if_permitted('devmode', self.__setup_dev_commands)
        await self.__setup_section_if_permitted(None, self.__set_up_admin_commends)

    async def __setup_section_if_permitted(self, section_name: Optional[str], setup_function: callable):
        if self.config.get_process_permissions_for_section(section_name):
            await setup_function()

    def __set_up_admin_commends(self):
        self.client.add_cog(AdminCommands(self.client, self.admin_channel_allowed_to_use, self.admin_roles))

    def __setup_dev_commands(self):
        self.client.devmode_initialized = True
        self.client.add_cog(DevTestCommands())

    def __setup_rupella_commands(self):
        self.client.rupella_action_initialized = True

        roles = self.config.get_config_key("actions.rupella.roles")

        try:
            self.rupella_manager = RupellaGuard(
                    self.config,
                    None,
                    roles,
                    self.channels_allowed_to_use,
                    self.admin_roles,
                    self.admin_channel_allowed_to_use
                )

            self.client.add_cog(self.rupella_manager)
        except Exception as error:
            print("Adding Rupella Actions has failed", error)

    def __setup_eyes_commands(self):
        self.client.eye_game_initialized = True

        roles = self.__get_allowed_roles_for_eye()
        players = self.config.get_config_key("games.eye.bot_names")

        players_objects = []

        for player_name in players:
            players_objects.append(Character(
                name=player_name,
                config=self.config,
                roles=self.roles,
                channels=self.channels_allowed_to_use
            ))

        try:
            self.__initiate_commends(players_objects)
        except Exception as error:
            print("Adding Eye Game has failed", error)

    async def __setup_and_run_welcome_section(self):
        welcome = WelcomeCommands(config=self.config)

        await welcome.welcome_guests(random.choice(self.channels_allowed_to_use))

    def __get_allowed_roles_for_eye(self):
        return self.config.get_config_key("games.eye.roles")

    """
    This methods require to adds new legit guilds handling if such will appear it require to add variables 
    and assigne to them proper channels
    """
    def __get_guilds_and_text_channels(self, current_client_guilds):
        legit_guilds = self.config.get_legit_guilds()
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

    def __get_allowed_channels(self, text_channels_to_check, guild) -> [List, List]:
        legit_channels = self.config.get_legit_channels()
        admin_legit_channels = self.config.get_config_key("legit.admin_channels")
        channels_to_use = []
        admin_channels = []

        for channel in text_channels_to_check:
            if channel.id in legit_channels and channel.permissions_for(guild.me).send_messages:
                channels_to_use.append(channel)
            if channel.id in admin_legit_channels and channel.permissions_for(guild.me).send_messages:
                admin_channels.append(channel)

        return channels_to_use, admin_channels

    def __setup_admin_config(self):
        self.admins = self.config.get_config_key("ADMIN_IDS")
        self.admin_roles = self.config.get_config_key("legit.admin_roles")

    def __initiate_commends(self, players_objects):
        for player_object in players_objects:
            char_group = SlashCommandGroup(player_object.name, f"Commands related to {player_object.name}")

            @char_group.command(description=f"Wyzwij {player_object.name.capitalize()}")
            async def challenge(ctx, number: Option(int, "Podaj kwotę zakładu")):
                await player_object.challenge(ctx, number)

            @char_group.command(description=f"Rzuć kością w grze z {player_object.name.capitalize()}")
            async def roll(ctx):
                # Assuming a roll method exists
                await player_object.player_roll_dices(ctx)

            @char_group.command(description=f"Dobierz kość w grze z {player_object.name.capitalize()}")
            async def draw(ctx):
                await player_object.player_draw_die(ctx)

            self.client.add_application_command(char_group)
