import asyncio
import ipaddress
import socket
from urllib.parse import urlparse, urljoin

import aiohttp

MAX_IMAGE_BYTES = 10 * 1024 * 1024
FETCH_TIMEOUT = aiohttp.ClientTimeout(total=15)
_MAX_REDIRECTS = 3
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)


class UnsafeUrlError(Exception):
    """The URL failed SSRF validation or response limits."""


async def _resolve_host(host: str) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(
        host, None, type=socket.SOCK_STREAM
    )
    return [info[4][0] for info in infos]


async def validate_public_http_url(url: str) -> None:
    """
    Raise UnsafeUrlError unless url is http(s) and every address its host
    resolves to is public — keeps the bot from fetching internal services.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"scheme {parsed.scheme!r} is not allowed")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no host")
    try:
        addresses = await _resolve_host(parsed.hostname)
    except (socket.gaierror, UnicodeError) as e:
        raise UnsafeUrlError(f"cannot resolve {parsed.hostname!r}") from e
    if not addresses:
        raise UnsafeUrlError(f"cannot resolve {parsed.hostname!r}")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address.split("%")[0])
        except ValueError as e:
            raise UnsafeUrlError(f"unparsable address {address!r}") from e
        if not ip.is_global:
            raise UnsafeUrlError(
                f"{parsed.hostname!r} resolves to a non-public address"
            )


async def fetch_image(url: str, *, max_bytes: int = MAX_IMAGE_BYTES) -> bytes:
    """
    Fetch a user-supplied image URL safely: public hosts only (re-checked on
    every redirect hop), total timeout, size cap, image Content-Type required.
    """
    async with aiohttp.ClientSession(timeout=FETCH_TIMEOUT) as session:
        for _ in range(_MAX_REDIRECTS + 1):
            await validate_public_http_url(url)
            async with session.get(url, allow_redirects=False) as response:
                if response.status in _REDIRECT_STATUSES:
                    location = response.headers.get("Location")
                    if not location:
                        raise UnsafeUrlError("redirect without Location header")
                    url = urljoin(url, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    raise UnsafeUrlError(f"expected an image, got {content_type!r}")
                if response.content_length and response.content_length > max_bytes:
                    raise UnsafeUrlError("image is too large")
                data = bytearray()
                async for chunk in response.content.iter_chunked(64 * 1024):
                    data.extend(chunk)
                    if len(data) > max_bytes:
                        raise UnsafeUrlError("image is too large")
                return bytes(data)
    raise UnsafeUrlError("too many redirects")
