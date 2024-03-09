import random
import uuid
from datetime import datetime
from typing import List

import discord

from src.const.paths import LOCAL_LOGS_RUPELLA_BLACKLIST_PATH
from src.services.config import Config
from src.services.general_utils import read_file_lines, write_to_game_logs
from src.services.translation import Translation


class CharacterEye:
    def __init__(
            self,
            name,
            config=Config(),
            translation=Translation(),
            busy=False,
            dice_count=1,
            strategy=None,
            bid=None,
            game_id=None,
            enemy_id=None,
            player_dices=None,
            roles=[],
            channels=[]
    ):
        self.name = name
        self.dice_count = dice_count
        self.strategy = strategy
        self.bid = bid
        self.game_id = game_id
        self.enemy_id = enemy_id
        self.player_dices = player_dices
        self.translation = translation
        self.config = config
        self.allowed_channels_ids = [channel.id for channel in channels]
        self.allowed_id_roles = roles
        self.GENERAL_COMMANDS = self.translation.translate("GAMES.EYE.GENERAL_COMMANDS")
        self.rueplla_color = int(self.config.get_config_key("actions.rupella.rupella_color"), 16)


        self.__define_bot_config_statuses(busy)

    async def challenge(self, ctx, bid: int):
        if not await self.__valid_statuses(ctx):
            return

        if self.lower_bid_threshold <= bid <= self.upper_bid_threshold:
            self.__setup_game(bid, ctx.author.id)

            bot_initiative, player_initiative = self.__roll_initiative()

            self.__generate_initiative_log({
                "player": ctx.author,
                "bot_initiative": bot_initiative,
                "player_initiative": player_initiative,
                "bid": bid
            })

            beginning_of_game_log = self.translation.translate(
                f"GAMES.EYE.{self.name.upper()}.START",
                [
                    {"bot_value": bot_initiative},
                    {"player_value": player_initiative},
                    {"player_name": ctx.author.display_name}
                ])

            message_to_display_text = f"**Głos z eteru:**\n{beginning_of_game_log}"

            if bot_initiative < player_initiative:
                await self.__perform_bot_action(ctx, message_to_display_text)
            else:
                embed = discord.Embed(
                    description=f"{message_to_display_text}\n\n{self.GENERAL_COMMANDS}",
                    color=self.color
                )

                await ctx.respond(embed=embed)
        elif isinstance(bid, int):
            await self.__display_wrong_thresold_message(
                ctx=ctx,
                bid=bid
            )

    async def player_draw_die(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel):
            if not self.busy or (self.busy and self.enemy_id != ctx.author.id):
                await self.__cannot_draw(ctx)
                return

            self.player_dices += 1

            self.__save_draw_log({
                "bot": ctx.author.display_name,
                "amount": self.player_dices
            })

            draw_response = self.translation.translate("GAMES.EYE.DRAW_PLAYER",
                                                       [{"amount": str(self.player_dices)}])

            draw_message = f"**Głos z Eteru:**\n{draw_response}"

            await self.__perform_bot_action(ctx, draw_message)

    async def player_roll_dices(self, ctx):
        if self.__role_and_channel_valid(ctx.author.roles, ctx.channel):
            if not self.busy or (self.busy and self.enemy_id != ctx.author.id):
                await self.__cannot_roll(ctx)
                return

            player_roll_result, roll_result_message = self.__perform_roll(
                self.player_dices,
                ctx.author.display_name
            )

            if "9" in player_roll_result:
                await self.__process_victory(
                    ctx,
                    message_to_send=None,
                    results=player_roll_result,
                    result_roll_message=roll_result_message,
                    is_bot_winner=False
                )
            else:
                self.__save_roll_log({
                    "roller": ctx.author.display_name,
                    "result": player_roll_result
                })

                bot_reaction_message = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.REACTION_ON_FAIL_PLAYER")
                bot_reaction = f"**{self.name.capitalize()}:**\n{bot_reaction_message}"
                message_to_process = f"{roll_result_message}\n\n{bot_reaction}"

                await self.__perform_bot_action(ctx, message_to_process)

    async def __perform_bot_action(self, ctx, message_to_send):
        if self.dice_count >= self.strategy:
            await self.__roll_dices(ctx, message_to_send)
        else:
            await self.__draw_die(ctx, message_to_send)

    async def __draw_die(self, ctx, message_to_send=""):
        self.dice_count += 1

        draw_message = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.DRAW", [{"dices": str(self.dice_count)}])

        embed = discord.Embed(
            description=f"{message_to_send}\n\n"
                        f"**{self.name.capitalize()}:**\n{draw_message}\n{self.GENERAL_COMMANDS}",
            color=self.color
        )

        await ctx.respond(embed=embed)

        self.__save_draw_log({
            "bot": self.name.capitalize,
            "amount": self.dice_count
        })

    async def __roll_dices(self, ctx, message_to_send=""):
        results, result_roll_message = self.__perform_roll(
            self.dice_count,
            self.name.capitalize()
        )

        if "9" in results:
            await self.__process_victory(
                ctx,
                message_to_send=message_to_send,
                results=results,
                result_roll_message=result_roll_message,
                is_bot_winner=True
            )
        else:
            self.__save_roll_log({
                "roller": self.name,
                "result": results
            })

            failure_message = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.FAIL")

            embed = discord.Embed(
                description=f"{message_to_send}\n\n"
                            f"{result_roll_message}\n\n"
                            f"**{self.name.capitalize()}:**\n{failure_message}\n{self.GENERAL_COMMANDS}",
                color=self.color
            )

            await ctx.respond(embed=embed)

    def __perform_roll(self, dices: int, roller) -> (List[str], str):
        if roller == self.name.capitalize() and self.is_cheating:
            result, roll_result_message = self.__cheating_method(dices)
        else:
            result, roll_result_message = self.__perform_fair_roll(dices, roller)

        return result, roll_result_message

    def __add_to_already_played_file(self, data_players):
        player_id = data_players.get("player", "angrist")

        write_to_game_logs(f"oko/{self.name}.txt", player_id)

    def __save_winning_log(self, data):
        roller = data.get("roller", "cycki")
        roll_result = data.get("result", [9])
        loser = data.get("loser", None)
        is_bot_winner = data.get("bot_victory", False)

        loser_part = f" (against {loser})"
        sumup_log_player_info = \
            f"{loser} lost. !remove-coins @{loser}" if is_bot_winner else f"{roller} won. !give-coins @{roller}"
        general_log = f"{roller} won{loser_part}! The result winning roll: {roll_result} (bid: {self.bid})" \

        log = f"[{self.game_id}] {datetime.now()}: {general_log}"
        sumup_log = f"[{self.game_id}] {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}, bid: {self.bid}: {sumup_log_player_info} {self.bid}"
        write_to_game_logs('oko/eye-game-logs.txt', log)
        write_to_game_logs('oko/eye-game-sumup-logs.txt', sumup_log)

    async def __valid_statuses(self, ctx) -> bool:
        if await self.__is_rupella_in_action(ctx):
            return False

        if self.busy and self.enemy_id == ctx.author.id:
            await self.__display_u_play_with_him(ctx)
            return False

        if self.busy:
            await self.__display_lack_of_player(ctx)
            return False

        banned = self.__read_blacklist_players()
        if str(ctx.author.id) in banned and not self.is_bot_eager_for_many_games:
            await self.__display_that_we_already_played(ctx)
            return False

        return True

    """
    Validation section consider to move separate class
    """
    def __role_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.allowed_id_roles) and \
               channel.id in self.allowed_channels_ids

    async def __display_that_we_already_played(self, ctx):
        we_played_log = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.WE_PLAYED")

        embed_message = discord.Embed(
            title=f"**{self.name.capitalize()}**",
            description=we_played_log,
            color=self.color
        )

        await ctx.respond(embed=embed_message)

    def __read_blacklist_players(self):
        list_of_players = read_file_lines(f"./localLogs/oko/{self.name}.txt")

        cleaned_list_of_players = [id.strip() for id in list_of_players]

        return cleaned_list_of_players

    async def __display_lack_of_player(self, ctx):
        lack_of_player = self.translation.translate("GAMES.EYE.LACK_OF_PLAYER", [{"name": self.name}])

        embed_message = discord.Embed(
            title="**Głos z Eteru**",
            description=lack_of_player
        )

        await ctx.respond(embed=embed_message)

    async def __display_u_play_with_him(self, ctx):
        u_play_with_this_oponent = self.translation.translate("GAMES.EYE.CURRENT_IN_GAME_WITH_THIS_OPONENET",
                                                              [{"name": self.name}])

        embed_message = discord.Embed(
            title="**Głos z Eteru**",
            description=u_play_with_this_oponent,
        )

        await ctx.respond(embed=embed_message)

    async def __is_rupella_in_action(self, ctx) -> bool:
        if str(ctx.author.id) in self.__read_blacklist_of_rupella():
            gtfo = self.translation.translate("GAMES.EYE.RUPELLA.GTFO")

            embed_message = discord.Embed(
                title="**Rupella**",
                description=gtfo,
                color=self.rueplla_color
            )

            await ctx.respond(embed=embed_message)
            return True

        return False

    def __read_blacklist_of_rupella(self) -> List[str]:
        list_of_players = read_file_lines(f"./localLogs/{LOCAL_LOGS_RUPELLA_BLACKLIST_PATH}")

        cleaned_list_of_blacklisted_players = [id.strip() for id in list_of_players]

        return cleaned_list_of_blacklisted_players

    """
    init extension    
    """
    def __define_bot_config_statuses(self, busy: bool):
        players = self.config.get_config_key("games.eye.players")
        self.bot = [player for player in players if player["name"] == self.name][0]

        self.busy = not self.bot.get("process", busy)
        self.is_bot_eager_for_many_games = self.bot.get("many_games")
        self.lower_bid_threshold = self.bot.get("lower_threshold")
        self.upper_bid_threshold = self.bot.get("upper_threshold")
        self.upper_strategy_boundary = self.bot.get("upper_strategy_boundary")
        self.lower_strategy_boundary = self.bot.get("lower_strategy_boundary")
        self.color = int(self.bot.get("color"), 16)
        self.is_cheating = self.bot.get("cheating_process", False)

        if self.is_cheating:
            cheating_method_type = self.bot.get("cheating", {}).get("method", "soft")

            if cheating_method_type == "soft":
                self.__cheating_method = self.__perform_soft_nine_force_roll
            elif cheating_method_type == "hard":
                self.__cheating_method = self.__perform_strong_nine_force_roll

    def __setup_game(self, bid, author_id):
        self.busy = True
        self.bid = bid
        self.game_id = uuid.uuid4()
        self.enemy_id = author_id
        self.player_dices = 1
        self.dice_count = 1
        self.strategy = random.randint(
            self.lower_strategy_boundary,
            self.upper_strategy_boundary
        )

    def __roll_initiative(self) -> (int, int):
        bot_initiative_roll = 0
        player_initiative_roll = 0

        while bot_initiative_roll == player_initiative_roll:
            bot_initiative_roll, player_initiative_roll = [
                random.randint(1, 10), random.randint(1, 10)
            ]

        return bot_initiative_roll, player_initiative_roll

    """
    Log section
    """
    def __generate_initiative_log(self, data):
        player = data.get("player", {"name": "pewno mal"})
        bot_initiative = data.get("bot_initiative", 0)
        player_initiative = data.get("player_initiative", 0)
        bid = data.get("bid", 0)

        log = \
            f"[{self.game_id}] {datetime.now()}: {self.name} VS {player.name}({player.id}), " \
            f"bid: {bid}, initiative rolls: {bot_initiative}:{player_initiative}, " \
            f"strategy drawing: {self.strategy}"

        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __save_roll_log(self, data):
        roller_name = data.get("roller", "cycki")
        roll_result = data.get("result", [9])

        log = f"[{self.game_id}] {datetime.now()}: {roller_name} performed its roll! The result roll: {roll_result}"
        write_to_game_logs('oko/eye-game-logs.txt', log)

    def __save_draw_log(self, data):
        bot = data.get("bot", "cycki")
        amount = data.get("amount", "current_amount")

        log = f"[{self.game_id}] {datetime.now()}: {bot} has drawn a dice, current amount of dice: {amount}"

        write_to_game_logs('oko/eye-game-logs.txt', log)

    async def __display_wrong_thresold_message(self, ctx, bid: int):
        if self.lower_bid_threshold > bid:
            not_enough = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.NOT_ENOUGH")

            embed_message = discord.Embed(title=self.name.capitalize(), description=not_enough, color=self.color)

            await ctx.respond(embed=embed_message)

        elif self.upper_bid_threshold < bid:
            too_much = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.TOO_MUCH")

            embed_message = discord.Embed(title=self.name.capitalize(), description=too_much, color=self.color)

            await ctx.respond(embed=embed_message)

    async def __process_victory(self, ctx, message_to_send, results, result_roll_message, is_bot_winner):
        self.__save_winning_log({
            "roller": self.name if is_bot_winner else ctx.author.name,
            "loser": ctx.author.name if is_bot_winner else self.name,
            "bot_victory": is_bot_winner,
            "result": results
        })
        previous_message_to_process = f"{message_to_send}\n\n" if message_to_send else ""

        victory_log = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.VICTORY") if is_bot_winner \
            else self.translation.translate(f"GAMES.EYE.{self.name.upper()}.REACTION_ON_SUCCESS_PLAYER")
        game_is_done_log = \
            self.translation.translate("GAMES.EYE.GAME_IS_DONE", [
                {
                    "name": self.name.capitalize() if is_bot_winner else  ctx.author.display_name.capitalize()
                }, {
                    "bid": self.bid
                }
            ])

        chosen_message = previous_message_to_process +\
                         f"{result_roll_message}\n\n" \
                         f"**{self.name.capitalize()}:**\n{victory_log}\n\n" \
                         f"**Głos z Eteru:**\n{game_is_done_log}"

        embed = discord.Embed(description=chosen_message, color=self.color)

        await ctx.respond(embed=embed)

        self.__add_to_already_played_file({
            "player": ctx.author.id
        })
        self.busy = False

    async def __cannot_draw(self, ctx):
        cannot_draw = self.translation.translate("GAMES.EYE.CANNOT_DRAW")
        
        embed = discord.Embed(description=f"**Głos z Eteru:**\n{cannot_draw}")
        
        await ctx.respond(embed=embed)

    async def __cannot_roll(self, ctx):
        cannot_roll = self.translation.translate("GAMES.EYE.CANNOT_ROLL")

        embed = discord.Embed(description=f"**Głos z Eteru:**\n{cannot_roll}")

        await ctx.respond(embed=embed)

    def __perform_strong_nine_force_roll(self, dices: int) -> (List[str], str):
        result = [random.randint(1, 14) for _ in range(dices)]

        for index in range(len(result)):
            if 7 <= result[index] <= 8:
                result[index] = "7"
            elif 9 <= result[index] <= 10:
                result[index] = "8"
            elif 11 <= result[index] <= 13:
                result[index] = "9"
            elif result[index] == 14:
                result[index] = "10"
            else:
                result[index] = str(result[index])

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT", [{"name": self.name.capitalize()}, {"result": ",".join(result)}])

        roll_result_message = f"**Głos z Eteru:**\n{comment_to_roll_result}"

        return result, roll_result_message

    def __perform_soft_nine_force_roll(self, dices: int) -> (List[str], str):
        result = [random.randint(1, 100) for _ in range(dices)]

        for index in range(len(result)):
            if 1 <= result[index] <= 7:
                result[index] = "1"
            elif 8 <= result[index] <= 16:
                result[index] = "2"
            elif 17 <= result[index] <= 25:
                result[index] = "3"
            elif 26 <= result[index] <= 33:
                result[index] = "4"
            elif 34 <= result[index] <= 42:
                result[index] = "5"
            elif 42 <= result[index] <= 50:
                result[index] = "6"
            elif 51 <= result[index] <= 62:
                result[index] = "7"
            elif 63 <= result[index] <= 75:
                result[index] = "8"
            elif 76 <= result[index] <= 89:
                result[index] = "9"
            else:
                result[index] = "10"

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT",
                                       [{"name": self.name.capitalize()}, {"result": ",".join(result)}])

        roll_result_message = f"**Głos z Eteru:**\n{comment_to_roll_result}"

        return result, roll_result_message

    def __perform_fair_roll(self, dices, roller):
        result = [str(random.randint(1, 10)) for _ in range(dices)]

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT", [{"name": roller}, {"result": ", ".join(result)}])

        roll_result_message = f"**Głos z Eteru:**\n{comment_to_roll_result}"

        return result, roll_result_message
