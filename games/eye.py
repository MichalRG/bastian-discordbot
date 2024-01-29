from datetime import datetime
import random
import uuid
from typing import List

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from helpers.constants import LEGIT_SERVERS
from services.config import Config
from services.general_utils import write_to_game_logs, read_file_lines
from services.translation import Translation


class EyeGame(commands.Cog):
    def __init__(self, config, translation, roles, channels):
        self.config = config or Config()
        self.translation = translation or Translation()
        self.allowed_channels = channels  # TODO: Consider to not reply just use this channels or in this game just single channel
        self.allowed_channels_names = [channel.name for channel in channels]
        self.allowed_roles = roles
        self.GENERAL_COMMANDS = self.translation.translate("GAMES.EYE.GENERAL_COMMANDS")
        self.blacklisted_by_Rupella = None

        self.__define_player_statuses()

    def __define_player_statuses(self):
        players = self.config.get_config_key("games.eye.players")

        gerald = players.get("Gerald Berchtold", {"process": False, "many_games": False})
        liebwin = players.get("Liebwin Müller", {"process": False, "many_games": False})
        guerino = players.get("Guerino Wessely", {"process": False, "many_games": False})
        amalberg = players.get("Amalberga Auerswald", {"process": False, "many_games": False})
        thrognik = players.get("Thrognik Rockson", {"process": False, "many_games": False})

        self.is_not_gerald_busy = gerald.get("process")
        self.is_not_liebwin_busy = liebwin.get("process")
        self.is_not_guerino_busy = guerino.get("process")
        self.is_not_amalberga_busy = amalberg.get("process")
        self.is_not_thrognik_busy = thrognik.get("process")

        self.is_gerald_eager_for_many_games = gerald.get("many_games")
        self.is_liebwin_eager_for_many_games = liebwin.get("many_games")
        self.is_guerino_eager_for_many_games = guerino.get("many_games")
        self.is_amalberg_eager_for_many_games = amalberg.get("many_games")
        self.is_thrognik_eager_for_many_games = thrognik.get("many_games")

    def __get_available_players(self) -> List:
        players = []

        if self.is_not_thrognik_busy:
            players.append("Thrognik Rockson")
        if self.is_not_amalberga_busy:
            players.append("Amalberga Auerswald")
        if self.is_not_gerald_busy:
            players.append("Gerald Berchtold")
        if self.is_not_guerino_busy:
            players.append("Guerino Wessely")
        if self.is_not_liebwin_busy:
            players.append("Liebwin Müller")

        return players

    @slash_command(name="oko-pomoc", guild_ids=LEGIT_SERVERS, description="Sprawdź dostępne komendy do gry w oko")
    async def available_commands(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            rules = self.translation.translate("WELCOME.EYE.RULES")
            commands = self.translation.translate("GAMES.EYE.HELP_COMMANDS")

            await ctx.respond(f"**Głos z Eteru:**\n{rules}\n\n{commands}")

    @slash_command(name="oko-gracze", guild_ids=LEGIT_SERVERS, description="Sprawdź dostępnych graczy")
    async def display_available_player(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            ready_players = self.__get_available_players()

            if not ready_players:
                non_available = self.translation.translate("GAMES.EYE.AVAILABLE_PLAYERS.NON")

                await ctx.respond(f"**Bastian:**\n{non_available}")

                return

            base_response = self.translation.translate("GAMES.EYE.AVAILABLE_PLAYERS.MESSAGE")
            concatenated_players = ", ".join(ready_players)
            rule_to_challenge = self.translation.translate("GAMES.EYE.AVAILABLE_PLAYERS.CHALLENGE_PLAYER")

            await ctx.respond(f"**Bastian:**\n{base_response}{concatenated_players}.\n{rule_to_challenge}")

    @slash_command(name="wyzwij-thrognik", guild_ids=LEGIT_SERVERS, description="Wyzwij Thrognika na potyczkę w Oko")
    async def challenge_thrognik(self, ctx, number: Option(int, "Enter a number")):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if await self.__is_rupella_in_action(ctx):
                return

            if not self.is_not_thrognik_busy:
                await self.__display_lack_of_player(ctx, "Thrognika")
                return

            banned = self.__read_blacklist_players("thrognik")
            if str(ctx.author.id) in banned and not self.is_thrognik_eager_for_many_games:
                we_played_log = self.translation.translate("GAMES.EYE.THROGNIK.WE_PLAYED")
                await ctx.respond(f"**Thrognik:**\n{we_played_log}")
                return

            if 25 < number < 41:
                self.is_not_thrognik_busy = False
                self.thrognik_bid = number
                self.id_thrognik_game = uuid.uuid4()
                self.thrognik_enemy_id = ctx.author.id
                self.player_thrognik_dices = 1
                self.thrognik_dices = 1
                self.thrognik_game_strategy = random.randint(2, 3)

                thrognik_initiative, player_initiative = self.__roll_initiative()
                self.__generate_initiative_log({
                    "id_game": self.id_thrognik_game,
                    "bot": "thrognik",
                    "player": ctx.author,
                    "bot_initiative": thrognik_initiative,
                    "player_initiative": player_initiative,
                    "bot_strategy": self.thrognik_game_strategy,
                    "bid": number
                })

                beginning_of_game_thrognik = self.translation.translate(
                    "GAMES.EYE.THROGNIK.START",
                    [
                        {"bot_value": thrognik_initiative},
                        {"player_value": player_initiative},
                        {"player_name": ctx.author.display_name}
                    ])
                await ctx.respond(f"**Głos z eteru:**\n{beginning_of_game_thrognik}")

                if thrognik_initiative < player_initiative:
                    await self.__thrognik_draw_die(ctx)
                else:
                    await ctx.respond(f"{self.GENERAL_COMMANDS}")
            elif isinstance(number, int):
                await self.__display_wrong_thresold_message(
                    ctx=ctx,
                    name="thrognik",
                    lower_limit=26,
                    upper_limit=40,
                    bid=number
                )

    @slash_command(name="wyzwij-guerino", guild_ids=LEGIT_SERVERS, description="Wyzwij Guerino na potyczkę w Oko")
    async def challenge_guerino(self, ctx, number: Option(int, "Enter a number")):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if await self.__is_rupella_in_action(ctx):
                return

            if not self.is_not_guerino_busy:
                await self.__display_lack_of_player(ctx, "Guerino")
                return

            banned = self.__read_blacklist_players("guerino")
            if str(ctx.author.id) in banned and not self.is_guerino_eager_for_many_games:
                we_played_log = self.translation.translate("GAMES.EYE.GUERINO.WE_PLAYED")
                await ctx.respond(f"**Guerino:**\n{we_played_log}")
                return

            if number == 1:
                self.is_not_guerino_busy = False
                self.guerino_bid = number
                self.id_guerino_game = uuid.uuid4()
                self.guerino_enemy_id = ctx.author.id
                self.player_guerino_dices = 1
                self.guerino_dices = 1
                self.guerino_game_strategy = random.randint(1, 2)

                guerino_initiative, player_initiative = self.__roll_initiative()
                self.__generate_initiative_log({
                    "id_game": self.id_guerino_game,
                    "bot": "guerino",
                    "player": ctx.author,
                    "bot_initiative": guerino_initiative,
                    "player_initiative": player_initiative,
                    "bot_strategy": self.guerino_game_strategy,
                    "bid": number
                })

                beginning_of_game_guerino = self.translation.translate(
                    "GAMES.EYE.GUERINO.START",
                    [
                        {"bot_value": guerino_initiative},
                        {"player_value": player_initiative},
                        {"player_name": ctx.author.display_name}
                    ])
                await ctx.respond(f"**Głos z eteru:**\n{beginning_of_game_guerino}")

                if guerino_initiative < player_initiative:
                    if self.guerino_game_strategy > 1:
                        await self.__guerino_draw_die(ctx)
                    else:
                        results = await self.__perform_roll(
                            self.guerino_dices,
                            ctx,
                            "Guerino"
                        )

                        if "9" in results:
                            self.__save_winning_log({
                                "id_game": self.id_guerino_game,
                                "roller": "guerino",
                                "result": results
                            })
                            victory_guerino_log = self.translation.translate("GAMES.EYE.GUERINO.VICTORY")

                            await ctx.respond(f"**Guerino:**\n{victory_guerino_log}")

                            self.__add_to_already_played_file({
                                "bot": "guerino",
                                "player": ctx.author.id
                             })
                            self.is_not_guerino_busy = True
                        else:
                            self.__save_roll_log({
                                "id_game": self.id_guerino_game,
                                "roller": "guerino",
                                "result": results
                            })
                            failure_guerino_log = self.translation.translate("GAMES.EYE.GUERINO.FAIL")

                            await ctx.respond(f"**Guerino:**\n{failure_guerino_log}")
                else:
                    await ctx.respond(f"{self.GENERAL_COMMANDS}")

            elif isinstance(number, int):
                await self.__display_wrong_thresold_message(
                    ctx=ctx,
                    name="guerino",
                    lower_limit=1,
                    upper_limit=1,
                    bid=number
                )

    @slash_command(name="wyzwij-liebwin", guild_ids=LEGIT_SERVERS, description="Wyzwij Liebwina na potyczkę w Oko")
    async def challenge_liebwin(self, ctx, number: Option(int, "Enter a number")):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if await self.__is_rupella_in_action(ctx):
                return

            if not self.is_not_liebwin_busy:
                await self.__display_lack_of_player(ctx, "Liebwina")
                return

            banned = self.__read_blacklist_players("liebwin")
            if str(ctx.author.id) in banned and not self.is_liebwin_eager_for_many_games:
                we_played_log = self.translation.translate("GAMES.EYE.LIEBWIN.WE_PLAYED")
                await ctx.respond(f"**Liebwin:**\n{we_played_log}")
                return

            if 1 < number < 10:
                self.is_not_liebwin_busy = False
                self.liebwin_bid = number
                self.id_liebwin_game = uuid.uuid4()
                self.liebwin_enemy_id = ctx.author.id
                self.player_liebwin_dices = 1
                self.liebwin_dices = 1
                self.liebwin_game_strategy = random.randint(1, 3)

                liebwin_initiative, player_initiative = self.__roll_initiative()
                self.__generate_initiative_log({
                    "id_game": self.id_liebwin_game,
                    "bot": "liebwin",
                    "player": ctx.author,
                    "bot_initiative": liebwin_initiative,
                    "player_initiative": player_initiative,
                    "bot_strategy": self.liebwin_game_strategy,
                    "bid": number
                })

                beginning_of_game_liebwin = self.translation.translate(
                    "GAMES.EYE.LIEBWIN.START",
                    [
                        {"bot_value": liebwin_initiative},
                        {"player_value": player_initiative},
                        {"player_name": ctx.author.display_name}
                    ])
                await ctx.respond(f"**Głos z eteru:**\n{beginning_of_game_liebwin}")

                if liebwin_initiative < player_initiative:
                    if self.liebwin_game_strategy > 1:
                        await self.__liebwin_draw_die(ctx)
                    else:
                        results = await self.__perform_roll(
                            self.liebwin_dices,
                            ctx,
                            "Liebwin"
                        )

                        if "9" in results:
                            self.__save_winning_log({
                                "id_game": self.id_liebwin_game,
                                "roller": "liebwin",
                                "result": results
                            })
                            victory_liebwin_log = self.translation.translate("GAMES.EYE.LIEBWIN.VICTORY")

                            await ctx.respond(f"**Liebwin:**\n{victory_liebwin_log}")

                            self.__add_to_already_played_file({
                                "bot": "liebwin",
                                "player": ctx.author.id
                            })
                            self.is_not_liebwin_busy = True
                        else:
                            self.__save_roll_log({
                                "id_game": self.id_liebwin_game,
                                "roller": "liebwin",
                                "result": results
                            })
                            faiulre_liebwin_log = self.translation.translate("GAMES.EYE.LIEBWIN.FAIL")

                            await ctx.respond(f"**Liebwin:**\n{faiulre_liebwin_log}")
                else:
                    await ctx.respond(f"{self.GENERAL_COMMANDS}")
            elif isinstance(number, int):
                await self.__display_wrong_thresold_message(
                    ctx=ctx,
                    name="liebwin",
                    lower_limit=1,
                    upper_limit=9,
                    bid=number
                )

    @slash_command(name="wyzwij-gerald", guild_ids=LEGIT_SERVERS, description="Wyzwij Geralda na potyczkę w Oko")
    async def challenge_gerald(self, ctx, number: Option(int, "Enter a number")):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if await self.__is_rupella_in_action(ctx):
                return

            if not self.is_not_gerald_busy:
                await self.__display_lack_of_player(ctx, "Geralda")
                return

            banned = self.__read_blacklist_players("gerald")
            if str(ctx.author.id) in banned and not self.is_gerald_eager_for_many_games:
                we_played_log = self.translation.translate("GAMES.EYE.GERALD.WE_PLAYED")
                await ctx.respond(f"**Gerald:**\n{we_played_log}")
                return

            if 9 < number < 26:
                self.is_not_gerald_busy = False
                self.gerald_bid = number
                self.id_gerald_game = uuid.uuid4()
                self.gerald_enemy_id = ctx.author.id
                self.player_gerald_dices = 1
                self.gerald_dices = 1
                self.gerald_game_strategy = random.randint(2, 4)

                gerald_initiative, player_initiative = self.__roll_initiative()
                self.__generate_initiative_log({
                    "id_game": self.id_gerald_game,
                    "bot": "gerald",
                    "player": ctx.author,
                    "bot_initiative": gerald_initiative,
                    "player_initiative": player_initiative,
                    "bot_strategy": self.gerald_game_strategy,
                    "bid": number
                })

                beginning_of_game_gerald = self.translation.translate(
                    "GAMES.EYE.GERALD.START",
                    [
                        {"bot_value": gerald_initiative},
                        {"player_value": player_initiative},
                        {"player_name": ctx.author.display_name}
                    ])
                await ctx.respond(f"**Głos z eteru:**\n{beginning_of_game_gerald}")

                if gerald_initiative < player_initiative:
                    await self.__gerald_draw_die(ctx)
                else:
                    await ctx.respond(f"{self.GENERAL_COMMANDS}")
            elif isinstance(number, int):
                await self.__display_wrong_thresold_message(
                    ctx=ctx,
                    name="gerald",
                    lower_limit=10,
                    upper_limit=25,
                    bid=number
                )

    @slash_command(name="wyzwij-amalberg", guild_ids=LEGIT_SERVERS, description="Wyzwij Amalberg na potyczkę w Oko")
    async def challenge_amalberg(self, ctx, number: Option(int, "Enter a number")):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if await self.__is_rupella_in_action(ctx):
                return

            if not self.is_not_amalberga_busy:
                await self.__display_lack_of_player(ctx, "Amalbergi")
                return

            banned = self.__read_blacklist_players("amalberg")
            if str(ctx.author.id) in banned and not self.is_amalberg_eager_for_many_games:
                we_played_log = self.translation.translate("GAMES.EYE.AMALBERG.WE_PLAYED")
                await ctx.respond(f"**Amalberg:**\n{we_played_log}")
                return

            if 19 < number < 30:
                self.is_not_amalberga_busy = False
                self.amalberg_bid = number
                self.id_amalberg_game = uuid.uuid4()
                self.amalberg_enemy_id = ctx.author.id
                self.player_amalberg_dices = 1
                self.amalberg_dices = 1
                self.amalberg_game_strategy = random.randint(3, 4)

                amalberg_initiative, player_initiative = self.__roll_initiative()
                self.__generate_initiative_log({
                    "id_game": self.id_amalberg_game,
                    "bot": "amalberg",
                    "player": ctx.author,
                    "bot_initiative": amalberg_initiative,
                    "player_initiative": player_initiative,
                    "bot_strategy": self.amalberg_game_strategy,
                    "bid": number
                })

                beginning_of_game_amalberg = self.translation.translate(
                    "GAMES.EYE.AMALBERG.START",
                    [
                        {"bot_value": amalberg_initiative},
                        {"player_value": player_initiative},
                        {"player_name": ctx.author.display_name}
                    ])
                await ctx.respond(f"**Głos z eteru:**\n{beginning_of_game_amalberg}")

                if amalberg_initiative < player_initiative:
                    await self.__amalberg_draw_die(ctx)
                else:
                    await ctx.respond(f"{self.GENERAL_COMMANDS}")
            elif isinstance(number, int):
                await self.__display_wrong_thresold_message(
                    ctx=ctx,
                    name="amalberg",
                    lower_limit=20,
                    upper_limit=29,
                    bid=number
                )

    @slash_command(name="oko-dobieram-thrognik", guild_ids=LEGIT_SERVERS,
                   description="Dobierz kość w grze z Thrognikiem")
    async def player_draw_die_in_thrognik_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_thrognik_busy or (not self.is_not_thrognik_busy and self.thrognik_enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_thrognik_dices += 1

            self.__save_draw_log({
                "id_game": self.id_thrognik_game,
                "bot": ctx.author.display_name,
                "amount": self.player_thrognik_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER", [{"amount": str(self.player_thrognik_dices)}])

            await ctx.respond(f"**Głos z Eteru:**\n{draw_response}")

            await self.__perform_thrognik_action(ctx)

    @slash_command(name="oko-rzucam-thrognik", guild_ids=LEGIT_SERVERS,
                   description="Wykonaj rzut w grze z Thrognikiem")
    async def player_roll_dices_in_thrognik_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_thrognik_busy or (not self.is_not_thrognik_busy and self.thrognik_enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_thrognik_roll_result = await self.__perform_roll(self.player_thrognik_dices, ctx, ctx.author.display_name)

            self.__save_roll_log({
                "id_game": self.id_thrognik_game,
                "roller": ctx.author.display_name,
                "result": player_thrognik_roll_result
            })

            if "9" in player_thrognik_roll_result:
                self.__save_winning_log({
                    "id_game": self.id_thrognik_game,
                    "roller": ctx.author.display_name,
                    "result": player_thrognik_roll_result
                })

                thrognik_reaction = self.translation.translate("GAMES.EYE.THROGNIK.REACTION_ON_SUCCESS_PLAYER")
                await ctx.respond(f"**Thrognik:**\n{thrognik_reaction}")

                self.__add_to_already_played_file({
                    "bot": "thrognik",
                    "player": ctx.author.id
                })
                self.is_not_thrognik_busy = True
            else:
                thrognik_reaction = self.translation.translate("GAMES.EYE.THROGNIK.REACTION_ON_FAIL_PLAYER")
                await ctx.respond(f"**Thrognik:**\n{thrognik_reaction}")

                await self.__perform_thrognik_action(ctx)

    async def __perform_thrognik_action(self, ctx):
        if self.thrognik_dices >= self.thrognik_game_strategy:
            await self.__thrognik_roll_dices(ctx)
        else:
            await self.__thrognik_draw_die(ctx)

    async def __thrognik_draw_die(self, ctx):
        self.thrognik_dices += 1

        draw_thrognik = self.translation.translate('GAMES.EYE.THROGNIK.DRAW', [{"dices": str(self.thrognik_dices)}])
        await ctx.respond(f"**Thrognik:**\n{draw_thrognik}\n{self.GENERAL_COMMANDS}")

        self.__save_draw_log({
            "id_game": self.id_thrognik_game,
            "bot": "Thrognik",
            "current_amount": self.thrognik_dices
        })

    async def __thrognik_roll_dices(self, ctx):
        results = await self.__perform_cheat_roll(
            self.thrognik_dices,
            ctx
        )

        if "9" in results:
            self.__save_winning_log({
                "id_game": self.id_thrognik_game,
                "roller": "thrognik",
                "result": results
            })
            victory_thrognik_log = self.translation.translate("GAMES.EYE.THROGNIK.VICTORY")

            await ctx.respond(f"**Thrognik:**\n{victory_thrognik_log}")

            self.__add_to_already_played_file({
                "bot": "thrognik",
                "player": ctx.author.id
            })
            self.is_not_thrognik_busy = True
        else:
            self.__save_roll_log({
                "id_game": self.id_thrognik_game,
                "roller": "thrognik",
                "result": results
            })
            faiulre_thrognik_log = self.translation.translate("GAMES.EYE.THROGNIK.FAIL")

            await ctx.respond(f"**Thrognik:**\n{faiulre_thrognik_log}\n{self.GENERAL_COMMANDS}")

    @slash_command(name="oko-dobieram-gerald", guild_ids=LEGIT_SERVERS, description="Dobierz kość w grze z Geraldem")
    async def player_draw_die_in_gerald_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_gerald_busy or (not self.is_not_gerald_busy and self.gerald_enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_gerald_dices += 1

            self.__save_draw_log({
                "id_game": self.id_gerald_game,
                "bot": ctx.author.display_name,
                "amount": self.player_gerald_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER", [{"amount": str(self.player_gerald_dices)}])

            await ctx.respond(f"**Głos z Eteru:**\n{draw_response}")

            await self.__perform_gerald_action(ctx)

    @slash_command(name="oko-rzucam-gerald", guild_ids=LEGIT_SERVERS,
                   description="Wykonaj rzut w grze z Geraldem")
    async def player_roll_dices_in_gerald_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_gerald_busy or (not self.is_not_gerald_busy and self.gerald_enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_gerald_roll_result = await self.__perform_roll(self.player_gerald_dices, ctx, ctx.author.display_name)

            self.__save_roll_log({
                "id_game": self.id_gerald_game,
                "roller": ctx.author.display_name,
                "result": player_gerald_roll_result
            })

            if "9" in player_gerald_roll_result:
                self.__save_winning_log({
                    "id_game": self.id_gerald_game,
                    "roller": ctx.author.display_name,
                    "result": player_gerald_roll_result
                })

                gerald_reaction = self.translation.translate("GAMES.EYE.GERALD.REACTION_ON_SUCCESS_PLAYER")
                await ctx.respond(f"**Gerald:**\n{gerald_reaction}")

                self.__add_to_already_played_file({
                    "bot": "gerald",
                    "player": ctx.author.id
                })
                self.is_not_gerald_busy = True
            else:
                gerald_reaction = self.translation.translate("GAMES.EYE.GERALD.REACTION_ON_FAIL_PLAYER")
                await ctx.respond(f"**Gerald:**\n{gerald_reaction}")

                await self.__perform_gerald_action(ctx)

    async def __perform_gerald_action(self, ctx):
        if self.gerald_dices >= self.gerald_game_strategy:
            await self.__gerald_roll_dices(ctx)
        else:
            await self.__gerald_draw_die(ctx)

    async def __gerald_draw_die(self, ctx):
        self.gerald_dices += 1

        draw_gerald = self.translation.translate('GAMES.EYE.GERALD.DRAW', [{"dices": str(self.gerald_dices)}])
        await ctx.respond(f"**Gerald:**\n{draw_gerald}\n{self.GENERAL_COMMANDS}")

        self.__save_draw_log({
            "id_game": self.id_gerald_game,
            "bot": "gerald",
            "current_amount": self.gerald_dices
        })

    async def __gerald_roll_dices(self, ctx):
        results = await self.__perform_roll(
            self.gerald_dices,
            ctx,
            "Gerald"
        )

        if "9" in results:
            self.__save_winning_log({
                "id_game": self.id_gerald_game,
                "roller": "gerald",
                "result": results
            })
            victory_gerald_log = self.translation.translate("GAMES.EYE.GERALD.VICTORY")

            await ctx.respond(f"**Gerald:**\n{victory_gerald_log}")

            self.__add_to_already_played_file({
                "bot": "gerald",
                "player": ctx.author.id
            })
            self.is_not_gerald_busy = True
        else:
            self.__save_roll_log({
                "id_game": self.id_gerald_game,
                "roller": "gerald",
                "result": results
            })
            failure_gerald_log = self.translation.translate("GAMES.EYE.GERALD.FAIL")

            await ctx.respond(f"**Gerald:**\n{failure_gerald_log}\n{self.GENERAL_COMMANDS}")

    @slash_command(name="oko-dobieram-amalberg", guild_ids=LEGIT_SERVERS, description="Dobierz kość w grze z Amalberg")
    async def player_draw_die_in_amalberg_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_amalberga_busy or (not self.is_not_amalberga_busy and self.amalberg_enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_amalberg_dices += 1

            self.__save_draw_log({
                "id_game": self.id_amalberg_game,
                "bot": ctx.author.display_name,
                "amount": self.player_amalberg_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER", [{"amount": str(self.player_amalberg_dices)}])

            await ctx.respond(f"**Głos z Eteru:**\n{draw_response}")

            await self.__perform_amalberg_action(ctx)

    @slash_command(name="oko-rzucam-amalberg", guild_ids=LEGIT_SERVERS,
                   description="Wykonaj rzut w grze z Amalberg")
    async def player_roll_dices_in_amalberg_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_amalberga_busy or (not self.is_not_amalberga_busy and self.amalberg_enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_amalberg_roll_result = await self.__perform_roll(self.player_amalberg_dices, ctx, ctx.author.display_name)

            self.__save_roll_log({
                "id_game": self.id_amalberg_game,
                "roller": ctx.author.display_name,
                "result": player_amalberg_roll_result
            })

            if "9" in player_amalberg_roll_result:
                self.__save_winning_log({
                    "id_game": self.id_amalberg_game,
                    "roller": ctx.author.display_name,
                    "result": player_amalberg_roll_result
                })

                amalberg_reaction = self.translation.translate("GAMES.EYE.AMALBERG.REACTION_ON_SUCCESS_PLAYER")
                await ctx.respond(f"**Amalberg:**\n{amalberg_reaction}")

                self.__add_to_already_played_file({
                    "bot": "amalberg",
                    "player": ctx.author.id
                })
                self.is_not_amalberga_busy = True
            else:
                amalberg_reaction = self.translation.translate("GAMES.EYE.AMALBERG.REACTION_ON_FAIL_PLAYER")
                await ctx.respond(f"**Amalberg:**\n{amalberg_reaction}")

                await self.__perform_amalberg_action(ctx)

    async def __perform_amalberg_action(self, ctx):
        if self.amalberg_dices >= self.amalberg_game_strategy:
            await self.__amalberg_roll_dices(ctx)
        else:
            await self.__amalberg_draw_die(ctx)

    async def __amalberg_draw_die(self, ctx):
        self.amalberg_dices += 1

        draw_amalberg = self.translation.translate('GAMES.EYE.AMALBERG.DRAW', [{"dices": str(self.amalberg_dices)}])
        await ctx.respond(f"**Głos z Eteru:**\n{draw_amalberg}\n{self.GENERAL_COMMANDS}")

        self.__save_draw_log({
            "id_game": self.id_amalberg_game,
            "bot": "alamberg",
            "current_amount": self.amalberg_dices
        })

    async def __amalberg_roll_dices(self, ctx):
        results = await self.__perform_roll(
            self.amalberg_dices,
            ctx,
            "Amalberg"
        )

        if "9" in results:
            self.__save_winning_log({
                "id_game": self.id_amalberg_game,
                "roller": "amalberg",
                "result": results
            })
            victory_amalberg_log = self.translation.translate("GAMES.EYE.AMALBERG.VICTORY")

            await ctx.respond(f"**Amalberg:**\n{victory_amalberg_log}")

            self.__add_to_already_played_file({
                "bot": "amalberg",
                "player": ctx.author.id
            })
            self.is_not_amalberga_busy = True
        else:
            self.__save_roll_log({
                "id_game": self.id_amalberg_game,
                "roller": "amalberg",
                "result": results
            })
            failure_amalberg_log = self.translation.translate("GAMES.EYE.AMALBERG.FAIL")

            await ctx.respond(f"**Amalberg:**\n{failure_amalberg_log}\n{self.GENERAL_COMMANDS}")

    @slash_command(name="oko-dobieram-liebwin", guild_ids=LEGIT_SERVERS, description="Dobierz kość w grze z Liebwinem")
    async def player_draw_die_in_liebwin_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_liebwin_busy or (not self.is_not_liebwin_busy and self.liebwin_enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_liebwin_dices += 1

            self.__save_draw_log({
                "id_game": self.id_liebwin_game,
                "bot": ctx.author.display_name,
                "amount": self.player_liebwin_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER", [{"amount": str(self.player_liebwin_dices)}])

            await ctx.respond(f"**Głos z Eteru:**\n{draw_response}")

            await self.__perform_liebwin_action(ctx)

    @slash_command(name="oko-rzucam-liebwin", guild_ids=LEGIT_SERVERS,
                   description="Wykonaj rzut w grze z Liebwinem")
    async def player_roll_dices_in_liebwin_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_liebwin_busy or (not self.is_not_liebwin_busy and self.liebwin_enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_liebwin_roll_result = await self.__perform_roll(self.player_liebwin_dices, ctx, ctx.author.display_name)

            self.__save_roll_log({
                "id_game": self.id_liebwin_game,
                "roller": ctx.author.display_name,
                "result": player_liebwin_roll_result
            })

            if "9" in player_liebwin_roll_result:
                self.__save_winning_log({
                    "id_game": self.id_liebwin_game,
                    "roller": ctx.author.display_name,
                    "result": player_liebwin_roll_result
                })

                liebwin_reaction = self.translation.translate("GAMES.EYE.LIEBWIN.REACTION_ON_SUCCESS_PLAYER")
                await ctx.respond(f"**Liebwin:**\n{liebwin_reaction}")

                self.__add_to_already_played_file({
                    "bot": "liebwin",
                    "player": ctx.author.id
                })
                self.is_not_liebwin_busy = True
            else:
                liebwin_reaction = self.translation.translate("GAMES.EYE.LIEBWIN.REACTION_ON_FAIL_PLAYER")
                await ctx.respond(f"**Liebwin:**\n{liebwin_reaction}")

                await self.__perform_liebwin_action(ctx)

    async def __perform_liebwin_action(self, ctx):
        if self.liebwin_dices >= self.liebwin_game_strategy:
            await self.__liebwin_roll_dices(ctx)
        else:
            await self.__liebwin_draw_die(ctx)

    async def __liebwin_draw_die(self, ctx):
        self.liebwin_dices += 1

        draw_liebwin = self.translation.translate('GAMES.EYE.LIEBWIN.DRAW', [{"dices": str(self.liebwin_dices)}])
        await ctx.respond(f"**Głos z Eteru:**\n{draw_liebwin}\n{self.GENERAL_COMMANDS}")

        self.__save_draw_log({
            "id_game": self.id_liebwin_game,
            "bot": "liebwin",
            "current_amount": self.liebwin_dices
        })

    async def __liebwin_roll_dices(self, ctx):
        results = await self.__perform_roll(
            self.liebwin_dices,
            ctx,
            "Liebwin"
        )

        if "9" in results:
            self.__save_winning_log({
                "id_game": self.id_liebwin_game,
                "roller": "liebwin",
                "result": results
            })
            victory_liebwin_log = self.translation.translate("GAMES.EYE.LIEBWIN.VICTORY")

            await ctx.respond(f"**Liebwin:**\n{victory_liebwin_log}")

            self.__add_to_already_played_file({
                "bot": "liebwin",
                "player": ctx.author.id
            })
            self.is_not_liebwin_busy = True
        else:
            self.__save_roll_log({
                "id_game": self.id_liebwin_game,
                "roller": "liebwin",
                "result": results
            })
            failure_liebwin_log = self.translation.translate("GAMES.EYE.LIEBWIN.FAIL")

            await ctx.respond(f"**Liebwin:**\n{failure_liebwin_log}\n{self.GENERAL_COMMANDS}")

    @slash_command(name="oko-dobieram-guerino", guild_ids=LEGIT_SERVERS, description="Dobierz kość w grze z Guerino")
    async def player_draw_die_in_guerino_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_guerino_busy or (not self.is_not_guerino_busy and self.guerino_enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_guerino_dices += 1

            self.__save_draw_log({
                "id_game": self.id_guerino_game,
                "bot": ctx.author.display_name,
                "amount": self.player_guerino_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER", [{"amount": str(self.player_guerino_dices)}])

            await ctx.respond(f"**Głos z Eteru:**\n{draw_response}")

            await self.__perform_guerino_action(ctx)

    @slash_command(name="oko-rzucam-guerino", guild_ids=LEGIT_SERVERS,
                   description="Wykonaj rzut w grze z Guerino")
    async def player_roll_dices_in_guerino_game(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel.name):
            if self.is_not_guerino_busy or (not self.is_not_guerino_busy and self.guerino_enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_guerino_roll_result = await self.__perform_roll(self.player_guerino_dices, ctx, ctx.author.display_name)

            self.__save_roll_log({
                "id_game": self.id_guerino_game,
                "roller": ctx.author.display_name,
                "result": player_guerino_roll_result
            })

            if "9" in player_guerino_roll_result:
                self.__save_winning_log({
                    "id_game": self.id_guerino_game,
                    "roller": ctx.author.display_name,
                    "result": player_guerino_roll_result
                })

                guerino_reaction = self.translation.translate("GAMES.EYE.GUERINO.REACTION_ON_SUCCESS_PLAYER")
                await ctx.respond(f"**Guerino:**\n{guerino_reaction}")

                self.__add_to_already_played_file({
                    "bot": "guerino",
                    "player": ctx.author.id
                })
                self.is_not_guerino_busy = True
            else:
                guerino_reaction = self.translation.translate("GAMES.EYE.GUERINO.REACTION_ON_FAIL_PLAYER")
                await ctx.respond(f"**Guerino:**\n{guerino_reaction}")

                await self.__perform_guerino_action(ctx)

    async def __perform_guerino_action(self, ctx):
        if self.guerino_dices >= self.guerino_game_strategy:
            await self.__guerino_roll_dices(ctx)
        else:
            await self.__guerino_draw_die(ctx)

    async def __guerino_draw_die(self, ctx):
        self.guerino_dices += 1

        draw_guerino = self.translation.translate('GAMES.EYE.GUERINO.DRAW', [{"dices": str(self.guerino_dices)}])
        await ctx.respond(f"**Głos z Eteru:**\n{random.choice(draw_guerino)}\n{self.GENERAL_COMMANDS}")

        self.__save_draw_log({
            "id_game": self.id_guerino_game,
            "bot": "guerino",
            "current_amount": self.guerino_dices
        })

    async def __guerino_roll_dices(self, ctx):
        results = await self.__perform_roll(
            self.guerino_dices,
            ctx,
            "Guerino"
        )

        if "9" in results:
            self.__save_winning_log({
                "id_game": self.id_guerino_game,
                "roller": "guerino",
                "result": results
            })
            victory_guerino_log = self.translation.translate("GAMES.EYE.GUERINO.VICTORY")

            await ctx.respond(f"**Guerino:**\n{victory_guerino_log}\n{self.GENERAL_COMMANDS}")

            self.__add_to_already_played_file({
                "bot": "guerino",
                "player": ctx.author.id
            })
            self.is_not_guerino_busy = True
        else:
            self.__save_roll_log({
                "id_game": self.id_guerino_game,
                "roller": "guerino",
                "result": results
            })
            failure_guerino_log = self.translation.translate("GAMES.EYE.GUERINO.FAIL")

            await ctx.respond(f"**Guerino:**\n{failure_guerino_log}")

    async def __display_wrong_thresold_message(self, ctx, name: str, lower_limit: int, upper_limit: int, bid: int):
        if lower_limit > bid:
            not_enough = self.translation.translate(f"GAMES.EYE.{name.upper()}.NOT_ENOUGH")
            await ctx.respond(f"**{name.capitalize()}:**\n{not_enough}")

        elif upper_limit < bid:
            too_much = self.translation.translate(f"GAMES.EYE.{name.upper()}.TOO_MUCH")
            await ctx.respond(f"**{name.capitalize()}:**\n{too_much}")

    async def __display_lack_of_player(self, ctx, name: str):
        lack_of_player = self.translation.translate("GAMES.EYE.LACK_OF_PLAYER", [{"name": name}])
        await ctx.respond(f"**Głos z Eteru:**\n{lack_of_player}")

    def __save_winning_log(self, data):
        id = data.get("id_game", "dupa")
        roller = data.get("roller", "cycki")
        roll_result = data.get("result", [9])

        log = f"[{id}] {datetime.now()}: {roller} won! The result winning roll: {roll_result}"
        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __save_roll_log(self, data):
        id = data.get("id_game", "dupa")
        roller_name = data.get("roller", "cycki")
        roll_result = data.get("result", [9])

        log = f"[{id}] {datetime.now()}: {roller_name} performed its roll! The result roll: {roll_result}"
        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __roll_initiative(self) -> (int, int):
        bot_initiative_roll = 0
        player_initiative_roll = 0

        while bot_initiative_roll == player_initiative_roll:
            bot_initiative_roll, player_initiative_roll = [
                random.randint(1, 10), random.randint(1, 10)
            ]

        return bot_initiative_roll, player_initiative_roll

    async def __perform_roll(self, dices: int, ctx, roller) -> List[str]:
        result = [str(random.randint(1, 10)) for _ in range(dices)]

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT", [{"name": roller},{"result": ", ".join(result)}])

        await ctx.respond(f"**Głos z Eteru:**\n{comment_to_roll_result}")

        return result

    async def __perform_cheat_roll(self, dices: int, ctx) -> List[str]:
        result = [random.randint(1, 14) for _ in range(dices)]

        result = self.__transform_values(result)

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT", [{"name": "Thrognik"}, {"result": ",".join(result)}])

        await ctx.respond(f"**Głos z Eteru:**\n{comment_to_roll_result}")

        return result

    async def __cannot_roll(self, ctx):
        cannot_roll = self.translation.translate("GAMES.EYE.CANNOT_ROLL")
        await ctx.respond(f'**Głos z Eteru:**\n{cannot_roll}')

    async def __cannot_draw(self, ctx):
        cannot_draw = self.translation.translate("GAMES.EYE.CANNOT_DRAW")
        await ctx.respond(f'**Głos z Eteru:**\n{cannot_draw}')

    async def __is_rupella_in_action(self, ctx):
        if str(ctx.author.id) in self.__read_blacklist_of_rupella():
            gtfo = self.translation.translate("GAMES.EYE.RUPELLA.GTFO")
            await ctx.respond(f"**Rupella:**\n{gtfo}")
            return True

        return False

    def __transform_values(self, arr: List[int]) -> List[str]:
        for i in range(len(arr)):
            if 7 <= arr[i] <= 8:
                arr[i] = "7"
            elif 9 <= arr[i] <= 10:
                arr[i] = "8"
            elif 11 <= arr[i] <= 13:
                arr[i] = "9"
            elif arr[i] == 14:
                arr[i] = "10"
            else:
                arr[i] = str(arr[i])
        return arr

    def __generate_initiative_log(self, data):
        id = data.get("id_game", "dupa-id")
        bot = data.get("bot", "cycki")
        player = data.get("player", {"name": "pewno mal"})
        bot_initiative = data.get("bot_initiative", 0)
        player_initiative = data.get("player_initiative", 0)
        bot_strategy = data.get("bot_strategy", "secret")
        bid = data.get("bid", 0)

        log = f"[{id}] {datetime.now()}: {bot} VS {player.name}({player.id}), bid: {bid}, initiative rolls: {bot_initiative}:{player_initiative}, strategy drawing: {bot_strategy}"

        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __save_draw_log(self, data):
        id = data.get("id_game", "dupa-id")
        bot = data.get("bot", "cycki")
        amount = data.get("amount", "current_amount")

        log = f"[{id}] {datetime.now()}: {bot} has drawn a dice, current amount of dice: {amount}"

        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __add_to_already_played_file(self, data_players):
        bot = data_players.get("bot", "solveig")
        player_id = data_players.get("player", "angrist")

        write_to_game_logs(f"oko/{bot}.txt", player_id)

    def __read_blacklist_players(self, bot_name):
        list_of_players = read_file_lines(f"./localLogs/oko/{bot_name}.txt")

        cleaned_list_of_players = [id.strip() for id in list_of_players]

        return cleaned_list_of_players

    def __read_blacklist_of_rupella(self):
        list_of_players = read_file_lines(f"./localLogs/actions/rueplla-blacklist.txt")

        cleaned_list_of_blacklisted_players = [id.strip() for id in list_of_players]

        return cleaned_list_of_blacklisted_players

    def __role_and_channel_valid(self, rolesAuthor, channelName):
        return any(discord.utils.get(rolesAuthor, name=role) for role in self.allowed_roles) and \
               channelName in self.allowed_channels_names

