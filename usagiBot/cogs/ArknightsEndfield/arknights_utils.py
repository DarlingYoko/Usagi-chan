"""
Async client for Arknights: Endfield (SKPort).

Features:
- OAuth / cred / sign_token handling
- Daily attendance
- Profile (stamina, BP, daily missions)
- Unified API result models
- Async (aiohttp)
- Ready for Discord bot / background tasks
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

import aiohttp
import discord

from usagiBot.src.UsagiUtils import get_embed

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKPORT_BASE_URL = "https://zonai.skport.com"

ACCOUNT_TOKEN_URL = "https://web-api.skport.com/cookie_store/account_token"
OAUTH_GRANT_URL = "https://as.gryphline.com/user/oauth2/v2/grant"

SKPORT_APP_CODE = "6eb76d4e13aa36e6"
ENDFIELD_GAME_ID = "3"

PLATFORM = "3"
VNAME = "1.0.0"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Generic API result
# ---------------------------------------------------------------------------

T = TypeVar("T")


@dataclass
class ApiResult(Generic[T]):
    """
    Unified result for any API call.
    """
    success: bool
    message: str
    data: Optional[T] = None


# ---------------------------------------------------------------------------
# Attendance models
# ---------------------------------------------------------------------------

@dataclass
class AttendanceData:
    days_signed: Optional[int] = None
    today_reward: Optional[str] = None
    already_signed: bool = False


# ---------------------------------------------------------------------------
# Profile models
# ---------------------------------------------------------------------------

@dataclass
class SanityInfo:
    current: int
    max: int
    recover_ts: Optional[int]


@dataclass
class BattlePassInfo:
    level: int
    max: int


@dataclass
class DailyMissionInfo:
    current: int
    max: int


@dataclass
class Domain:
    name: str
    aurylene_count: int
    crate_count: int


@dataclass
class ProfileData:
    nickname: str
    avatar_url: str
    uid: int
    level: int
    world_level: int
    sanity: SanityInfo
    bp: BattlePassInfo
    daily: DailyMissionInfo
    char_num: int
    weapon_num: int
    valley: Domain
    wuling: Domain


# ---------------------------------------------------------------------------
# Endfield client
# ---------------------------------------------------------------------------

class EndfieldClient:
    """
    Async client for interacting with Arknights: Endfield APIs via SKPort.
    """

    def __init__(
        self,
        account_token: str,
        cookie: Optional[str] = '',
        language: str = "en",
    ):
        self.cookie: str = cookie.strip()
        self.account_token: Optional[str] = account_token

        self.language: str = language

        self.cred_token: Optional[str] = None
        self.sign_token: Optional[str] = None

        self.game_role: Optional[str] = None
        self.uid: Optional[int] = None

        self.session: Optional[aiohttp.ClientSession] = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://game.skport.com",
                "Referer": "https://game.skport.com/",
            }
        )

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_cookie_value(self, name: str) -> Optional[str]:
        """Extract a cookie value from raw cookie string."""
        match = re.search(rf"{name}=([^;]+)", self.cookie)
        return match.group(1) if match else None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def _get_account_token(self) -> Optional[str]:
        """
        Get account token for OAuth authentication.

        The ACCOUNT_TOKEN is an httpOnly cookie that cannot be accessed via document.cookie.
        It must be provided directly via the 'token' parameter or extracted from browser DevTools.

        Returns:
            Account token string or None if not available
        """
        if self.account_token:
            return self.account_token

        token = self._extract_cookie_value("ACCOUNT_TOKEN")
        if token:
            return token

        sk_oauth = self._extract_cookie_value("SK_OAUTH_CRED_KEY")
        if not sk_oauth or not self.session:
            return None

        headers = {"Cookie": f"SK_OAUTH_CRED_KEY={sk_oauth}"}
        async with self.session.get(ACCOUNT_TOKEN_URL, headers=headers) as r:
            if r.status != 200:
                return None
            data = await r.json()
            return data.get("data", {}).get("content")

    async def _refresh_oauth_code(self, account_token: str) -> Optional[str]:
        """
        Exchange account token for a fresh SK_OAUTH_CRED_KEY.

        This calls the OAuth grant endpoint to get a new credential token
        that can be used for authenticated API requests.

        Args:
            account_token: The ACCOUNT_TOKEN value

        Returns:
            New SK_OAUTH_CRED_KEY token (cred) or None on failure
        """
        if not self.session:
            return None

        async with self.session.post(
            OAUTH_GRANT_URL,
            json={"token": account_token, "appCode": SKPORT_APP_CODE, "type": 0},
        ) as r:
            if r.status != 200:
                return None
            data = await r.json()
            return data.get("data", {}).get("code")

    async def _get_cred_from_oauth(self, oauth_code: str) -> Optional[str]:
        """
        Generate a cred (credential) from the OAuth code.

        The OAuth code from gryphline.com needs to be exchanged for a cred
        that can be used with zonai.skport.com API.

        Args:
            oauth_code: The OAuth code from grant endpoint

        Returns:
            The cred token or None on failure
        """
        if not self.session:
            return None

        async with self.session.post(
            f"{SKPORT_BASE_URL}/web/v1/user/auth/generate_cred_by_code",
            json={"kind": 1, "code": oauth_code},
        ) as r:
            if r.status != 200:
                return None
            data = await r.json()
            return data.get("data", {}).get("cred")

    async def refresh_sign_token(self) -> bool:
        """
        Refresh the sign token by calling the auth/refresh endpoint.

        Returns:
            True if successful, False otherwise
        """
        if not self.session or not self.cred_token:
            return False

        ts = str(int(time.time()))
        async with self.session.get(
            f"{SKPORT_BASE_URL}/web/v1/auth/refresh",
            headers={
                "cred": self.cred_token,
                "platform": PLATFORM,
                "vname": VNAME,
                "timestamp": ts,
                "sk-language": self.language,
            },
        ) as r:
            if r.status != 200:
                return False
            data = await r.json()
            self.sign_token = data.get("data", {}).get("token")
            return bool(self.sign_token)

    async def get_player_binding(self) -> bool:
        """
        Get player binding info to determine the sk-game-role header.

        The sk-game-role format is: "gameId_roleId_serverId"
        For example: "3_4605473178_2"

        Returns:
            True if successful, False otherwise
        """
        if not self.session or not self.cred_token:
            return False

        ts = str(int(time.time()))
        path = "/api/v1/game/player/binding"

        headers = {
            "cred": self.cred_token,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": self.language,
        }

        if self.sign_token:
            headers["sign"] = self._compute_sign(path, ts)

        async with self.session.get(SKPORT_BASE_URL + path, headers=headers) as r:
            if r.status != 200:
                return False
            data = await r.json()

        for app in data.get("data", {}).get("list", []):
            if app.get("appCode") == "endfield":
                binding = app["bindingList"][0]
                role = binding.get("defaultRole")
                self.uid = int(role["roleId"])
                self.game_role = f"{ENDFIELD_GAME_ID}_{role['roleId']}_{role['serverId']}"
                return True

        return False

    async def ensure_auth(self) -> bool:
        """
        Ensure valid authentication state.
        Safe to call before any API request.
        """
        if not self.cred_token:
            return await self.sign_in()
        return await self.refresh_sign_token()

    # ------------------------------------------------------------------
    # Sign-in / Attendance
    # ------------------------------------------------------------------

    async def sign_in(self) -> bool:
        """
        Perform sign-in.

        The authentication flow:
        1. Get ACCOUNT_TOKEN (from config token, cookie string, or cookie_store API)
        2. Exchange ACCOUNT_TOKEN for OAuth code via OAuth grant
        3. Exchange OAuth code for cred via generate_cred_by_code
        4. Refresh sign token via auth/refresh
        5. Use cred and sign token to call the attendance API with signed headers

        Returns:
            True if successful, False otherwise
        """
        account_token = await self._get_account_token()
        if not account_token:
            return False

        oauth_code = await self._refresh_oauth_code(account_token)
        if oauth_code:
            self.cred_token = await self._get_cred_from_oauth(oauth_code) or oauth_code
        else:
            self.cred_token = self._extract_cookie_value("SK_OAUTH_CRED_KEY")

        if not self.cred_token:
            return False

        refresh_status = await self.refresh_sign_token()
        binding_status = await self.get_player_binding()
        if refresh_status and binding_status:
            return True
        else:
            return False

    async def get_attendance(self) -> ApiResult[AttendanceData]:
        """
        Perform daily attendance check-in.

        Returns:
            ApiResult with success status and details
        """
        if not await self.ensure_auth() or not self.session:
            return ApiResult(False, "Not authenticated")

        ts = str(int(time.time()))
        path = "/web/v1/game/endfield/attendance"

        headers = {
            "cred": self.cred_token,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": self.language,
        }

        if self.game_role:
            headers["sk-game-role"] = self.game_role
        if self.sign_token:
            headers["sign"] = self._compute_sign(path, ts)

        async with self.session.post(SKPORT_BASE_URL + path, headers=headers) as r:
            data = await r.json()

        return self._parse_attendance(data, r.status)

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    async def get_profile(self) -> ApiResult[ProfileData]:
        """
        Fetch Endfield profile data.

        Returns:
            ApiResult with success status and details
        """
        if not await self.ensure_auth() or not self.session:
            return ApiResult(False, "Not authenticated")

        ts = str(int(time.time()))
        path = "/api/v1/game/endfield/card/detail"

        headers = {
            "cred": self.cred_token,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": self.language,
            "sk-game-role": self.game_role,
        }

        if self.sign_token:
            headers["sign"] = self._compute_sign(path, ts)

        async with self.session.get(SKPORT_BASE_URL + path, headers=headers) as r:
            data = await r.json()

        return self._parse_profile(data)

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def _parse_attendance(self, data: dict, status: int) -> ApiResult[AttendanceData]:
        code = data.get("code", -1)
        msg = data.get("message", "Unknown")

        if code == 0:
            d = data["data"]
            reward = d.get("reward")
            return ApiResult(
                True,
                "Attendance successful",
                AttendanceData(
                    days_signed=d.get("signInCount"),
                    today_reward=self._format_reward(reward) if reward else None,
                ),
            )

        if status == 403 or "already" in msg.lower():
            return ApiResult(True, "Already signed", AttendanceData(already_signed=True))

        return ApiResult(False, msg)

    def _parse_profile(self, data: dict) -> ApiResult[ProfileData]:
        try:
            d = data["data"]["detail"]

            base_domain = Domain(
                name="",
                aurylene_count=0,
                crate_count=0
            )
            domains = {}
            for domain in d["domain"]:
                aurylene_count = 0
                crate_count = 0
                for collection in domain["collections"]:
                    aurylene_count += collection.get("puzzleCount", 0)
                    crate_count += collection.get("trchestCount", 0)

                domains[domain["name"]] = Domain(
                    name=domain["name"],
                    aurylene_count=aurylene_count,
                    crate_count=crate_count
                )

            return ApiResult(
                True,
                "Profile fetched",
                ProfileData(
                    nickname=d["base"]["name"],
                    avatar_url=d["base"]["avatarUrl"],
                    uid=self.uid,
                    level=d["base"]["level"],
                    world_level=d["base"]["worldLevel"],
                    sanity=SanityInfo(
                        current=int(d["dungeon"]["curStamina"]),
                        max=int(d["dungeon"]["maxStamina"]),
                        recover_ts=int(d["dungeon"].get("maxTs")),
                    ),
                    bp=BattlePassInfo(
                        level=d["bpSystem"]["curLevel"],
                        max=d["bpSystem"]["maxLevel"],
                    ),
                    daily=DailyMissionInfo(
                        current=d["dailyMission"]["dailyActivation"],
                        max=d["dailyMission"]["maxDailyActivation"],
                    ),
                    char_num=d["base"]["charNum"],
                    weapon_num=d["base"]["weaponNum"],
                    valley=domains.get("Valley IV", base_domain),
                    wuling=domains.get("Wuling", base_domain),
                ),
            )
        except Exception as e:
            return ApiResult(False, str(e))

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------

    def _compute_sign(self, path: str, timestamp: str, body: str = "") -> str:
        """
        Compute the signature for zonai.skport.com API requests.

        The signature is computed using HMAC-SHA256 with the sign_token as the key.
        Formula: sign = MD5(HMAC-SHA256(path + body + timestamp + headers_json, sign_token))

        Args:
            path: API path (e.g., "/web/v1/game/endfield/attendance")
            timestamp: Unix timestamp as string
            body: Request body as JSON string (empty for GET, "{}" for POST)

        Returns:
            Signature hex string
        """
        headers_json = json.dumps(
            {
                "platform": PLATFORM,
                "timestamp": timestamp,
                "dId": "",
                "vName": VNAME,
            },
            separators=(",", ":"),
        )

        sign_str = f"{path}{body}{timestamp}{headers_json}"
        h = hmac.new(self.sign_token.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
        return hashlib.md5(h.encode()).hexdigest()

    @staticmethod
    def _format_reward(reward: dict) -> str:
        return f"{reward.get('name', 'Unknown')} x{reward.get('count', 1)}"


def generate_endfield_profile(p: ProfileData) -> discord.Embed:
    fields = [
        discord.EmbedField(
            name='_ _ _ _ _ _ _ _ _ _⭐ LVL',
            value=f'``` {p.level} (WL {p.world_level}) ```',
            inline=True,
        ),
        discord.EmbedField(
            name="_ _  🎫 Battle Pass",
            value=f'```   {p.bp.level}/{p.bp.max}   ```',
            inline=True,
        ),
        discord.EmbedField(
            name="_ _ _ _ _ _ 🧠 Sanity",
            value=f'```  {p.sanity.current}/{p.sanity.max}  ``` <t:{p.sanity.recover_ts}:R>',
            inline=True,
        ),
        discord.EmbedField(
            name=f"_ _ _ _ _ _ _ _ 📅 Daily",
            value=f'```  {p.daily.current}/{p.daily.max} ```',
            inline=True,
        ),
        discord.EmbedField(
            name="_ _ 🫃Characters",
            value=f"```    {p.char_num}```",
            inline=True,
        ),
        discord.EmbedField(
            name="_ _ _ _ 🔫 Weapons",
            value=f"```    {p.weapon_num}```\n_ _",
            inline=True,
        ),
        discord.EmbedField(
            name="_ _ _ _ _ _ _ _ _ _ _ _ _ _🌄 Valley IV",
            value=f"```Aurylene - {p.valley.aurylene_count}\nCrate - {p.valley.crate_count}```",
            inline=True,
        ),
        discord.EmbedField(
            name="_ _ _ _ _ _ _ _ _ _ _ _ _ _🐉 Wuling",
            value=f"```Aurylene - {p.wuling.aurylene_count}\nCrate - {p.wuling.crate_count}```",
            inline=True,
        ),
    ]

    return get_embed(
        title='Profile',
        author_name=p.nickname,
        author_icon_URL=p.avatar_url,
        footer=[str(p.uid), ''],
        fields=fields,
    )