from discord.ext.commands import CommandError


class UsagiNotSetUpError(CommandError):
    """Exception raised when the command is not set up in database

    This inherits from :exc:`CommandError`
    """


class UsagiModuleDisabledError(CommandError):
    """Exception raised when the command was called from disabled module

    This inherits from :exc:`CommandError`
    """


class UsagiCallFromNotModerError(CommandError):
    """Exception raised when the command was called not by Moder member

    This inherits from :exc:`CommandError`
    """


class UsagiCallFromWrongChannelError(CommandError):
    """Exception raised when the command was called from wrong channel

    This inherits from :exc:`CommandError`
    """
    def __init__(self, channel_id=None):
        self.channel_id = channel_id
