"""游程编码 (RLE) 压缩与解压缩模块。

二进制 RLE 格式
-----------------
编码流为 (count, byte) 对序列：
每个 run 使用固定 2 字节小端序 count + 1 字节数据值（共 3 字节）编码。
最大游程长度为 65535。

布局：[count_lo][count_hi][byte_value] 循环重复...
"""

from __future__ import annotations

import struct

# 每个 run 编码为：2 字节小端序 count + 1 字节 value = 3 字节。
_RUN_STRUCT = struct.Struct("<HB")  # 无符号短整型 + 无符号字符
_MAX_RUN = 0xFFFF  # 65535


def compress(data: bytes) -> bytes:
    """使用 RLE 算法压缩数据。

    返回
    -------
    bytes
        RLE 编码后的字节流。
    """
    if not data:
        return b""

    parts: list[bytes] = []
    prev = data[0]
    count = 1

    for byte in data[1:]:
        if byte == prev and count < _MAX_RUN:
            count += 1
        else:
            # 输出当前游程
            parts.append(_RUN_STRUCT.pack(count, prev))
            prev = byte
            count = 1

    # 输出最后一个游程
    parts.append(_RUN_STRUCT.pack(count, prev))
    return b"".join(parts)


def decompress(data: bytes) -> bytes:
    """解压 RLE 编码后的字节流。

    异常
    ------
    ValueError
        如果数据长度不是 3 的倍数（流损坏）。
    """
    run_size = _RUN_STRUCT.size  # 3
    if len(data) % run_size != 0:
        raise ValueError(
            f"Corrupted RLE data: length {len(data)} is not a multiple of {run_size}"
        )

    parts: list[bytes] = []
    for offset in range(0, len(data), run_size):
        count, value = _RUN_STRUCT.unpack_from(data, offset)
        parts.append(bytes([value]) * count)
    return b"".join(parts)
