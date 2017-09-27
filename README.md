## btc_parser

解析比特币的块文件的工具

### 钱包目录结构

### 块文件结构
在**.dat文件中，存储了比特币区块链的信息

比特币的块结构如下

| 大小(字节) | 名称 | 数据类型 |描述|
| -------- | ---- | ------ | -- |
| 4 | magic_number | uint32 | 总是0xD9B4BEF9,作为区块之间的分隔符 |
| 4 | block_size | uint32 | 后面数据到块结束的字节数 |
| 80 | block_header | char[] | block header |
| varies | transaction_cnt | uint | 交易数量 |
| varies | transaction | char[] | 交易详情 |


block header的结构如下

| 大小(字节) |  名称    |               数据类型  |      描述  |
| --------- | ------- | ---------------------- | ---------- |
|4 |          version            |   int32_t     |   版本号 |
|32 |         previous_block_hash  | char[32]   |    前一个block的hash值 |
|32    |      merkle_root_hash   |   char[32]    |   区块内所有交易的merkle hash值 |
|4     |      time            |      uint32     |    unix时间戳，矿工挖矿的时间 |
|4       |    nBits        |         uint32      |   该块的标题hash必须小于的值。难度 |
| 4       |    nonce        |         uint32     |    随机值，用于产生满足难度的hash值 |


交易的结构如下

|大小(字节) | 名称     |                 数据类型      |      描述 |
|4       |   version        |          uint32        |     交易版本号|
|varies   |  tx_in_count     |         uint        |       交易输入数量|
|varies   |  tx_in        |            tx_in      |        交易输入|
|varies  |   tx_out_count    |         uint    |           交易输出数量|
|varies    | tx_out          |         tx_out      |       交易输出|
|4        |  lock_time        |        uint32      |       锁定时间|


交易输入的结构如下

|大小(字节) | 名称         |             数据类型    |        描述|
|32       |  previous_output_hash |    outpoint       |    前置交易hash|
|4       |   previous_output_index|    uint32        |     前置交易index|
|varint   |  script_bytes    |         uint     |          解锁脚本长度|
|varies    | signature_script   |      char[]     |        解锁脚本|
|4       |   sequence     |            uint32    |         序列号|


交易输出的结构如下

|大小(字节) | 名称         |             数据类型     |       描述|
|8       |   value        |            int64   |           花费的数量，单位是聪|
|1+     |    pk_script_size  |         uint    |           pubkey脚本中的字节数量|
|varies   |  pk_script       |         char[]   |          花费这笔输出需要满足的条件|
