from usagiBot.env import (
    TWITCH_TOKEN,
    REFRESH_TOKEN,
    CLIENT_ID,
    CLIENT_SECRET,
)
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope


async def twitch_auth() -> Twitch:
    """
    Create new object to Twitch API
    :return: new Twitch
    """
    twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
    target_scope = [AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
    await twitch.set_user_authentication(TWITCH_TOKEN, target_scope, REFRESH_TOKEN)
    return twitch
