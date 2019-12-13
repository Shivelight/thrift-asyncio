from struct import unpack

from thrift.protocol.TBinaryProtocol import TBinaryProtocol, TBinaryProtocolFactory
from thrift.protocol.TProtocol import TProtocolException
from thrift.Thrift import TType


class TAsyncioBinaryProtocol(TBinaryProtocol):
    """Binary implementation of the Thrift asyncio protocol driver."""

    async def readMessageBegin(self):
        sz = await self.readI32()
        if sz < 0:
            version = sz & TBinaryProtocol.VERSION_MASK
            if version != TBinaryProtocol.VERSION_1:
                raise TProtocolException(
                    type=TProtocolException.BAD_VERSION,
                    message="Bad version in readMessageBegin: %d" % (sz),
                )
            type = sz & TBinaryProtocol.TYPE_MASK
            name = await self.readString()
            seqid = await self.readI32()
        else:
            if self.strictRead:
                raise TProtocolException(
                    type=TProtocolException.BAD_VERSION,
                    message="No protocol version header",
                )
            name = await self.trans.readAll(sz)
            type = await self.readByte()
            seqid = await self.readI32()
        return (name, type, seqid)

    async def readMessageEnd(self):
        pass

    async def readStructBegin(self):
        pass

    async def readStructEnd(self):
        pass

    async def readFieldBegin(self):
        type = await self.readByte()
        if type == TType.STOP:
            return (None, type, 0)
        id = await self.readI16()
        return (None, type, id)

    async def readFieldEnd(self):
        pass

    async def readMapBegin(self):
        ktype = await self.readByte()
        vtype = await self.readByte()
        size = await self.readI32()
        self._check_container_length(size)
        return (ktype, vtype, size)

    async def readMapEnd(self):
        pass

    async def readListBegin(self):
        etype = await self.readByte()
        size = await self.readI32()
        self._check_container_length(size)
        return (etype, size)

    async def readListEnd(self):
        pass

    async def readSetBegin(self):
        etype = await self.readByte()
        size = await self.readI32()
        self._check_container_length(size)
        return (etype, size)

    async def readSetEnd(self):
        pass

    async def readBool(self):
        byte = await self.readByte()
        if byte == 0:
            return False
        return True

    async def readByte(self):
        buff = await self.trans.readAll(1)
        (val,) = unpack("!b", buff)
        return val

    async def readI16(self):
        buff = await self.trans.readAll(2)
        (val,) = unpack("!h", buff)
        return val

    async def readI32(self):
        buff = await self.trans.readAll(4)
        (val,) = unpack("!i", buff)
        return val

    async def readI64(self):
        buff = await self.trans.readAll(8)
        (val,) = unpack("!q", buff)
        return val

    async def readDouble(self):
        buff = await self.trans.readAll(8)
        (val,) = unpack("!d", buff)
        return val

    async def readBinary(self):
        size = await self.readI32()
        self._check_string_length(size)
        s = await self.trans.readAll(size)
        return s

    async def skip(self, ttype):
        if ttype == TType.BOOL:
            await self.readBool()
        elif ttype == TType.BYTE:
            await self.readByte()
        elif ttype == TType.I16:
            await self.readI16()
        elif ttype == TType.I32:
            await self.readI32()
        elif ttype == TType.I64:
            await self.readI64()
        elif ttype == TType.DOUBLE:
            await self.readDouble()
        elif ttype == TType.STRING:
            await self.readString()
        elif ttype == TType.STRUCT:
            name = await self.readStructBegin()
            while True:
                (name, ttype, id) = await self.readFieldBegin()
                if ttype == TType.STOP:
                    break
                await self.skip(ttype)
                await self.readFieldEnd()
            await self.readStructEnd()
        elif ttype == TType.MAP:
            (ktype, vtype, size) = await self.readMapBegin()
            for _ in range(size):
                await self.skip(ktype)
                await self.skip(vtype)
            await self.readMapEnd()
        elif ttype == TType.SET:
            (etype, size) = await self.readSetBegin()
            for _ in range(size):
                await self.skip(etype)
            await self.readSetEnd()
        elif ttype == TType.LIST:
            (etype, size) = await self.readListBegin()
            for _ in range(size):
                await self.skip(etype)
            await self.readListEnd()
        else:
            raise TProtocolException(TProtocolException.INVALID_DATA, "invalid TType")


class TAsyncioBinaryProtocolFactory(TBinaryProtocolFactory):
    def getProtocol(self, trans):
        prot = TAsyncioBinaryProtocol(
            trans,
            self.strictRead,
            self.strictWrite,
            string_length_limit=self.string_length_limit,
            container_length_limit=self.container_length_limit,
        )
        return prot
