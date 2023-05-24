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


class OpenAIError(CommandError):
    """Exception raised for OpenAI module

    This inherits from :exc:`CommandError`
    """

    def __init__(self, error, status_code):
        self.status_code = status_code
        self.message = error.get("message")
        self.type = error.get("type")

    def __str__(self):
        return (
            f"Status Code: {self.status_code}\n"
            f"Error message: {self.message}.\n"
            f"Error type: {self.type}.\n"
        )
