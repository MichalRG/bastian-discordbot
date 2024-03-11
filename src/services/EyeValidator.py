import discord


class EyeValidator:
    def __init__(self, allowed_id_roles, allowed_channels_ids):
        self.allowed_id_roles = allowed_id_roles
        self.allowed_eye_player_channels_ids = allowed_channels_ids

    def role_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.allowed_id_roles) and \
               channel.id in self.allowed_eye_player_channels_ids
