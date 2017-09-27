# coding=utf-8
import hashlib
import struct
import sys
from binascii import hexlify

if sys.version > '3':
    to_int = lambda x: int(x)
else:
    to_int = ord


def format_hash(data):
    return str(hexlify(data[::-1]).decode('utf-8'))


def decode_uint32(data):
    assert(len(data) == 4)
    return struct.unpack("<I", data)[0]


def decode_uint64(data):
    assert(len(data) == 8)
    return struct.unpack("<Q", data)[0]


def decode_varint(data):
    assert(len(data) > 0)
    size = to_int(data[0])
    assert(size <= 255)

    if size < 253:
        return size, 1

    format_ = None
    if size == 253:
        format_ = '<H'
    elif size == 254:
        format_ = '<I'
    elif size == 255:
        format_ = '<Q'
    else:
        assert 0, 'unknown format_ for size: {size}'.format(size=size)
    size = struct.calcsize(format_)
    return struct.unpack(format_, data[1:size+1])[0], size + 1


def is_public_key(hex_data):
    """
    检查16进制数据是否符合公钥地址格式
    :param hex_data:
    :return:
    """
    if type(hex_data) != bytes:
        return False

    if len(hex_data) == 65 and to_int(hex_data[0]) == 4:
        return True

    if len(hex_data) == 33 and to_int(hex_data[0]) in (2, 3):
        return True

    return False


def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()
