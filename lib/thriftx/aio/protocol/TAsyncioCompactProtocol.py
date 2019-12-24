from struct import unpack

from thriftx.protocol.TProtocol import TType, TProtocolException
from thriftx.protocol.TCompactProtocol import (
    CompactType,
    TCompactProtocol,
    reader,
    BOOL_READ,
    CLEAR,
    CONTAINER_READ,
    FIELD_READ,
    VALUE_READ,
)


class TAsyncioCompactProtocol(TCompactProtocol):
    async def readFieldBegin(self):
        assert self.state == FIELD_READ, self.state
        type = await self._readUByte()
        if type & 0x0F == TType.STOP:
            return (None, 0, 0)
        delta = type >> 4
        if delta == 0:
            fid = await self._readI16()
        else:
            fid = self._last_fid + delta
        self._last_fid = fid
        type = type & 0x0F
        if type == CompactType.TRUE:
            self.state = BOOL_READ
            self._bool_value = True
        elif type == CompactType.FALSE:
            self.state = BOOL_READ
            self._bool_value = False
        else:
            self.state = VALUE_READ
        return (None, self._getTType(type), fid)

    async def readFieldEnd(self):
        # This function don't have any I/O but it will be awaited.
        # Any function similiar to this is also the same.
        super().readFieldEnd()

    async def _readUByte(self):
        (result,) = unpack("!B", await self.trans.readAll(1))
        return result

    async def _readByte(self):
        (result,) = unpack("!b", await self.trans.readAll(1))
        return result

    async def _readVarint(self):
        # This function is supposed to call readVarint, but I don't
        # understand the reasoning, why would you put a function
        # outside a class and make one and only one function inside
        # a class that call the outside function.
        # I guess "Seems to work".
        result = 0
        shift = 0
        while True:
            x = await self.trans.readAll(1)
            byte = ord(x)
            result |= (byte & 0x7F) << shift
            if byte >> 7 == 0:
                return result
            shift += 7

    async def _readZigZag(self):
        n = await self._readVarint()
        return (n >> 1) ^ -(n & 1)

    async def _readSize(self):
        result = await self._readVarint()
        if result < 0:
            raise TProtocolException("Length < 0")
        return result

    async def readMessageBegin(self):
        assert self.state == CLEAR
        proto_id = await self._readUByte()
        if proto_id != self.PROTOCOL_ID:
            raise TProtocolException(
                TProtocolException.BAD_VERSION,
                "Bad protocol id in the message: %d" % proto_id,
            )
        ver_type = await self._readUByte()
        type = (ver_type >> self.TYPE_SHIFT_AMOUNT) & self.TYPE_BITS
        version = ver_type & self.VERSION_MASK
        if version != self.VERSION:
            raise TProtocolException(
                TProtocolException.BAD_VERSION,
                "Bad version: %d (expect %d)" % (version, self.VERSION),
            )
        seqid = await self._readVarint()
        # the sequence is a compact "var int" which is treaded as unsigned,
        # however the sequence is actually signed...
        if seqid > 2147483647:
            seqid = -2147483648 - (2147483648 - seqid)
        name = await self._readBinary().decode()
        return (name, type, seqid)

    async def readMessageEnd(self):
        super().readMessageEnd()

    async def readStructBegin(self):
        super().readMessageBegin()

    async def readStructEnd(self):
        super().readStructEnd()

    async def readCollectionBegin(self):
        assert self.state in (VALUE_READ, CONTAINER_READ), self.state
        size_type = await self._readUByte()
        size = size_type >> 4
        type = await self._getTType(size_type)
        if size == 15:
            size = await self._readSize()
        self._check_container_length(size)
        self._containers.append(self.state)
        self.state = CONTAINER_READ
        return type, size

    readSetBegin = readCollectionBegin
    readListBegin = readCollectionBegin

    async def readMapBegin(self):
        assert self.state in (VALUE_READ, CONTAINER_READ), self.state
        size = await self._readSize()
        self._check_container_length(size)
        types = 0
        if size > 0:
            types = await self._readUByte()
        vtype = self._getTType(types)
        ktype = self._getTType(types >> 4)
        self._containers.append(self.state)
        self.state = CONTAINER_READ
        return (ktype, vtype, size)

    async def readCollectionEnd(self):
        super().readCollectionEnd()

    readSetEnd = readCollectionEnd
    readListEnd = readCollectionEnd
    readMapEnd = readCollectionEnd

    async def readBool(self):
        if self.state == BOOL_READ:
            return self._bool_value == CompactType.TRUE
        elif self.state == CONTAINER_READ:
            return await self._readByte() == CompactType.TRUE
        else:
            raise AssertionError("Invalid state in compact protocol: %d" % self.state)

    readByte = reader(_readByte)
    _readI16 = _readZigZag
    readI16 = reader(_readZigZag)
    readI32 = reader(_readZigZag)
    readI64 = reader(_readZigZag)

    @reader
    async def readDouble(self):
        buff = await self.trans.readAll(8)
        (val,) = unpack("<d", buff)
        return val

    async def _readBinary(self):
        size = await self._readSize()
        self._check_string_length(size)
        return await self.trans.readAll(size)

    readBinary = reader(_readBinary)

    async def skip(self, ttype):  # noqa
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
