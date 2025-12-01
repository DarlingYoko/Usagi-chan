from typing import Dict

import discord
from discord.types.embed import Embed

from usagiBot.env import (
    VPN_USERNAME,
    VPN_PASSWORD,
    VPN_API_URL
)
from usagiBot.src.UsagiUtils import get_embed

from py3xui import AsyncApi


class Vpn3xui:
    def __init__(self):
        self.api = AsyncApi(
            VPN_API_URL,
            VPN_USERNAME,
            VPN_PASSWORD
        )

    async def login(self):
        await self.api.login()

    async def get_user(self, user_name) -> Dict[str, float]:
        client = await self.api.client.get_by_email(user_name)
        return {
            "traffic": round((client.down + client.up) / (1024 ** 3), 2),
            "expiryTime": client.expiry_time // 1000
        }

    async def update_user_expiry_time(self, user_name, uuid, new_expiry_time):
        client = await self.api.client.get_by_email(user_name)
        client.id = uuid
        client.flow = 'xtls-rprx-vision'
        client.expiry_time = new_expiry_time
        client.enable = True

        await self.api.client.update(client.id, client)

    async def get_top_traffic(self) -> Dict[str, float]:
        users_traffic = {}
        inbounds = await self.api.inbound.get_list()
        for inbound in inbounds:
            for client in inbound.settings.clients:
                user = await self.api.client.get_by_email(client.email)
                users_traffic[client.email] = round((user.down + user.up) / (1024 ** 3), 2)

        return dict(sorted(users_traffic.items(), key=lambda x: x[1], reverse=True)[:10])


async def generate_vpn_user_info(bot, vpn_users, lang) -> Embed:
    vpn3xui = Vpn3xui()
    await vpn3xui.login()

    vpn_info = []
    for idx, vpn_user in enumerate(vpn_users):
        user_info = await vpn3xui.get_user(vpn_user.vpn_username)

        expiry_time = user_info['expiryTime']
        vpn_timer = f'<t:{expiry_time}:R>' if expiry_time else '∞'

        vpn_traffic = user_info['traffic']
        vpn_info.append(f'{idx + 1}. {vpn_user.vpn_username} — {vpn_traffic}GB — {vpn_timer}')

    max_len = max(len(line.split("—")[0]) for line in vpn_info)
    formatted_vpn_info = []
    for line in vpn_info:
        name, traffic, date = line.split(" — ")
        formatted_vpn_info.append(f"`{name.ljust(max_len)}` — {traffic} — {date}")

    result_vpn_info = "\n".join(formatted_vpn_info)

    notify_text = f'on' if vpn_users[0].notify_enabled else f'off'
    vpn_fields = [
        discord.EmbedField(
            name=bot.i18n.get_text(f'VPN notifications {notify_text}', lang),
            value='_ _'
        )
    ]
    title = bot.i18n.get_text('Your VPN profiles', lang)
    return get_embed(title=title, description=result_vpn_info, fields=vpn_fields)
