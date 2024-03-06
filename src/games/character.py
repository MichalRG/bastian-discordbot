import random
import uuid
from datetime import datetime
from typing import List

import discord

from src.const.paths import LOCAL_LOGS_RUPELLA_BLACKLIST_PATH
from src.services.config import Config
from src.services.general_utils import read_file_lines, write_to_game_logs
from src.services.translation import Translation


class Character:
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
            if self.busy or (not self.busy and self.enemy_id != ctx.author.id):
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
            if self.busy or (not self.busy and self.enemy_id != ctx.author.id):
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

                await self.__perform_bot_action(ctx, bot_reaction)

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
        result = [str(random.randint(1, 10)) for _ in range(dices)]

        comment_to_roll_result = \
            self.translation.translate("GAMES.EYE.ROLL_RESULT", [{"name": roller}, {"result": ", ".join(result)}])

        roll_result_message = f"**Głos z Eteru:**\n{comment_to_roll_result}"

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

        await ctx.respond(f"**{self.name}:**\n{we_played_log}")

    def __read_blacklist_players(self):
        list_of_players = read_file_lines(f"./localLogs/oko/{self.name}.txt")

        cleaned_list_of_players = [id.strip() for id in list_of_players]

        return cleaned_list_of_players

    async def __display_lack_of_player(self, ctx):
        lack_of_player = self.translation.translate("GAMES.EYE.LACK_OF_PLAYER", [{"name": self.name}])
        await ctx.respond(f"**Głos z Eteru:**\n{lack_of_player}")

    async def __display_u_play_with_him(self, ctx):
        u_play_with_this_oponent = self.translation.translate("GAMES.EYE.CURRENT_IN_GAME_WITH_THIS_OPONENET",
                                                              [{"name": self.name}])

        await ctx.respond(f"**Głos z Eteru:**\n{u_play_with_this_oponent}")

    async def __is_rupella_in_action(self, ctx) -> bool:
        if str(ctx.author.id) in self.__read_blacklist_of_rupella():
            gtfo = self.translation.translate("GAMES.EYE.RUPELLA.GTFO")
            await ctx.respond(f"**Rupella:**\n{gtfo}")
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

        self.bot = players.get(self.name, {"process": False, "many_games": False})
        self.busy = self.bot.get("process", busy)
        self.is_bot_eager_for_many_games = self.bot.get("many_games")
        self.lower_bid_threshold = self.bot.get("lower_threshold")
        self.upper_bid_threshold = self.bot.get("upper_threshold")
        self.upper_strategy_boundary = self.bot.get("upper_strategy_boundary")
        self.lower_strategy_boundary = self.bot.get("lower_strategy_boundary")
        self.color = self.bot.get("color")

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
            await ctx.respond(f"**{self.name.capitalize()}:**\n{not_enough}")

        elif self.upper_bid_threshold < bid:
            too_much = self.translation.translate(f"GAMES.EYE.{self.name.upper()}.TOO_MUCH")
            await ctx.respond(f"**{self.name.capitalize()}:**\n{too_much}")

    async def __process_victory(self, ctx, message_to_send, results, result_roll_message, is_bot_winner):
        self.__save_winning_log({
            "roller": self.name if is_bot_winner else ctx.author.name,
            "loser": ctx.author.name if is_bot_winner else self.name,
            "bot_victory": is_bot_winner,
            "result": results
        })

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

        chosen_message = f"{message_to_send}\n\n" if message_to_send else "" \
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
        
        embed = discord.Embed(description=f"**Głos z Eteru:**\n{cannot_draw}", color=self.color)
        
        await ctx.respond(embed=embed)

    async def __cannot_roll(self, ctx):
        cannot_roll = self.translation.translate("GAMES.EYE.CANNOT_ROLL")

        embed = discord.Embed(description=f"**Głos z Eteru:**\n{cannot_roll}", color=self.color)

        await ctx.respond(embed=embed)
