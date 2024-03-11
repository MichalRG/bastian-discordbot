from typing import List

from src.services.Config import Config


class ObservableEyeService:
    def __init__(self, config=Config()):
        self.config = config

        self.available_eye_players: List[str] = config.get_config_key("games.eye.bot_names")

    def activate_eye_bot(self, name: str):
        if name not in self.available_eye_players:
            self.available_eye_players.append(name)

    def deactivate_eye_bot(self, name: str):
        self.available_eye_players.remove(name)

    def get_active_eye_bots(self) -> List[str]:
        return self.available_eye_players or []
