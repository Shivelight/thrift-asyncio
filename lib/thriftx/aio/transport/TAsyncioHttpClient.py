from io import BytesIO

from .TAsyncioTransport import TAsyncioTransportBase


def _missing_dep(msg):
    class _MissingDependencies:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(msg)

    return _MissingDependencies


try:
    from aiohttp import ClientSession, TCPConnector
    from aiohttp.resolver import AsyncResolver

    class TAsyncioAiohttpClient(TAsyncioTransportBase):
        """Aiohttp implementation of asyncio http client."""

        def __init__(self, url, session=None):
            self.url = url
            if session is None:
                # Explicitly use async resolver to keep aiohttp from using
                # threaded resolver which causing memory leak (or not)
                # because the spawned thread doesn't terminate.
                async_dns = AsyncResolver()
                # AsyncResolver has problems related to domains with IPv6.
                # If you can't connect or network is unreachable try this
                # solution: https://stackoverflow.com/a/48008873
                tcp = TCPConnector(resolver=async_dns)
                self._session = ClientSession(connector=tcp)
            else:
                self._session = session

            self._wbuf = BytesIO()
            self._http_response = None
            self._default_headers = {
                "Content-Type": "application/x-thrift",
                "User-Agent": "Python/TAsyncioAiohttpClient",
            }
            self._custom_headers = self._headers

        def setCustomHeaders(self, headers):
            self._custom_headers = {**self._default_headers, **headers}

        def write(self, buf):
            self._wbuf.write(buf)

        async def read(self, sz):
            return await self._http_response.content.read(sz)

        async def flush(self):
            data = self._wbuf.getvalue()
            self._wbuf = BytesIO()

            self._http_response = await self._session.post(
                self.url, data=data, headers=self._custom_headers
            )
            self.code = self._http_response.status
            self.message = self._http_response.reason
            self.headers = self._http_response.headers

        async def close(self):
            await self._session.close()


except ImportError:
    TAsyncioAiohttpClient = _missing_dep(
        "Please install `aiohttp` and `aiodns` or `aiohttp[speedups]`"
    )
