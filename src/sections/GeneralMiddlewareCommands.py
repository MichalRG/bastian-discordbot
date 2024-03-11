import discord
from discord import slash_command
from discord.ext import commands

from src.helpers.enums.ValidatorsEnum import ValidatorsEnum
from src.services.Config import Config
from src.services.Translation import Translation


class GeneralMiddlewareCommands(commands.Cog):
    def __init__(self, config=Config(), translator=Translation(), eye_observable=None):
        self.config = config
        self.translator = translator
        self.eye_observable = eye_observable
        self.validators = {}

        self.eter_color = 0x000000

    def add_validator(self, key, validator_object):
        self.validators[key] = validator_object

    @slash_command(name="oko-przeciwnicy", description="Wyświetla aktualnie dostępnych graczy w Oko")
    async def show_available_eye_oponenets(self, ctx):
        validator = self.validators.get(ValidatorsEnum.EYE_VALIDATOR)

        if validator and validator.role_and_channel_valid(ctx.author.roles, ctx.channel):
            available_players = self.eye_observable.get_active_eye_bots()

            translated_message = f"{self.translator.translate('GAMES.EYE.AVAILABLE_PLAYERS.MESSAGE')}{', '.join(available_players)}"

            embedded_message = discord.Embed(
                title="**Głogs z eteru**",
                color=self.eter_color,
                description=translated_message
            )

            await ctx.respond(embed=embedded_message)
