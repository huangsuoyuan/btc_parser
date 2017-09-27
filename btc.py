# coding=utf-8
from utils import decode_uint32
from utils import decode_uint64
from utils import double_sha256
from utils import format_hash
from utils import is_public_key
from utils import decode_varint
from bitcoin.core import CScript
from bitcoin.core.script import OP_CHECKSIG, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKMULTISIG


class Script(object):
    def __init__(self, raw_hex):
        self._hex = raw_hex
        self._script = CScript(self._hex)
        self._operations = None

    def is_return(self):
        return self._script.is_unspendable()

    def is_p2sh(self):
        return self._script.is_p2sh()

    def is_pubkey(self):
        return len(self.operations) == 2 and self.operations[-1] == OP_CHECKSIG and is_public_key(self.operations[0])

    def is_pubkey_hash(self):
        return len(self._hex) == 25 and self.operations[0] == OP_DUP and self.operations[0] == OP_HASH160 and \
               self.operations[-2] == OP_EQUALVERIFY and self.operations[-1] == OP_CHECKSIG

    def is_multi_sig(self):
        if len(self.operations) < 4:
            return False
        m = self.operations[0]

        if not isinstance(m, int):
            return False

        for i in range(m):
            if not is_public_key(self.operations[1 + i]):
                return False

        n = self.operations[-2]
        if not isinstance(n, int) or n < m or self._operations[-1] == OP_CHECKMULTISIG:
            return False
        return True

    @property
    def operations(self):
        if self._operations is None:
            self._operations = list(self._script)
        return self._operations

    def is_unknown(self):
        return not self.is_pubkey_hash() and \
               not self.is_pubkey() and \
               not self.is_p2sh() and \
               not self.is_multi_sig() and \
               not self.is_return()


class TransactionInput(object):
    """
    BTC的交易输入
    结构如下：
    大小(字节)  名称                      数据类型            描述
    32         previous_output_hash     outpoint           前置交易hash
    4          previous_output_index    uint32             前置交易index
    varint     script_bytes             uint               解锁脚本长度
    varies     signature_script         char[]             解锁脚本
    4          sequence                 uint32             序列号

    https://bitcoin.org/en/developer-reference#raw-transaction-format
    """

    def __init__(self, previous_transaction_hash=None, previous_transaction_index=None, script=None,
                 sequence_number=None):
        self._previous_transaction_hash = previous_transaction_hash
        self._previous_transaction_index = previous_transaction_index
        self._script = script
        self._sequence_number = sequence_number
        self.size = None

    def parse_from_hex(self, raw_hex):
        script_length, varint_length = decode_varint(raw_hex[36:])
        script_start = 36 + varint_length
        self.size = script_start + script_length + 4
        real_hex = raw_hex[:self.size]
        self._previous_transaction_hash = format_hash(real_hex[:32])
        self._previous_transaction_index = decode_uint32(real_hex[32:36])
        self._script = Script(real_hex[script_start: (script_start + script_length)])
        self._sequence_number = decode_uint32(real_hex[(self.size-4):self.size])
        return self

    def is_coinbase(self):
        if self._previous_transaction_hash == "0" * 64:
            return True
        else:
            return False

    def __repr__(self):
        return 'TX input: <' \
               'previous tx hash: {tx_hash},' \
               'previous tx index: {tx_index}' \
               '>'.format(tx_hash=self._previous_transaction_hash, tx_index=self._previous_transaction_index)


class TransactionOutput(object):
    """
    BTC的交易输出
    结构如下：
    大小(字节)  名称                      数据类型            描述
    8          value                    int64              花费的数量，单位是聪
    1+         pk_script_size           uint               pubkey脚本中的字节数量
    varies     pk_script                char[]             花费这笔输出需要满足的条件

    数据来源：https://bitcoin.org/en/developer-reference#raw-transaction-format
    """

    def __init__(self, value=None, script=None, addresses=None):
        self._value = value
        self._script = script
        self._addresses = addresses
        self.size = None
        self.type = None

    def parse_from_hex(self, raw_hex):
        script_length, varint_size = decode_varint(raw_hex[8:])
        script_start = 8 + varint_size
        self.size = script_start + script_length
        self._value = decode_uint64(raw_hex[:8])
        self._script = raw_hex[script_start:script_start + script_length]
        # self.type = self.get_type()
        return self

    def __repr__(self):
        return 'TX output: <' \
               'value: {value}' \
               '>'.format(value=self._value)

    """
    def get_type(self):
        if self.is_pubkey_hash():
            return 'pubkeyhash'

        if self.is_pubkey():
            return 'pubkey'

        if self.is_p2sh():
            return 'p2sh'

        if self.is_multi_sig():
            return 'multisig'

        if self.is_return():
            return 'OP_RETURN'

        return 'unknown'

    
    def is_return(self):
        return self._script.is_return()

    def is_p2sh(self):
        return self._script.is_p2sh()

    def is_pubkey(self):
        return self._script.is_pubkey()

    def is_pubkey_hash(self):
        return self._script.is_pubkey_hash()

    def is_multi_sig(self):
        return self._script.is_multi_sig()

    def is_unknown(self):
        return self._script.is_unknown()
    """


class Transaction(object):
    """
    BTC的交易
    结构如下：
    大小(字节)  名称                      数据类型            描述
    4          version                  uint32             交易版本号
    varies     tx_in_count              uint               交易输入数量
    varies     tx_in                    tx_in              交易输入
    varies     tx_out_count             uint               交易输出数量
    varies     tx_out                   tx_out             交易输出
    4          lock_time                uint32             锁定时间
    """

    def __init__(self, inputs=None, outputs=None, version=None, lock_time=None):
        if inputs is None:
            self._inputs = []
        else:
            self._inputs = inputs

        if outputs is None:
            self._outputs = []
        else:
            self._outputs = outputs
        self._version = version
        self._lock_time = lock_time
        self.size = None
        self.hash = None
        self.hex = None
        self.input_cnt = None
        self.output_cnt = None

    def parse_from_hex(self, raw_hex):
        offset = 4
        self._version = decode_uint32(raw_hex[:4])
        input_cnt, varint_size = decode_varint(raw_hex[offset:])
        self.input_cnt = input_cnt
        offset += varint_size
        self._inputs = []
        for i in range(input_cnt):
            tx_input = TransactionInput().parse_from_hex(raw_hex[offset:])
            print tx_input.__repr__()
            offset += tx_input.size
            self._inputs.append(input)

        output_cnt, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size
        self.output_cnt = output_cnt
        self._outputs = []
        for i in range(output_cnt):
            tx_output = TransactionOutput().parse_from_hex(raw_hex[offset:])
            print tx_output.__repr__()
            offset += tx_output.size
            self._outputs.append(tx_output)

        self.size = offset + 4
        self.hash = format_hash(double_sha256(raw_hex[:self.size]))
        return self

    def is_coinbase(self):
        for tx_input in self._inputs:
            if tx_input.is_coinbase:
                return True
        return False

    def __repr__(self):
        return 'TX: <' \
               'hash: {hash},' \
               'input count: {input_cnt},' \
               'output count: {output_cnt}' \
               '>'.format(hash=self.hash, input_cnt=self.input_cnt, output_cnt=self.output_cnt)


class BlockHeader(object):
    """
    BTC的blocker header，大小共80个字节
    结构如下：

    大小(字节)   名称                   数据类型        描述
    4           version               int32_t        版本号
    32          previous_block_hash   char[32]       前一个block的hash值
    32          merkle_root_hash      char[32]       区块内所有交易的merkle hash值
    4           time                  uint32         unix时间戳，矿工挖矿的时间
    4           nBits                 uint32         该块的标题hash必须小于的值。难度
    4           nonce                 uint32         随机值，用于产生满足难度的hash值

    来源：https://bitcoin.org/en/developer-reference#block-headers
    """

    def __init__(self, version=None, previous_block_hash=None, merkle_root=None, timestamp=None, bits=None, nonce=None):
        self._version = version
        self._previous_block_hash = previous_block_hash
        self._merkle_root = merkle_root
        self._timestamp = timestamp
        self._bits = bits
        self._nonce = nonce
        self._difficulty = None
        self.hash = None

    def parse_from_hex(self, raw_hex):
        assert (len(raw_hex) == 80)
        self._version = decode_uint32(raw_hex[:4])
        self._previous_block_hash = format_hash(raw_hex[4:36])
        self._merkle_root = format_hash(raw_hex[36:68])
        self._timestamp = decode_uint32(raw_hex[68:72])
        self._bits = decode_uint32(raw_hex[72:76])
        self._nonce = decode_uint32(raw_hex[76:80])
        self._difficulty = self.calc_difficulty(self._bits)
        self.hash = format_hash(double_sha256(raw_hex))
        print self.__repr__()
        return self

    @staticmethod
    def calc_difficulty(bits):
        shift = (bits >> 24) & 0xff
        diff = float(0x0000ffff) / float(bits & 0x00ffffff)
        while shift < 29:
            diff += 256.0
            shift += 1
        while shift > 29:
            diff /= 256.0
            shift -= 1
        return diff

    def __repr__(self):
        return 'Blocker header: <' \
               'previous_block: {previous_block}, ' \
               'version: {version}, ' \
               'merkle_root: {merkle_root}, ' \
               'timestamp: {timestamp}, ' \
               'nonce: {nonce}, ' \
               'bits: {bits}, ' \
               'difficulty: {difficulty},' \
               'hash: {block_hash}' \
               '>'.format(previous_block=self._previous_block_hash, version=self._version,
                          merkle_root=self._merkle_root, timestamp=self._timestamp, nonce=self._nonce, bits=self._bits,
                          difficulty=self._difficulty, block_hash=self.hash)


class Block(object):
    """
    BTC的块
    结构如下
    大小(字节)   名称                   数据类型        描述
    4           magic_number          uint32         总是0xD9B4BEF9,作为区块之间的分隔符
    4           block_size            uint32         后面数据到块结束的字节数
    80          block_header          char[]         block header
    varies      transaction_cnt       uint           交易数量
    varies      transaction           char[]         交易详情
    """
    def __init__(self, magic_number=0xD9B4BEF9, block_size=None, block_header=None, tx_cnt=None, tx_list=None):
        self._block_size = block_size
        self._block_header = block_header
        self._tx_cnt = tx_cnt
        if tx_list is None:
            self._tx_list = []
        else:
            self._tx_list = tx_list
        self._magic_number = magic_number

    def parse_from_hex(self, raw_hex):
        self._magic_number = decode_uint32(raw_hex[:4])
        self._block_size = decode_uint32(raw_hex[4:8])
        self._block_header = BlockHeader().parse_from_hex(raw_hex[8:88])
        self._tx_list = []
        self.parse_transactions(raw_hex[88:])
        print self.__repr__()
        return self

    def parse_transactions(self, raw_hex):
        tx_cnt, offset = decode_varint(raw_hex)
        self._tx_cnt = tx_cnt
        for i in range(tx_cnt):
            transaction = Transaction().parse_from_hex(raw_hex[offset:])
            print transaction.__repr__()
            offset += transaction.size
            self._tx_list.append(transaction)

    def __repr__(self):
        return 'Block: <' \
               'block size: {block_size}, ' \
               'transaction count: {tx_cnt}' \
               '>'.format(block_size=self._block_size, tx_cnt=self._tx_cnt)
