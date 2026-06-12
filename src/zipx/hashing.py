"""哈希摘要工具（MD5、SHA-1、SHA-256）。"""

from __future__ import annotations

import hashlib
from typing import Literal

Algorithm = Literal["md5", "sha1", "sha256"]

ALGORITHMS: tuple[Algorithm, ...] = ("md5", "sha1", "sha256")


def digest(data: bytes, algorithm: Algorithm = "sha256") -> str:
    """使用指定算法计算数据的十六进制哈希摘要。

    参数
    ----------
    data:
        待计算的原始字节数据。
    algorithm:
        哈希算法，支持 "md5"、"sha1" 或 "sha256"。

    返回
    -------
    str
        十六进制编码的摘要字符串。

    异常
    ------
    ValueError
        当算法不支持时。
    """
    if algorithm not in ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm {algorithm!r}. "
            f"Choose from {ALGORITHMS}"
        )
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def digest_file(path: str, algorithm: Algorithm = "sha256") -> str:
    """计算指定路径文件的十六进制哈希摘要。"""
    with open(path, "rb") as f:
        data = f.read()
    return digest(data, algorithm)
