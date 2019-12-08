from thrift.transport import TTransport


class TAsyncioTransportBase(TTransport.TTransportBase):
    """Base class for Thrift asyncio transport layer."""

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
