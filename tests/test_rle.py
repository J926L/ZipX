"""zipx.rle (游程编码) 的测试。"""

import pytest

from zipx.rle import compress, decompress


class TestCompress:
    def test_empty(self) -> None:
        assert compress(b"") == b""

    def test_single_byte(self) -> None:
        result = compress(b"A")
        assert decompress(result) == b"A"

    def test_all_same(self) -> None:
        # 重复数据应能极大地被压缩（一万字节变为 3 字节）
        data = b"\x00" * 1000
        compressed = compress(data)
        assert len(compressed) == 3  # 2 字节计数 + 1 字节值
        assert decompress(compressed) == data

    def test_no_repeats(self) -> None:
        # 无重复的数据
        data = bytes(range(256))
        compressed = compress(data)
        # 256 个游程，每个长度为 1 → 256 * 3 = 768 字节
        assert len(compressed) == 768
        assert decompress(compressed) == data

    def test_mixed(self) -> None:
        # 混合数据压缩
        data = b"AAABBBCCDDDDDD"
        compressed = compress(data)
        assert decompress(compressed) == data


class TestDecompress:
    def test_empty(self) -> None:
        assert decompress(b"") == b""

    def test_corrupted_length(self) -> None:
        # 长度必须是 3 的倍数，否则抛出 ValueError
        with pytest.raises(ValueError, match="Corrupted RLE data"):
            decompress(b"\x01\x00")  # 只有 2 字节


class TestRoundTrip:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param(b"Hello, World!", id="ascii"),
            pytest.param(b"\x00" * 65535, id="65535_zeros"),
            pytest.param(b"\xFF\x00" * 500, id="alternating_ff_00"),
            pytest.param(bytes(range(256)) * 10, id="byte_range_x10"),
            pytest.param("包含中文的文本内容".encode("utf-8"), id="chinese_utf8"),
        ],
    )
    def test_round_trip(self, data: bytes) -> None:
        assert decompress(compress(data)) == data

    def test_large_run_splitting(self) -> None:
        """超过 65535 的游程必须拆分为多个记录。"""
        data = b"\xAB" * 70000
        compressed = compress(data)
        # 应生成 2 个游程：65535 + 4465
        assert len(compressed) == 6  # 2 * 3
        assert decompress(compressed) == data
