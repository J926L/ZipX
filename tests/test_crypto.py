"""zipx.crypto (XOR 加密) 的测试。"""

import pytest

from zipx.crypto import decrypt, encrypt, xor_bytes


class TestXorBytes:
    def test_empty_data(self) -> None:
        assert xor_bytes(b"", b"key") == b""

    def test_single_byte_key(self) -> None:
        data = b"\x00\x01\x02\x03"
        key = b"\xFF"
        result = xor_bytes(data, key)
        assert result == bytes(b ^ 0xFF for b in data)

    def test_cycling_key(self) -> None:
        data = b"ABCDEF"
        key = b"XY"
        result = xor_bytes(data, key)
        expected = bytes(d ^ key[i % 2] for i, d in enumerate(data))
        assert result == expected

    def test_empty_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Key must not be empty"):
            xor_bytes(b"data", b"")


class TestEncryptDecrypt:
    @pytest.mark.parametrize(
        "data,key",
        [
            (b"Hello, World!", b"secret"),
            (b"\x00" * 100, b"\xAB\xCD"),
            (b"a", b"k"),
            (b"\xff" * 50, b"\x01\x02\x03\x04"),
            ("日本語テスト".encode("utf-8"), b"key123"),
        ],
    )
    def test_round_trip(self, data: bytes, key: bytes) -> None:
        encrypted = encrypt(data, key)
        assert encrypted != data or all(b == 0 for b in data)  # 应不同（除非 XOR 后恰好相同）
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_different_keys_different_output(self) -> None:
        data = b"plaintext"
        assert encrypt(data, b"key1") != encrypt(data, b"key2")
