from thriftx.transport import TTransport


class TAsyncioTransportBase(TTransport.TTransportBase):
    """Base class for Thrift asyncio transport layer."""

    def isOpen(self):
        pass

    async def open(self):
        pass

    async def close(self):
        pass

    async def read(self, sz):
        pass

    async def readAll(self, sz):
        buff = b""
        have = 0
        while have < sz:
            chunk = await self.read(sz - have)
            chunkLen = len(chunk)
            have += chunkLen
            buff += chunk

            if chunkLen == 0:
                raise EOFError()

        return buff

    def write(self, buf):
        pass

    async def flush(self):
        pass
