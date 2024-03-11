import discord
from discord import slash_command
from discord.ext import commands

from src.helpers.constants import LEGIT_SERVERS
from src.services.Translation import Translation


class GeneralEyeCommands(commands.Cog):
    def __init__(self, translation, roles, channels):
        self.translation = translation or Translation()
        # TODO: Consider to not reply just use this channels or in this game just single channel
        self.allowed_channels = channels
        self.allowed_channels_ids = [channel.id for channel in channels]
        self.allowed_id_roles = roles
        self.color = 0x000000

    @slash_command(name="oko-pomoc", guild_ids=LEGIT_SERVERS, description="Sprawdź dostępne komendy do gry w oko")
    async def available_commands(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel):
            rules = self.translation.translate("WELCOME.EYE.RULES")
            commands = self.translation.translate("GAMES.EYE.HELP_COMMANDS")

            embed_message = discord.Embed(
                title="**Głos z Eteru**",
                description=f"{rules}\n\n{commands}",
                color=self.color
            )

            await ctx.respond(embed=embed_message)

    def __role_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.allowed_id_roles) and \
               channel.id in self.allowed_channels_ids

