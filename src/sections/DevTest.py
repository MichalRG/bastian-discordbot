import discord
from discord import slash_command
from discord.ext import commands

from src.helpers.constants import LEGIT_SERVERS


class DevTestCommands(commands.Cog):
    @slash_command(name="test", guild_ids=LEGIT_SERVERS, description="tatka tam")
    # @commands.has_role(1195438414951104522)
    async def taka_tam(self, ctx, arg):
        if ctx.author.id == 688301052033761282:
            await ctx.respond(arg)
            knownrole = discord.utils.get(ctx.guild.roles, name="czatownik")
            await ctx.author.add_roles(knownrole)