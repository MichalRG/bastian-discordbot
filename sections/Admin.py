from discord import slash_command, Object
from discord.ext import commands

from helpers.constants import LEGIT_SERVERS
from services.general_utils import role_and_channel_valid


class AdminCommands(commands.Cog):
    def __init__(self, bot_client, channels, roles):
        self.client = bot_client
        self.allowed_channels_ids = channels
        self.allowed_roles = roles

    @slash_command(name="sync-bot", guild_ids=LEGIT_SERVERS, description="[Admin commands]: Sync bot commands")
    async def sync_bot_commands(self, ctx):
        data = {
            "author_roles": ctx.author.roles,
            "channel_source": ctx.channel.id,
            "allowed_roles":  self.allowed_role_ids,
            "allowed_channel_ids": self.allowed_channels_ids
        }

        if role_and_channel_valid(data):
            await self.client.tree.sync(guild=Object(id=ctx.guild_id))
            await ctx.respond("Commands synced successfully! 🔄️")

    @slash_command(name="kill-bot-process", guild_ids=LEGIT_SERVERS, description="[Admin command]: Turn off the bot")
    async def kill_bastian(self, ctx):
        data = {
            "author_roles": ctx.author.roles,
            "channel_source": ctx.channel.id,
            "allowed_roles": self.allowed_role_ids,
            "allowed_channel_ids": self.allowed_channels_ids
        }

        if role_and_channel_valid(data):
            exit(0)
