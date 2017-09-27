#!/usr/bin/env python
# coding=utf-8
import sys
import mmap
import struct
from btc import Block

BITCOIN_CONSTANT = b"\xf9\xbe\xb4\xd9"


def parse_from_file(raw_data):
    length = len(raw_data)
    offset = 0
    while offset < (length-4):
        if raw_data[offset: offset+4] == BITCOIN_CONSTANT:
            offset += 4
            size = struct.unpack("<I", raw_data[offset:offset+4])[0]
            offset += 4+size
            block = Block().parse_from_hex(raw_data[offset-8-size: offset])
            print(block)
        else:
            offset += 1


if __name__ == '__main__':
    blk_file_path = sys.argv[1]
    with open(blk_file_path, 'rb') as f:
        raw_data = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        parse_from_file(raw_data)

