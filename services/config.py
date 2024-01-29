import json
from typing import List, Dict

from services.general_utils import read_json_file, get_key_in_dict, split_by_dots


class Config:
    def __init__(self):
        self.config = read_json_file("./config.json")

    def get_config_key(self, section: str):
        splitted_section = split_by_dots(section)

        return get_key_in_dict(splitted_section, self.config)

    def get_process_permissions_for_section(self, section: str) -> bool:
        splitted_section = split_by_dots(section)

        splitted_section.append('process')

        return get_key_in_dict(splitted_section, self.config)
        # return self.config.get(section, {}).get("process")

    def get_permissions_access_for_guilds(self) -> Dict:
        return self.config.get('permissions', {})

    def get_legit_guilds(self) -> List:
        return self.config.get("legit", {}).get("guilds")

    def get_legit_channels(self) -> List:
        return self.config.get("legit", {}).get("channels")

