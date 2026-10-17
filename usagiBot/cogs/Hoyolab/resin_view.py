from dataclasses import dataclass
from typing import Awaitable, Callable

import discord
from pycord18n.extension import _

from usagiBot.cogs.Hoyolab.genshin_utils import generate_fields
from usagiBot.cogs.Hoyolab.schemas import UsagiHoyolab
from usagiBot.src.UsagiUtils import get_embed

# (key used by get_user_data/generate_fields, select label, UsagiHoyolab column)
GAMES = (
    ("genshin", "Genshin Impact", "show_genshin"),
    ("starrail", "Honkai: Star Rail", "show_starrail"),
    ("zzz", "Zenless Zone Zero", "show_zzz"),
)

LABEL_LIMIT = 100


@dataclass
class ResinAccount:
    user: UsagiHoyolab
    # Empty when Hoyolab rejected the stored cookies.
    data: dict


Loader = Callable[[UsagiHoyolab], Awaitable[dict]]


def enabled_games(user: UsagiHoyolab) -> list[str]:
    return [key for key, _name, column in GAMES if getattr(user, column)]


def account_label(user_id: int, data: dict | None) -> str:
    """Nickname, or a stable placeholder so a dead account is never hidden."""
    nickname = (data or {}).get("nickname")
    if nickname:
        return nickname[:LABEL_LIMIT]
    return f"Hoyolab user #{user_id} (cookie expired)"[:LABEL_LIMIT]


class ResinAccountSelect(discord.ui.Select):
    def __init__(self, accounts: list[ResinAccount]) -> None:
        super().__init__(
            placeholder="Choose account",
            options=[
                discord.SelectOption(
                    label=account_label(account.user.id, account.data),
                    value=str(account.user.id),
                )
                for account in accounts
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResinView = self.view
        view.select_account(int(self.values[0]))
        await interaction.response.edit_message(**view.render(), view=view)


class ResinGamesSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Games to show",
            min_values=1,
            max_values=len(GAMES),
            options=[
                discord.SelectOption(label=name, value=key) for key, name, _col in GAMES
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ResinView = self.view
        account = view.current
        chosen = set(self.values)
        flags = {column: key in chosen for key, _name, column in GAMES}

        # The refetch below talks to Hoyolab, which can outlast the 3s window.
        await interaction.response.defer()
        await UsagiHoyolab.update(id=account.user.id, **flags)
        for column, value in flags.items():
            setattr(account.user, column, value)
        account.data = await view.loader(account.user)
        view.sync_defaults()
        await interaction.edit_original_response(**view.render(), view=view)


class ResinView(discord.ui.View):
    def __init__(
        self, accounts: list[ResinAccount], loader: Loader, *, editable: bool
    ) -> None:
        super().__init__()
        self.accounts = accounts
        self.loader = loader
        self.current = next((a for a in accounts if a.data), accounts[0])

        self.account_select = ResinAccountSelect(accounts)
        self.add_item(self.account_select)
        # Someone else's accounts (`/hoyolab resin user_id:`) are view-only.
        self.games_select = ResinGamesSelect() if editable else None
        if self.games_select:
            self.add_item(self.games_select)
        self.sync_defaults()

    def select_account(self, user_id: int) -> None:
        self.current = next(a for a in self.accounts if a.user.id == user_id)
        self.sync_defaults()

    def sync_defaults(self) -> None:
        """Mark the currently shown account and its games in the selects."""
        for option in self.account_select.options:
            option.default = option.value == str(self.current.user.id)
        if self.games_select:
            enabled = enabled_games(self.current.user)
            for option in self.games_select.options:
                option.default = option.value in enabled

    def render(self) -> dict:
        account = self.current
        label = account_label(account.user.id, account.data)
        if not account.data:
            embed = get_embed(
                title=_("Resin"),
                author_name=label,
                description=_("Your cookie out of date"),
            )
            return {"embed": embed, "content": ""}

        embed = get_embed(
            title=_("Resin"),
            author_name=label,
            author_icon_URL=account.data.get("icon", None),
            fields=generate_fields(account.data, enabled_games(account.user)),
        )
        geetest_error = account.data.get("geetest_error")
        content = (
            _("geetest error").format(geetest_error=geetest_error)
            if geetest_error
            else ""
        )
        return {"embed": embed, "content": content}
