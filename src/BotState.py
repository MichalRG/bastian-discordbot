import random
from functools import partial
from typing import List, Optional

from discord import SlashCommandGroup, Option

from src.games.CharacterEye import CharacterEye
from src.games.EyeAdmin import EyeAdminCommands
from src.games.GeneralEye import GeneralEyeCommands
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
        self.eye_bots = {}
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

    async def __set_up_admin_commends(self):
        self.client.add_cog(AdminCommands(self.client, self.admin_channel_allowed_to_use, self.admin_roles))

    async def __setup_dev_commands(self):
        self.client.devmode_initialized = True
        self.client.add_cog(DevTestCommands())

    async def __setup_rupella_commands(self):
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

    async def __setup_eyes_commands(self):
        self.client.eye_game_initialized = True

        players = self.config.get_config_key("games.eye.bot_names")

        for player_name in players:
            self.eye_bots[player_name] = CharacterEye(
                name=player_name,
                config=self.config,
                roles=self.roles,
                channels=self.channels_allowed_to_use
            )

        try:
            self.__initiate_eye_commends()
        except Exception as error:
            print("Adding Eye Game has failed", error)

    async def __setup_and_run_welcome_section(self):
        welcome = WelcomeCommands(config=self.config)

        await welcome.welcome_guests(random.choice(self.channels_allowed_to_use))

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

    def __initiate_eye_commends(self):
        eye_admin_commands = EyeAdminCommands(
            self.config,
            None,
            self.roles,
            self.channels_allowed_to_use,
            self.admin_roles,
            self.admin_channel_allowed_to_use
        )
        self.client.add_cog(eye_admin_commands)

        general_eye_commands = GeneralEyeCommands(None, self.roles, self.channels_allowed_to_use)
        self.client.add_cog(general_eye_commands)

        for key, player_object in self.eye_bots.items():
            char_group = SlashCommandGroup(player_object.name, f"Komendy związane z {player_object.name.capitalize()}")

            challenge_command = self.make_challenge_command()
            roll_command = self.make_roll_command()
            draw_command = self.make_draw_command()

            char_group.command(name="wyzwij", description=f"Wyzwij {player_object.name}")\
                        (challenge_command)
            char_group.command(name="rzuć", description=f"Rzuć kością w grze z {player_object.name}")\
                        (roll_command)
            char_group.command(name="dobierz", description=f"Dobierz kość w grze z {player_object.name}")\
                        (draw_command)

            self.client.add_application_command(char_group)

    def make_challenge_command(self):
        async def challenge(ctx, number: Option(int, "Podaj kwotę zakładu")):
            player_name = ctx.command.full_parent_name
            await self.eye_bots.get(player_name).challenge(ctx, number)
        return challenge

    def make_roll_command(self):
        async def roll(ctx):
            player_name = ctx.command.full_parent_name
            await self.eye_bots.get(player_name).player_roll_dices(ctx)
        return roll

    def make_draw_command(self):
        async def draw(ctx):
            player_name = ctx.command.full_parent_name
            await self.eye_bots.get(player_name).player_draw_die(ctx)
        return draw
