import random
from typing import List, Dict

from src.services.general_utils import read_json_file, get_key_in_dict, split_by_dots


class Translation:
    """
    In current version it's forced to pass variables always as a list of dicts where each dict should contains one key + value
    e.g. [{"variable1": "Thor"},{"variable2": "Odyn"}]
    """
    def translate(self, path: str, variables: List[Dict[str, str]] = None) -> str:
        splitted_key = split_by_dots(path)

        translations = read_json_file("./pl.json")

        aimed_translation = get_key_in_dict(splitted_key, translations)

        if isinstance(aimed_translation, list):
            aimed_translation = random.choice(aimed_translation)

        if variables:
            aimed_translation = self.__replace_variables_with_values(variables, aimed_translation)

        return aimed_translation

    def __replace_variables_with_values(self, variables: List[Dict[str, str]], aimed_translation: str) -> str:
        if isinstance(variables, list):
            for variable in variables:
                if isinstance(variable, Dict):
                    key = list(variable.keys())[0]
                    value = str(list(variable.values())[0])

                    aimed_translation = aimed_translation.replace(f"{{{{{key}}}}}", value)

        return aimed_translation
