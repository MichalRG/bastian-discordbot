import random
from typing import List

import discord

from services.config import Config
from services.translation import Translation


class Welcome:
    def __init__(self, config=None):
        self.config = config or Config()
        self.translate_service = Translation()

    async def welcome_guests(self, channel):
        await self.__send_welcome_message(channel)

        games_we_play = await self.__send_game_proposal(channel)

        if games_we_play:
            await self.__send_rules_for_active_games(games_we_play, channel)

    async def __send_welcome_message(self, channel):
        if self.config.get_process_permissions_for_section("welcome.come_in"):
            welcome_messages = self.translate_service.translate("WELCOME.SAY_HELLO")

            chosen_message = welcome_messages

            # TEST APPROACH EXPERIMENTAL WITH EMBEDED
            embed = discord.Embed(title="Kajuta Hazardzistów Wita!", description=chosen_message,
                                  color=0x47bbd6)
            embed.set_image(url="attachment://KajutaHazardzistow.png")
            # embed.set_thumbnail(url="attachment://KajutaHazardzistow.png")
            file = discord.File("./imgs/KajutaHazardzistow.png", filename="KajutaHazardzistow.png")
            await channel.send(file=file, embed=embed)

            # NEW APPROACh
            # await channel.send("", file=discord.File("./imgs/KajutaHazardzistow.png", description="Kajuta Hazardzistów Wita!"))
            # await channel.send(chosen_message)

            # LEGACY APPROACH
            # await channel.send(f"{chosen_message}",
            #                    file=discord.File("./imgs/bastianWelcome.png", description="Bastian"))

    async def __send_game_proposal(self, channel) -> List:
        if not self.config.get_process_permissions_for_section("welcome.games"):
            return

        games_which_we_play = []
        proposal_message = self.translate_service.translate("WELCOME.PROPOSAL_GENERAL_MESSAGE")

        if self.config.get_process_permissions_for_section("welcome.games.eye"):
            proposal_message += self.translate_service.translate("WELCOME.EYE.TITLE")
            games_which_we_play.append("eye")

        if not games_which_we_play:
            proposal_message += self.translate_service.translate("WELCOME.PLAY_NOTHING")

        await channel.send(f"**Bastian:**\n{proposal_message}",
                           file=discord.File("./imgs/bastianAtTable.png", description="Bastian"))

        return games_which_we_play

    async def __send_rules_for_active_games(self, games_we_play: List, channel):
        rule_message = "**Bastian:**\n"
        if "eye" in games_we_play:
            rule_message += self.__add_eye_text()

        await channel.send(rule_message)

    def __add_eye_text(self) -> str:
        eye_rule = self.translate_service.translate("WELCOME.EYE.RULES")
        eye_example = self.translate_service.translate("WELCOME.EYE.EXAMPLE")
        eye_usage = self.translate_service.translate("WELCOME.EYE.MECHANIC_SHOW_PLAYERS")

        return f"{eye_rule}\n{eye_example}\n{eye_usage}\n\n"
