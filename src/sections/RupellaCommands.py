import random

import discord
from discord import slash_command
from discord.ext import commands

from src.const.paths import LOCAL_LOGS_RUPELLA_BLACKLIST_PATH, WISE_QUOTES_PATH
from src.helpers.constants import LEGIT_SERVERS
from src.services.Config import Config
from src.services.general_utils import write_to_actions_logs, read_json_file, role_and_channel_valid, reset_localLogs_file
from src.services.Translation import Translation


class RupellaGuard(commands.Cog):
    def __init__(
            self,
            config,
            translation,
            roles,
            channels,
            test_channels,
            admin_roles,
            admins_channels,
            rupella_validator
    ):
        self.config = config or Config()
        self.translation = translation or Translation()
        self.admin_channels = admins_channels
        self.admin_channels_ids = [channel.id for channel in admins_channels]
        self.allowed_channels_ids = channels
        self.test_channels = test_channels
        self.allowed_role_ids = roles
        self.bel_shelorin_quotes = read_json_file(WISE_QUOTES_PATH)
        self.admins_roles = admin_roles
        self.eter_color = 0x000000
        self.rupella_validator = rupella_validator

        self.bel_color = int(self.config.get_config_key("actions.rupella.bel_sherhorin_color"),16)
        self.rueplla_color = int(self.config.get_config_key("actions.rupella.rupella_color"),16)

    async def rupella_actions_check(self, message):
        message_content = message.content.lower().strip()

        if message_content == "!rupella" or message_content == "/rupella":
            what_are_u_doing_here = self.translation.translate("ACTIONS.RUPELLA.SURPRISED")

            embed_message = discord.Embed(
                title="**Rupella**",
                description=what_are_u_doing_here,
                color=self.rueplla_color
            )
            embed_message.set_thumbnail(url="attachment://rupella.png")
            token_file = discord.File("./imgs/rupellaToken.png", filename="rupella.png")

            await message.reply(embed=embed_message, file=token_file)

            self.__write_on_rupella_blacklist(message.author.id)

    def __write_on_rupella_blacklist(self, id: str):
        write_to_actions_logs("rupella-blacklist.txt", id)

    @slash_command(name="cytat", guild_ids=LEGIT_SERVERS, description="Poproś o cytat")
    async def display_available_player(self, ctx):
        if self.rupella_validator.role_and_channel_valid(ctx.author.roles, ctx.channel):
            description_of_elven = self.translation.translate("ACTIONS.RUPELLA.ELVEN.DESCRIPTION")
            introduction_of_elven = self.translation.translate("ACTIONS.RUPELLA.ELVEN.INTRODUCTION")

            quote = random.choice(self.bel_shelorin_quotes).get("quote", "Twoje życie staje się lepsze tylko wtedy, gdy stajesz się lepszym człowiekiem.")

            embed_message = discord.Embed(
                description=f"**Głos z Eteru:**\n{description_of_elven}\n\n**Bel-Sherhorin Pieśniarz Mądrości:**\n{introduction_of_elven}\n\n***{quote}***",
                color=self.bel_color
            )
            embed_message.set_thumbnail(url="attachment://belSherhorinToken.png")
            token_file = discord.File("./imgs/belSherhorinToken.png", filename="belSherhorinToken.png")

            await ctx.respond(embed=embed_message, file=token_file)

    @slash_command(name="reset-rupella-status", guild_ids=LEGIT_SERVERS,
                   description="[Admin command]: reset status for Rupella")
    async def rest_rupella_stats(self, ctx):
        if self.rupella_validator.admin_role_and_channel_valid(ctx.author.roles, ctx.channel):
            reset_localLogs_file(LOCAL_LOGS_RUPELLA_BLACKLIST_PATH)

            success_translation = self.translation.translate("ADMINS.RESET_BOTS_SUCCESSFULLY_PASSED")

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=success_translation,
                color=self.eter_color
            )

            await ctx.respond(embed=embed_message)