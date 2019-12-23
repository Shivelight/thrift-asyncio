#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#

from .TProtocol import TType, TProtocolBase, TProtocolException, TProtocolFactory, checkIntegerLimits
from struct import pack, unpack

from ..compat import binary_to_str, str_to_binary

__all__ = ['TCompactProtocol', 'TCompactProtocolFactory']

CLEAR = 0
FIELD_WRITE = 1
VALUE_WRITE = 2
CONTAINER_WRITE = 3
BOOL_WRITE = 4
FIELD_READ = 5
CONTAINER_READ = 6
VALUE_READ = 7
BOOL_READ = 8


def make_helper(v_from, container):
    def helper(func):
        def nested(self, *args, **kwargs):
            assert self.state in (v_from, container), (self.state, v_from, container)
            return func(self, *args, **kwargs)
        return nested
    return helper


writer = make_helper(VALUE_WRITE, CONTAINER_WRITE)
reader = make_helper(VALUE_READ, CONTAINER_READ)


def makeZigZag(n, bits):
    checkIntegerLimits(n, bits)
    return (n << 1) ^ (n >> (bits - 1))


def fromZigZag(n):
    return (n >> 1) ^ -(n & 1)


def writeVarint(trans, n):
    assert n >= 0, "Input to TCompactProtocol writeVarint cannot be negative!"
    out = bytearray()
    while True:
        if n & ~0x7f == 0:
            out.append(n)
            break
        else:
            out.append((n & 0xff) | 0x80)
            n = n >> 7
    trans.write(bytes(out))


def readVarint(trans):
    result = 0
    shift = 0
    while True:
        x = trans.readAll(1)
        byte = ord(x)
        result |= (byte & 0x7f) << shift
        if byte >> 7 == 0:
            return result
        shift += 7


class CompactType(object):
    STOP = 0x00
    TRUE = 0x01
    FALSE = 0x02
    BYTE = 0x03
    I16 = 0x04
    I32 = 0x05
    I64 = 0x06
    DOUBLE = 0x07
    BINARY = 0x08
    LIST = 0x09
    SET = 0x0A
    MAP = 0x0B
    STRUCT = 0x0C


CTYPES = {
    TType.STOP: CompactType.STOP,
    TType.BOOL: CompactType.TRUE,  # used for collection
    TType.BYTE: CompactType.BYTE,
    TType.I16: CompactType.I16,
    TType.I32: CompactType.I32,
    TType.I64: CompactType.I64,
    TType.DOUBLE: CompactType.DOUBLE,
    TType.STRING: CompactType.BINARY,
    TType.STRUCT: CompactType.STRUCT,
    TType.LIST: CompactType.LIST,
    TType.SET: CompactType.SET,
    TType.MAP: CompactType.MAP,
}

TTYPES = {}
for k, v in CTYPES.items():
    TTYPES[v] = k
TTYPES[CompactType.FALSE] = TType.BOOL
del k
del v


class TCompactProtocol(TProtocolBase):
    """Compact implementation of the Thrift protocol driver."""

    PROTOCOL_ID = 0x82
    VERSION = 1
    VERSION_MASK = 0x1f
    TYPE_MASK = 0xe0
    TYPE_BITS = 0x07
    TYPE_SHIFT_AMOUNT = 5

    def __init__(self, trans,
                 string_length_limit=None,
                 container_length_limit=None):
        TProtocolBase.__init__(self, trans)
        self.state = CLEAR
        self._last_fid = 0
        self._bool_fid = None
        self._bool_value = None
        self._structs = []
        self._containers = []
        self.string_length_limit = string_length_limit
        self.container_length_limit = container_length_limit

    def _check_string_length(self, length):
        self._check_length(self.string_length_limit, length)

    def _check_container_length(self, length):
        self._check_length(self.container_length_limit, length)

    def _writeVarint(self, n):
        writeVarint(self.trans, n)

    def writeMessageBegin(self, name, type, seqid):
        assert self.state == CLEAR
        self._writeUByte(self.PROTOCOL_ID)
        self._writeUByte(self.VERSION | (type << self.TYPE_SHIFT_AMOUNT))
        # The sequence id is a signed 32-bit integer but the compact protocol
        # writes this out as a "var int" which is always positive, and attempting
        # to write a negative number results in an infinite loop, so we may
        # need to do some conversion here...
        tseqid = seqid
        if tseqid < 0:
            tseqid = 2147483648 + (2147483648 + tseqid)
        self._writeVarint(tseqid)
        self._writeBinary(str_to_binary(name))
        self.state = VALUE_WRITE

    def writeMessageEnd(self):
        assert self.state == VALUE_WRITE
        self.state = CLEAR

    def writeStructBegin(self, name):
        assert self.state in (CLEAR, CONTAINER_WRITE, VALUE_WRITE), self.state
        self._structs.append((self.state, self._last_fid))
        self.state = FIELD_WRITE
        self._last_fid = 0

    def writeStructEnd(self):
        assert self.state == FIELD_WRITE
        self.state, self._last_fid = self._structs.pop()

    def writeFieldStop(self):
        self._writeByte(0)

    def _writeFieldHeader(self, type, fid):
        delta = fid - self._last_fid
        if 0 < delta <= 15:
            self._writeUByte(delta << 4 | type)
        else:
            self._writeByte(type)
            self._writeI16(fid)
        self._last_fid = fid

    def writeFieldBegin(self, name, type, fid):
        assert self.state == FIELD_WRITE, self.state
        if type == TType.BOOL:
            self.state = BOOL_WRITE
            self._bool_fid = fid
        else:
            self.state = VALUE_WRITE
            self._writeFieldHeader(CTYPES[type], fid)

    def writeFieldEnd(self):
        assert self.state in (VALUE_WRITE, BOOL_WRITE), self.state
        self.state = FIELD_WRITE

    def _writeUByte(self, byte):
        self.trans.write(pack('!B', byte))

    def _writeByte(self, byte):
        self.trans.write(pack('!b', byte))

    def _writeI16(self, i16):
        self._writeVarint(makeZigZag(i16, 16))

    def _writeSize(self, i32):
        self._writeVarint(i32)

    def writeCollectionBegin(self, etype, size):
        assert self.state in (VALUE_WRITE, CONTAINER_WRITE), self.state
        if size <= 14:
            self._writeUByte(size << 4 | CTYPES[etype])
        else:
            self._writeUByte(0xf0 | CTYPES[etype])
            self._writeSize(size)
        self._containers.append(self.state)
        self.state = CONTAINER_WRITE
    writeSetBegin = writeCollectionBegin
    writeListBegin = writeCollectionBegin

    def writeMapBegin(self, ktype, vtype, size):
        assert self.state in (VALUE_WRITE, CONTAINER_WRITE), self.state
        if size == 0:
            self._writeByte(0)
        else:
            self._writeSize(size)
            self._writeUByte(CTYPES[ktype] << 4 | CTYPES[vtype])
        self._containers.append(self.state)
        self.state = CONTAINER_WRITE

    def writeCollectionEnd(self):
        assert self.state == CONTAINER_WRITE, self.state
        self.state = self._containers.pop()
    writeMapEnd = writeCollectionEnd
    writeSetEnd = writeCollectionEnd
    writeListEnd = writeCollectionEnd

    def writeBool(self, bool):
        if self.state == BOOL_WRITE:
            if bool:
                ctype = CompactType.TRUE
            else:
                ctype = CompactType.FALSE
            self._writeFieldHeader(ctype, self._bool_fid)
        elif self.state == CONTAINER_WRITE:
            if bool:
                self._writeByte(CompactType.TRUE)
            else:
                self._writeByte(CompactType.FALSE)
        else:
            raise AssertionError("Invalid state in compact protocol")

    writeByte = writer(_writeByte)
    writeI16 = writer(_writeI16)

    @writer
    def writeI32(self, i32):
        self._writeVarint(makeZigZag(i32, 32))

    @writer
    def writeI64(self, i64):
        self._writeVarint(makeZigZag(i64, 64))

    @writer
    def writeDouble(self, dub):
        self.trans.write(pack('<d', dub))

    def _writeBinary(self, s):
        self._writeSize(len(s))
        self.trans.write(s)
    writeBinary = writer(_writeBinary)

    def readFieldBegin(self):
        assert self.state == FIELD_READ, self.state
        type = self._readUByte()
        if type & 0x0f == TType.STOP:
            return (None, 0, 0)
        delta = type >> 4
        if delta == 0:
            fid = self._readI16()
        else:
            fid = self._last_fid + delta
        self._last_fid = fid
        type = type & 0x0f
        if type == CompactType.TRUE:
            self.state = BOOL_READ
            self._bool_value = True
        elif type == CompactType.FALSE:
            self.state = BOOL_READ
            self._bool_value = False
        else:
            self.state = VALUE_READ
        return (None, self._getTType(type), fid)

    def readFieldEnd(self):
        assert self.state in (VALUE_READ, BOOL_READ), self.state
        self.state = FIELD_READ

    def _readUByte(self):
        result, = unpack('!B', self.trans.readAll(1))
        return result

    def _readByte(self):
        result, = unpack('!b', self.trans.readAll(1))
        return result

    def _readVarint(self):
        return readVarint(self.trans)

    def _readZigZag(self):
        return fromZigZag(self._readVarint())

    def _readSize(self):
        result = self._readVarint()
        if result < 0:
            raise TProtocolException("Length < 0")
        return result

    def readMessageBegin(self):
        assert self.state == CLEAR
        proto_id = self._readUByte()
        if proto_id != self.PROTOCOL_ID:
            raise TProtocolException(TProtocolException.BAD_VERSION,
                                     'Bad protocol id in the message: %d' % proto_id)
        ver_type = self._readUByte()
        type = (ver_type >> self.TYPE_SHIFT_AMOUNT) & self.TYPE_BITS
        version = ver_type & self.VERSION_MASK
        if version != self.VERSION:
            raise TProtocolException(TProtocolException.BAD_VERSION,
                                     'Bad version: %d (expect %d)' % (version, self.VERSION))
        seqid = self._readVarint()
        # the sequence is a compact "var int" which is treaded as unsigned,
        # however the sequence is actually signed...
        if seqid > 2147483647:
            seqid = -2147483648 - (2147483648 - seqid)
        name = binary_to_str(self._readBinary())
        return (name, type, seqid)

    def readMessageEnd(self):
        assert self.state == CLEAR
        assert len(self._structs) == 0

    def readStructBegin(self):
        assert self.state in (CLEAR, CONTAINER_READ, VALUE_READ), self.state
        self._structs.append((self.state, self._last_fid))
        self.state = FIELD_READ
        self._last_fid = 0

    def readStructEnd(self):
        assert self.state == FIELD_READ
        self.state, self._last_fid = self._structs.pop()

    def readCollectionBegin(self):
        assert self.state in (VALUE_READ, CONTAINER_READ), self.state
        size_type = self._readUByte()
        size = size_type >> 4
        type = self._getTType(size_type)
        if size == 15:
            size = self._readSize()
        self._check_container_length(size)
        self._containers.append(self.state)
        self.state = CONTAINER_READ
        return type, size
    readSetBegin = readCollectionBegin
    readListBegin = readCollectionBegin

    def readMapBegin(self):
        assert self.state in (VALUE_READ, CONTAINER_READ), self.state
        size = self._readSize()
        self._check_container_length(size)
        types = 0
        if size > 0:
            types = self._readUByte()
        vtype = self._getTType(types)
        ktype = self._getTType(types >> 4)
        self._containers.append(self.state)
        self.state = CONTAINER_READ
        return (ktype, vtype, size)

    def readCollectionEnd(self):
        assert self.state == CONTAINER_READ, self.state
        self.state = self._containers.pop()
    readSetEnd = readCollectionEnd
    readListEnd = readCollectionEnd
    readMapEnd = readCollectionEnd

    def readBool(self):
        if self.state == BOOL_READ:
            return self._bool_value == CompactType.TRUE
        elif self.state == CONTAINER_READ:
            return self._readByte() == CompactType.TRUE
        else:
            raise AssertionError("Invalid state in compact protocol: %d" %
                                 self.state)

    readByte = reader(_readByte)
    __readI16 = _readZigZag
    readI16 = reader(_readZigZag)
    readI32 = reader(_readZigZag)
    readI64 = reader(_readZigZag)

    @reader
    def readDouble(self):
        buff = self.trans.readAll(8)
        val, = unpack('<d', buff)
        return val

    def _readBinary(self):
        size = self._readSize()
        self._check_string_length(size)
        return self.trans.readAll(size)
    readBinary = reader(_readBinary)

    def _getTType(self, byte):
        return TTYPES[byte & 0x0f]


class TCompactProtocolFactory(TProtocolFactory):
    def __init__(self,
                 string_length_limit=None,
                 container_length_limit=None):
        self.string_length_limit = string_length_limit
        self.container_length_limit = container_length_limit

    def getProtocol(self, trans):
        return TCompactProtocol(trans,
                                self.string_length_limit,
                                self.container_length_limit)


class TCompactProtocolAccelerated(TCompactProtocol):
    """C-Accelerated version of TCompactProtocol.

    This class does not override any of TCompactProtocol's methods,
    but the generated code recognizes it directly and will call into
    our C module to do the encoding, bypassing this object entirely.
    We inherit from TCompactProtocol so that the normal TCompactProtocol
    encoding can happen if the fastbinary module doesn't work for some
    reason.
    To disable this behavior, pass fallback=False constructor argument.

    In order to take advantage of the C module, just use
    TCompactProtocolAccelerated instead of TCompactProtocol.
    """
    pass

    def __init__(self, *args, **kwargs):
        fallback = kwargs.pop('fallback', True)
        super(TCompactProtocolAccelerated, self).__init__(*args, **kwargs)
        try:
            from thrift.protocol import fastbinary
        except ImportError:
            if not fallback:
                raise
        else:
            self._fast_decode = fastbinary.decode_compact
            self._fast_encode = fastbinary.encode_compact


class TCompactProtocolAcceleratedFactory(TProtocolFactory):
    def __init__(self,
                 string_length_limit=None,
                 container_length_limit=None,
                 fallback=True):
        self.string_length_limit = string_length_limit
        self.container_length_limit = container_length_limit
        self._fallback = fallback

    def getProtocol(self, trans):
        return TCompactProtocolAccelerated(
            trans,
            string_length_limit=self.string_length_limit,
            container_length_limit=self.container_length_limit,
            fallback=self._fallback)
