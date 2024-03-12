import discord


class RupellaValidator:
    def __init__(self, allowed_id_roles, allowed_channel_ids, admin_roles, admin_channels):
        self.allowed_role_ids = allowed_id_roles
        self.allowed_eye_player_channels_ids = allowed_channel_ids
        self.admin_channel_ids = admin_channels
        self.admin_role_ids = admin_roles

    def role_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.allowed_role_ids) and \
               channel.id in self.allowed_eye_player_channels_ids

    def admin_role_and_channel_valid(self, rolesAuthor, channel):
        return any(discord.utils.get(rolesAuthor, id=role_id) for role_id in self.admin_role_ids) and \
               channel.id in self.admin_channel_ids