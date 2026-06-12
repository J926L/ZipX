"""高级流水线：对文件进行组合 RLE 和 XOR 操作。

支持的工作流
-------------------
* **pack**   : 读取 → RLE 压缩 → XOR 加密 → 写入 ``.zpx``
* **unpack** : 读取 ``.zpx`` → XOR 解密 → RLE 解压 → 写入原始文件

文件头部包含 16 字节 Header 用于解包时验证完整性：

    偏移量  大小  字段说明
    ------  ----  -----
    0       4     魔数 bytes ``ZPX\\x00``
    4       1     版本号     ``0x01``
    5       1     标志位     (保留，0x00)
    6       2     密钥长度   (uint16 LE) — 仅用于验证
    8       4     原始大小   (uint32 LE)
    12      4     原始数据的 SHA-256 校验和 (前 4 字节)
    ------  ----
    16      …     有效载荷 (先经过 RLE 压缩再经过 XOR 加密的字节流)
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

from zipx import crypto, rle

# ── 头部信息 ──────────────────────────────────────────────────────────

MAGIC = b"ZPX\x00"
VERSION = 0x01
_HEADER = struct.Struct("<4sBBHI4s")  # 16 字节
HEADER_SIZE = _HEADER.size

EXTENSION = ".zpx"


@dataclass(frozen=True)
class Header:
    """已解析的 ZPX 文件头部信息。"""

    version: int
    flags: int
    key_length: int
    original_size: int
    checksum: bytes  # SHA-256 的前 4 字节


def _checksum(data: bytes) -> bytes:
    """计算数据 SHA-256 并返回前 4 字节。"""
    return hashlib.sha256(data).digest()[:4]


def _build_header(original: bytes, key: bytes) -> bytes:
    return _HEADER.pack(
        MAGIC,
        VERSION,
        0x00,  # flags
        len(key),
        len(original),
        _checksum(original),
    )


def parse_header(raw: bytes) -> Header:
    if len(raw) < HEADER_SIZE:
        raise ValueError("File too small to contain a valid ZPX header")
    magic, ver, flags, key_len, orig_size, cksum = _HEADER.unpack_from(raw)
    if magic != MAGIC:
        raise ValueError(f"Invalid magic bytes: {magic!r}")
    return Header(
        version=ver,
        flags=flags,
        key_length=key_len,
        original_size=orig_size,
        checksum=cksum,
    )


# ── 公开 API ──────────────────────────────────────────────────────


def pack(data: bytes, key: bytes) -> bytes:
    """压缩并加密数据，返回打包后的字节流（含文件头）。

    流水线：数据 → RLE 压缩 → XOR 加密 → 拼接头部。
    """
    compressed = rle.compress(data)
    encrypted = crypto.encrypt(compressed, key)
    header = _build_header(data, key)
    return header + encrypted


def unpack(blob: bytes, key: bytes) -> bytes:
    """解密并解压 ZPX 字节流，还原为原始数据。

    异常
    ------
    ValueError
        文件头损坏或校验和不匹配时抛出。
    """
    hdr = parse_header(blob)
    payload = blob[HEADER_SIZE:]
    decrypted = crypto.decrypt(payload, key)
    decompressed = rle.decompress(decrypted)

    # 完整性校验
    if len(decompressed) != hdr.original_size:
        raise ValueError(
            f"Size mismatch: expected {hdr.original_size}, got {len(decompressed)}. "
            "Wrong key or corrupted file."
        )
    if _checksum(decompressed) != hdr.checksum:
        raise ValueError(
            "Checksum mismatch — wrong key or corrupted file."
        )
    return decompressed


def pack_file(src: str | Path, dst: str | Path, key: bytes) -> Path:
    """读取 src 文件，打包后写入 dst。返回 dst 的 Path 对象。"""
    src_path = Path(src)
    dst_path = Path(dst)
    data = src_path.read_bytes()
    dst_path.write_bytes(pack(data, key))
    return dst_path


def unpack_file(src: str | Path, dst: str | Path, key: bytes) -> Path:
    """读取 src 中的 .zpx 文件，解包后写入 dst。"""
    src_path = Path(src)
    dst_path = Path(dst)
    blob = src_path.read_bytes()
    dst_path.write_bytes(unpack(blob, key))
    return dst_path
