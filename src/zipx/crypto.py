"""XOR 加解密模块。

XOR 是对称的：encrypt(encrypt(data, key), key) == data。
密钥会循环重复以匹配数据长度。
"""

from __future__ import annotations


def xor_bytes(data: bytes, key: bytes) -> bytes:
    """对数据与循环密钥进行异或操作。

    参数
    ----------
    data:
        待转换的原始字节数据。
    key:
        密钥（至少 1 字节）。

    返回
    -------
    bytes
        转换后的字节数据（长度与输入相同）。

    异常
    ------
    ValueError
        当密钥为空时。
    """
    if not key:
        raise ValueError("Key must not be empty")
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def encrypt(data: bytes, key: bytes) -> bytes:
    """使用 XOR 算法加密数据。"""
    return xor_bytes(data, key)


def decrypt(data: bytes, key: bytes) -> bytes:
    """使用 XOR 算法解密数据（操作与加密相同）。"""
    return xor_bytes(data, key)
