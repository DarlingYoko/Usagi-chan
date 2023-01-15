from discord.ext.commands import CommandError


class UsagiNotSetUpError(CommandError):
    """Exception raised when the command is not set up in database

    This inherits from :exc:`CommandError`
    """


class UsagiModuleDisabled(CommandError):
    """Exception raised when the command was called from disabled module

    This inherits from :exc:`CommandError`
    """
