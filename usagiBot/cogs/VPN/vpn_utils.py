import asyncio
import uuid
from collections import defaultdict
from typing import Dict, List

import discord
from discord.types.embed import Embed

from usagiBot.cogs.VPN.schemas import UsagiVpnUsers
from usagiBot.env import (
    VPN_USERNAME,
    VPN_PASSWORD,
    VPN_API_URL,
    VPN_SUB_URL
)
from usagiBot.src.UsagiUtils import get_embed

from py3xui import AsyncApi, Client


class Vpn3xui:
    def __init__(self):
        self.api = AsyncApi(
            VPN_API_URL,
            VPN_USERNAME,
            VPN_PASSWORD
        )

    async def login(self):
        await self.api.login()

    async def create_user_sub(self, uid: str, sub_name: str, new_expiry_time: int) -> str:
        """Create a new user subscription for all Inbounds
        1. Get all Inbounds
        2. For every Inbound, add user with subscription
        """
        clients_email = []
        inbounds = await self.api.inbound.get_list()
        for inbound in inbounds:
            new_client = Client(
                id=str(uuid.uuid4()),
                email=f'{sub_name}-{inbound.remark}',
                sub_id=uid,
                flow='xtls-rprx-vision',
                expiry_time=new_expiry_time,
                enable=True
            )
            await self.api.client.add(inbound.id, [new_client])
            clients_email.append(new_client.email)

        return f'{VPN_SUB_URL}/{uid}'

    async def get_user(self, user_name: str) -> Dict[str, float]:
        client = await self.api.client.get_by_email(user_name)
        return {
            "traffic": round((client.down + client.up) / (1024 ** 3), 2),
            "expiryTime": client.expiry_time // 1000
        }

    async def get_sub(self, uid: str) -> Dict[str, float]:
        expiry_time = 0
        traffic = 0
        inbounds = await self.api.inbound.get_list()

        tasks = []
        clients = []

        for inbound in inbounds:
            for client in inbound.settings.clients:
                if client.sub_id == uid:
                    tasks.append(self.api.client.get_by_email(client.email))
                    clients.append(client)


        users = await asyncio.gather(*tasks)

        for client, user in zip(clients, users):
            traffic += round((user.down + user.up) / (1024 ** 3), 2)
            expiry_time = client.expiry_time // 1000

        return {
            "traffic": traffic,
            "expiryTime": expiry_time
        }

    async def update_user_expiry_time_by_sub_name(self, uid: str, new_expiry_time: int):
        inbounds = await self.api.inbound.get_list()

        tasks = []

        for inbound in inbounds:
            for client in inbound.settings.clients:
                if client.sub_id == uid:
                    tasks.append(self._update_client(client, new_expiry_time))

        await asyncio.gather(*tasks)

    async def _update_client(self, client, new_expiry_time):
        client_data = await self.api.client.get_by_email(client.email)
        client_data.id = client.id
        client_data.flow = "xtls-rprx-vision"
        client_data.expiry_time = new_expiry_time
        client_data.enable = True

        await self.api.client.update(client_data.id, client_data)

    async def get_top_traffic(self) -> Dict[str, Dict[str, float]]:
        users_traffic = defaultdict(lambda: {"sub_name": "", "traffic": 0.0})

        inbounds = await self.api.inbound.get_list()

        tasks = []
        clients = []

        for inbound in inbounds:
            for client in inbound.settings.clients:
                tasks.append(self.api.client.get_by_email(client.email))
                clients.append(client)

        users = await asyncio.gather(*tasks)

        for client, user in zip(clients, users):
            traffic = (user.down + user.up) / (1024 ** 3)
            data = users_traffic[client.sub_id]
            client_name = client.email.split('-')[0]

            data["sub_name"] = client_name
            data["traffic"] += traffic

        return dict(
            sorted(
                ((k, {"sub_name": v["sub_name"], "traffic": round(v["traffic"], 2)})
                 for k, v in users_traffic.items()),
                key=lambda x: x[1]["traffic"],
                reverse=True
            )[:10]
        )

    async def add_users_to_inboud(self, inbound_id: int, users: List[UsagiVpnUsers]) -> bool:
        inbound = await self.api.inbound.get_by_id(inbound_id)
        clients = []

        for user in users:
            expiry_time = int(user.expiration_date.timestamp() * 1000) if user.expiration_date else 0
            clients.append(
                Client(
                    id=str(uuid.uuid4()),
                    email=f'{user.sub_name}-{inbound.remark}',
                    sub_id=user.uid,
                    # flow='xtls-rprx-vision',
                    expiry_time=expiry_time,
                    enable=True
                )
            )

        await self.api.client.add(inbound_id, clients)
        return True


async def generate_vpn_user_info(bot, vpn_users, lang) -> Embed:
    vpn3xui = Vpn3xui()
    await vpn3xui.login()

    vpn_info = []
    for idx, vpn_user in enumerate(vpn_users):
        user_info = await vpn3xui.get_sub(vpn_user.uid)

        expiry_time = user_info['expiryTime']
        vpn_timer = f'<t:{expiry_time}:R>' if expiry_time else '∞'

        vpn_traffic = user_info['traffic']
        vpn_info.append(f'{idx + 1}. {vpn_user.sub_name} — {vpn_traffic}GB — {vpn_timer}')

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
