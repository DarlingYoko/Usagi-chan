from unittest import IsolatedAsyncioTestCase
from unittest import mock

from usagiBot.tests.utils import *


class FakeAsyncContext:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args) -> bool:
        return False


def make_response(
    status: int = 200,
    headers: dict | None = None,
    chunks: tuple = (b"imagedata",),
    content_length: int | None = None,
) -> mock.MagicMock:
    response = mock.MagicMock()
    response.status = status
    response.headers = headers if headers is not None else {"Content-Type": "image/png"}
    response.content_length = content_length

    async def iter_chunked(size):
        for chunk in chunks:
            yield chunk

    response.content.iter_chunked = iter_chunked
    return response


def make_session(responses: list) -> mock.MagicMock:
    session = mock.MagicMock()
    session.get = mock.MagicMock(
        side_effect=[FakeAsyncContext(response) for response in responses]
    )
    return session


class TestValidatePublicHttpUrl(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from usagiBot.src import UsagiNet

        self.UsagiNet = UsagiNet

    async def test_rejects_non_http_scheme(self) -> None:
        with self.assertRaises(self.UsagiNet.UnsafeUrlError):
            await self.UsagiNet.validate_public_http_url("ftp://example.com/a.png")

    async def test_rejects_url_without_host(self) -> None:
        with self.assertRaises(self.UsagiNet.UnsafeUrlError):
            await self.UsagiNet.validate_public_http_url("http://")

    async def _check_rejected(self, addresses: list) -> None:
        with mock.patch.object(
            self.UsagiNet, "_resolve_host", new_callable=mock.AsyncMock
        ) as resolver:
            resolver.return_value = addresses
            with self.assertRaises(self.UsagiNet.UnsafeUrlError):
                await self.UsagiNet.validate_public_http_url("http://host.example/a.png")

    async def test_rejects_loopback(self) -> None:
        await self._check_rejected(["127.0.0.1"])

    async def test_rejects_private_range(self) -> None:
        await self._check_rejected(["10.0.0.5"])

    async def test_rejects_link_local_metadata(self) -> None:
        await self._check_rejected(["169.254.169.254"])

    async def test_rejects_ipv6_loopback(self) -> None:
        await self._check_rejected(["::1"])

    async def test_rejects_mixed_resolution(self) -> None:
        await self._check_rejected(["93.184.216.34", "192.168.0.1"])

    async def test_accepts_public_host(self) -> None:
        with mock.patch.object(
            self.UsagiNet, "_resolve_host", new_callable=mock.AsyncMock
        ) as resolver:
            resolver.return_value = ["93.184.216.34"]
            await self.UsagiNet.validate_public_http_url("https://host.example/a.png")


class TestFetchImage(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from usagiBot.src import UsagiNet

        self.UsagiNet = UsagiNet

    def _patch_session(self, responses: list) -> mock.MagicMock:
        session = make_session(responses)
        patcher = mock.patch.object(
            self.UsagiNet.aiohttp,
            "ClientSession",
            return_value=FakeAsyncContext(session),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return session

    def _patch_resolver(self, table: dict) -> None:
        async def resolve(host):
            return table[host]

        patcher = mock.patch.object(self.UsagiNet, "_resolve_host", side_effect=resolve)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_returns_image_bytes(self) -> None:
        self._patch_resolver({"good.example": ["93.184.216.34"]})
        self._patch_session([make_response(chunks=(b"abc", b"def"))])

        data = await self.UsagiNet.fetch_image("http://good.example/a.png")

        self.assertEqual(data, b"abcdef")

    async def test_rejects_non_image_content_type(self) -> None:
        self._patch_resolver({"good.example": ["93.184.216.34"]})
        self._patch_session(
            [make_response(headers={"Content-Type": "text/html"})]
        )

        with self.assertRaises(self.UsagiNet.UnsafeUrlError):
            await self.UsagiNet.fetch_image("http://good.example/a.png")

    async def test_rejects_redirect_to_private_host(self) -> None:
        self._patch_resolver(
            {"good.example": ["93.184.216.34"], "internal.example": ["127.0.0.1"]}
        )
        self._patch_session(
            [
                make_response(
                    status=302,
                    headers={"Location": "http://internal.example/secret"},
                )
            ]
        )

        with self.assertRaises(self.UsagiNet.UnsafeUrlError):
            await self.UsagiNet.fetch_image("http://good.example/a.png")

    async def test_rejects_oversized_body(self) -> None:
        self._patch_resolver({"good.example": ["93.184.216.34"]})
        self._patch_session([make_response(chunks=(b"x" * 1024,) * 3)])

        with self.assertRaises(self.UsagiNet.UnsafeUrlError):
            await self.UsagiNet.fetch_image(
                "http://good.example/a.png", max_bytes=2048
            )
