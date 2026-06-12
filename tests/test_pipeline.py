"""zipx.pipeline (打包/解包流水线) 的测试。"""

from pathlib import Path

import pytest

from zipx.pipeline import (
    HEADER_SIZE,
    parse_header,
    pack,
    pack_file,
    unpack,
    unpack_file,
)


class TestPackUnpack:
    @pytest.mark.parametrize(
        "data,key",
        [
            (b"Simple text file content.\n", b"secret"),
            (b"# Markdown\n\nHello **world**.\n", b"key123"),
            (b"\x00" * 100, b"k"),
            (b"a", b"x"),
            ("日本語测试\n多行\n内容".encode("utf-8"), b"pwd"),
        ],
    )
    def test_round_trip(self, data: bytes, key: bytes) -> None:
        # 测试完整打包解包流程
        packed = pack(data, key)
        # 头部长度应符合预期
        assert len(packed) >= HEADER_SIZE
        # 校验魔数
        assert packed[:4] == b"ZPX\x00"
        # 解包还原
        restored = unpack(packed, key)
        assert restored == data

    def test_wrong_key_fails(self) -> None:
        # 错误的密钥解包时应当失败
        data = b"secret data"
        packed = pack(data, b"correct")
        with pytest.raises(ValueError):
            unpack(packed, b"wrong")

    def test_corrupted_magic(self) -> None:
        # 损坏的魔数解包时应当失败
        packed = pack(b"data", b"key")
        corrupted = b"XXXX" + packed[4:]
        with pytest.raises(ValueError, match="Invalid magic"):
            unpack(corrupted, b"key")

    def test_empty_data(self) -> None:
        # 空数据打包解包
        packed = pack(b"", b"key")
        assert unpack(packed, b"key") == b""


class TestFileIO:
    def test_pack_unpack_file(self, tmp_path: Path) -> None:
        # 测试文本文件的打包和解包
        src = tmp_path / "hello.txt"
        src.write_text("Hello, ZipX!\n", encoding="utf-8")

        zpx = tmp_path / "hello.zpx"
        pack_file(src, zpx, b"mykey")
        assert zpx.exists()

        dst = tmp_path / "restored.txt"
        unpack_file(zpx, dst, b"mykey")
        assert dst.read_text(encoding="utf-8") == "Hello, ZipX!\n"

    def test_pack_unpack_markdown(self, tmp_path: Path) -> None:
        # 测试 Markdown 文件的打包和解包
        src = tmp_path / "readme.md"
        content = "# Title\n\nParagraph with **bold**.\n\n- item 1\n- item 2\n"
        src.write_text(content, encoding="utf-8")

        zpx = tmp_path / "readme.zpx"
        pack_file(src, zpx, b"pass")

        dst = tmp_path / "readme_restored.md"
        unpack_file(zpx, dst, b"pass")
        assert dst.read_text(encoding="utf-8") == content


class TestHeader:
    def test_parse_valid(self) -> None:
        # 解析有效的文件头部信息
        packed = pack(b"data", b"key")
        hdr = parse_header(packed)
        assert hdr.version == 1
        assert hdr.original_size == 4
        assert hdr.key_length == 3

    def test_too_small(self) -> None:
        # 长度不足的头部应当解析失败
        with pytest.raises(ValueError, match="too small"):
            parse_header(b"short")
