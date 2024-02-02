import json
from typing import Dict, List, Union

import discord


def read_file_lines(path):
    try:
        lines = []

        with open(path, "r", encoding='utf-8') as file:
            for line in file:
                lines.append(line)

        return lines
    except FileNotFoundError:
        return []


def read_json_file(path):
    try:
        with open(path, "r", encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def write_to_game_logs(filename: str, text: str):
    with open(f"./localLogs/{filename}", 'a', encoding="utf-8") as file:
        file.write(f"{text}\n")


def write_to_actions_logs(filename: str, text: str):
    with open(f"./localLogs/actions/{filename}", 'a', encoding="utf-8") as file:
        file.write(f"{text}\n")


def split_by_dots(string: str) -> List:
    return string.split('.')


def get_key_in_dict(keys: List, dictionary: Dict) -> Union[str, bool]:
    try:
        iterator_dict = {}

        for key in keys:
            if iterator_dict:
                iterator_dict = iterator_dict.get(key)
            else:
                iterator_dict = dictionary.get(key)

        return iterator_dict
    except AttributeError:
        print("ERROR-UTIL-1: Problem with processing of key")
        return "Głowa mnie boli..."


def role_and_channel_valid(data):
    author_roles = data.get("author_roles", "")
    channel_name = data.get("channel_source", "")
    allowed_roles = data.get("allowed_roles", [])
    allowed_channels_names = data.get("allowed_channel_names", [])

    return any(discord.utils.get(author_roles, name=role) for role in allowed_roles) and \
           channel_name in allowed_channels_names

def reset_localLogs_file(path):
    try:
        with open(f"./localLogs/{path}", "w"):
            pass
    except FileNotFoundError:
        print(f"[RESET STATS]: lack of file {path}.text")
        return
    except IOError as e:
        print(f"[RESET STATS]: An unexpected error occurred: {e}")
        return