from thrift.Thrift import TApplicationException, TType


class TAsyncioApplicationException(TApplicationException):
    """Application level thrift asyncio exceptions."""

    async def read(self, iprot):
        await iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = await iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.message = await iprot.readString()
                else:
                    await iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.type = await iprot.readI32()
                else:
                    await iprot.skip(ftype)
            else:
                await iprot.skip(ftype)
            await iprot.readFieldEnd()
        await iprot.readStructEnd()
