"""zipx.cli (命令行界面) 的测试。"""

from pathlib import Path

from click.testing import CliRunner

from zipx.cli import cli


class TestPackUnpackCLI:
    def test_pack_and_unpack(self, tmp_path: Path) -> None:
        # 测试命令行打包与解包的基本流程
        runner = CliRunner()

        # 创建样本文件
        src = tmp_path / "sample.txt"
        src.write_text("Hello, ZipX CLI test!\n", encoding="utf-8")

        zpx = tmp_path / "sample.zpx"

        # 打包
        result = runner.invoke(cli, ["pack", str(src), "-k", "testkey", "-o", str(zpx)])
        assert result.exit_code == 0, result.output
        assert "Packed" in result.output
        assert zpx.exists()

        # 解包
        dst = tmp_path / "restored.txt"
        result = runner.invoke(cli, ["unpack", str(zpx), "-k", "testkey", "-o", str(dst)])
        assert result.exit_code == 0, result.output
        assert "Unpacked" in result.output
        assert dst.read_text(encoding="utf-8") == "Hello, ZipX CLI test!\n"

    def test_pack_unsupported_extension(self, tmp_path: Path) -> None:
        # 打包不支持的后缀时应报错
        runner = CliRunner()
        src = tmp_path / "image.png"
        src.write_bytes(b"\x89PNG")

        result = runner.invoke(cli, ["pack", str(src), "-k", "key"])
        assert result.exit_code != 0
        assert "Unsupported extension" in result.output

    def test_pack_no_overwrite_by_default(self, tmp_path: Path) -> None:
        # 默认不覆盖已存在的输出文件
        runner = CliRunner()
        src = tmp_path / "sample.txt"
        src.write_text("data", encoding="utf-8")
        zpx = tmp_path / "sample.zpx"
        zpx.write_bytes(b"existing")

        result = runner.invoke(cli, ["pack", str(src), "-k", "key", "-o", str(zpx)])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_pack_force_overwrite(self, tmp_path: Path) -> None:
        # 使用 -f 可以强制覆盖已存在文件
        runner = CliRunner()
        src = tmp_path / "sample.txt"
        src.write_text("data", encoding="utf-8")
        zpx = tmp_path / "sample.zpx"
        zpx.write_bytes(b"existing")

        result = runner.invoke(cli, ["pack", str(src), "-k", "key", "-o", str(zpx), "-f"])
        assert result.exit_code == 0

    def test_unpack_wrong_key(self, tmp_path: Path) -> None:
        # 使用错误密钥解包应当失败
        runner = CliRunner()
        src = tmp_path / "sample.txt"
        src.write_text("secret content\n", encoding="utf-8")
        zpx = tmp_path / "sample.zpx"

        runner.invoke(cli, ["pack", str(src), "-k", "correct", "-o", str(zpx)])

        dst = tmp_path / "bad.txt"
        result = runner.invoke(cli, ["unpack", str(zpx), "-k", "wrong", "-o", str(dst)])
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "mismatch" in result.output.lower()

    def test_pack_markdown(self, tmp_path: Path) -> None:
        # 验证 Markdown 文件的打包
        runner = CliRunner()
        src = tmp_path / "notes.md"
        src.write_text("# Notes\n\n- item\n", encoding="utf-8")
        zpx = tmp_path / "notes.zpx"

        result = runner.invoke(cli, ["pack", str(src), "-k", "mdkey", "-o", str(zpx)])
        assert result.exit_code == 0


class TestHashCLI:
    def test_sha256(self, tmp_path: Path) -> None:
        # 测试 hash 命令默认的 sha256 算法
        runner = CliRunner()
        f = tmp_path / "data.txt"
        f.write_text("hash me", encoding="utf-8")

        result = runner.invoke(cli, ["hash", str(f)])
        assert result.exit_code == 0
        assert "SHA256" in result.output

    def test_md5(self, tmp_path: Path) -> None:
        # 测试 hash 命令指定 md5 算法
        runner = CliRunner()
        f = tmp_path / "data.txt"
        f.write_text("hash me", encoding="utf-8")

        result = runner.invoke(cli, ["hash", str(f), "-a", "md5"])
        assert result.exit_code == 0
        assert "MD5" in result.output


class TestInfoCLI:
    def test_info(self, tmp_path: Path) -> None:
        # 测试 info 命令输出头部信息
        runner = CliRunner()
        src = tmp_path / "sample.txt"
        src.write_text("info test\n", encoding="utf-8")
        zpx = tmp_path / "sample.zpx"

        runner.invoke(cli, ["pack", str(src), "-k", "key", "-o", str(zpx)])

        result = runner.invoke(cli, ["info", str(zpx)])
        assert result.exit_code == 0
        assert "Version" in result.output
        assert "Orig. size" in result.output

    def test_info_invalid_file(self, tmp_path: Path) -> None:
        # 测试 info 命令在文件损坏或无效时的报错
        runner = CliRunner()
        f = tmp_path / "bad.zpx"
        f.write_bytes(b"not a zpx file")

        result = runner.invoke(cli, ["info", str(f)])
        assert result.exit_code != 0


class TestVersionHelp:
    def test_version(self) -> None:
        # 测试 --version 参数
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self) -> None:
        # 测试 --help 参数
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ZipX" in result.output
