import discord
from discord import Option, slash_command
from discord.ext import commands

from src.helpers.constants import LEGIT_SERVERS
from src.services.config import Config
from src.services.general_utils import reset_localLogs_file, read_file_lines
from src.services.translation import Translation


class EyeAdminCommands(commands.Cog):
    def __init__(self, config, translation, roles, channels, admin_roles, admin_channel_allowed_tou_use):
        self.config = config or Config()
        self.translation = translation or Translation()
        self.allowed_channels = channels
        self.allowed_channels_ids = [channel.id for channel in channels]
        self.allowed_admin_channels = admin_channel_allowed_tou_use
        self.admin_channel_allowed_to_use_ids = [channel.id for channel in admin_channel_allowed_tou_use]
        self.allowed_id_roles = roles
        self.admin_roles = admin_roles
        self.bot_names = self.config.get_config_key("games.eye.bot_names")
        self.eter_color = 0x000000

    @slash_command(
        name="reset-bots-status",
        guild_ids=LEGIT_SERVERS,
        description="[Admin command]: reset status of all players for all bots"
    )
    async def rest_stats(self, ctx, name: Option(str, "Enter a bot name")):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            if name == 'all':
                for name in self.bot_names:
                    reset_localLogs_file(f"oko/{name}.txt")
            elif name in self.bot_names:
                reset_localLogs_file(f"oko/{name}.txt")
            else:
                return
            success_translation = \
                self.translation.translate("ADMINS.RESET_BOTS_SUCCESSFULLY_PASSED")
            embed_message = discord.Embed(
                title="**Głos z Eteru**:",
                description=f"{success_translation}",
                color=self.eter_color
            )
            await ctx.respond(embed=embed_message)

    @slash_command(
        name="get-oponents-of-bot",
        guild_ids=LEGIT_SERVERS,
        description="[Admin command]: get players who played with bot"
    )
    async def get_oponenets_of_bot(self, ctx, name: Option(str, "Enter a bot name")):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            bot_name = name.lower().strip()

            if bot_name not in self.bot_names:
                not_found = self.translation.translate("ADMINS.NOT_FOUND_BOT")

                embed_message = discord.Embed(
                    title="**Głos z Eteru**",
                    description=not_found,
                    color=self.eter_color
                )

                await ctx.respond(embed=embed_message)

                return

            oponenets = ",".join(read_file_lines(f"./localLogs/oko/{bot_name}.txt")).replace("\n", "")

            if not oponenets:
                oponents_not_founded = self.translation.translate("ADMINS.NOT_FOUNDED_OPONENTS",
                                                                  [{"bot_name": bot_name.capitalize()}])

                embed_message = discord.Embed(
                    title="**Głos z Eteru**",
                    description=oponents_not_founded,
                    color=self.eter_color
                )

                await ctx.respond(embed=embed_message)
            else:
                oponents_founded = \
                    self.translation.translate("ADMINS.FOUNDED_OPONENTS", [{"bot_name": bot_name.capitalize()}, {"values": oponenets}])

                embed_message = discord.Embed(
                    title="**Głos z Eteru**",
                    description=oponents_founded,
                    color=self.eter_color
                )

                await ctx.respond(embed=embed_message)

    @slash_command(
        name="clean-logs",
        guild_ids=LEGIT_SERVERS,
        description="[Admin command]: it cleans logs! DONT DO IT IF U'RE NOT SURE!!"
    )
    async def clean_logs(self, ctx):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            try:
                with open("./localLogs/oko/eye-game-logs.txt", "w"):
                    pass
            except FileNotFoundError:
                print("[RESET LOGS]: lack of file eye-game-logs.txt")
                return
            except IOError as e:
                print(f"[RESET LOGS]: An unexpected error occurred: {e}")
                return

            success_translation = self.translation.translate("ADMINS.RESET_LOGS_SUCCESSFULLY_PASSED")

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=success_translation,
                color=self.eter_color
            )

            await ctx.respond(embed=embed_message)

    @slash_command(name="get-bot-full-logs", guild_ids=LEGIT_SERVERS, description="[Admin command]: get logs file")
    async def get_logs_full(self, ctx):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            path_to_logs = "./localLogs/oko/eye-game-logs.txt"

            file = discord.File(path_to_logs, filename="eye-game-logs.txt")

            here_are_logs = self.translation.translate("ADMINS.LOGS_FILE")

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=here_are_logs,
                color=self.eter_color
            )

            await ctx.respond(embed=embed_message, file=file)

    @slash_command(name="get-bot-sumup-logs", guild_ids=LEGIT_SERVERS,
                   description="[Admin command]: get sumup log file")
    async def get_logs_sumup(self, ctx):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            path_to_logs = "./localLogs/oko/eye-game-sumup-logs.txt"

            file = discord.File(path_to_logs, filename="eye-game-sumup-logs.txt")

            here_are_logs = self.translation.translate("ADMINS.LOGS_FILE")

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=here_are_logs,
                color=self.eter_color
            )

            await ctx.respond(embed=embed_message, file=file)

    @slash_command(name="reset-sumup-logs", guild_ids=LEGIT_SERVERS,
                   description="[Admin command]: it cleans sumup logs! DONT DO IT IF U'RE NOT SURE!!")
    async def clean_logs(self, ctx):
        if self.__id_admin_and_channel_valid(ctx.author.roles, ctx.channel):
            try:
                with open("./localLogs/oko/eye-game-sumup-logs.txt", "w"):
                    pass
            except FileNotFoundError:
                print(f"[RESET LOGS]: lack of file eye-game-sumup-logs.txt")
                return
            except IOError as e:
                print(f"[RESET LOGS]: An unexpected error occurred: {e}")
                return

            success_translation = self.translation.translate("ADMINS.RESET_LOGS_SUCCESSFULLY_PASSED")

            path_to_log = "./imgs/log.jpg"

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=success_translation,
                color=self.eter_color
            )
            embed_message.set_image(url="attachment://log.jpg")
            file = discord.File(path_to_log, filename="log.jpg")

            await ctx.respond(embed=embed_message, file=file)

    def __id_admin_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.allowed_id_roles) \
               and channel.id in self.admin_channel_allowed_to_use_ids

