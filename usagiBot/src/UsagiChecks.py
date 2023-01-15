from discord.ext import commands
from usagiBot.src.UsagiUtils import check_command_tag_in_db
from usagiBot.src.UsagiErrors import UsagiNotSetUpError


def check_is_already_set_up():
    async def predicate(ctx):
        command_tag = ctx.command.__original_kwargs__.get("command_tag")
        if not command_tag:
            raise UsagiNotSetUpError()

        checker = await check_command_tag_in_db(ctx, command_tag)
        if checker:
            return True
        else:
            raise UsagiNotSetUpError()

    return commands.check(predicate)
