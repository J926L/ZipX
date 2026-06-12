"""ZipX 命令行界面。

命令
--------
* ``zipx pack <FILE> -k <KEY>``   — 压缩并加密
* ``zipx unpack <FILE> -k <KEY>`` — 解密并解压
* ``zipx hash <FILE>``            — 打印哈希摘要
* ``zipx info <FILE>``            — 显示 ZPX 头部信息
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import click

from zipx import __version__
from zipx.hashing import ALGORITHMS, Algorithm, digest
from zipx.pipeline import EXTENSION, HEADER_SIZE, Header, parse_header, pack, unpack


# ── 辅助函数 ─────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".text", ".rst"}


def _resolve_output(src: Path, output: str | None, ext: str) -> Path:
    """确定输出路径：显式指定路径优先于默认后缀替换。"""
    if output:
        return Path(output)
    return src.with_suffix(ext)


def _read_key(key: str) -> bytes:
    """将密钥字符串转换为字节流。"""
    return key.encode("utf-8")


# ── CLI 组 ───────────────────────────────────────────────────────


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version")
def cli() -> None:
    """ZipX - 轻量级文件加密与压缩工具。

    对 TXT / Markdown 文件组合使用 RLE 压缩与 XOR 加密。
    """


# ── pack ────────────────────────────────────────────────────────────


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("-k", "--key", required=True, help="加密密钥（字符串）。")
@click.option("-o", "--output", default=None, help="输出文件路径。")
@click.option("-f", "--force", is_flag=True, help="覆盖已存在的输出文件。")
def pack_cmd(file: str, key: str, output: str | None, force: bool) -> None:
    """压缩并加密 FILE => .zpx"""
    src = Path(file)

    # 验证文件后缀
    if src.suffix.lower() not in SUPPORTED_EXTENSIONS:
        click.echo(
            f"[!] Unsupported extension {src.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            err=True,
        )
        sys.exit(1)

    dst = _resolve_output(src, output, EXTENSION)
    if dst.exists() and not force:
        click.echo(f"[-] Output file {dst} already exists. Use -f to overwrite.", err=True)
        sys.exit(1)

    data = src.read_bytes()
    result = pack(data, _read_key(key))
    dst.write_bytes(result)

    ratio = len(result) / len(data) * 100 if data else 0
    click.echo(f"[+] Packed {src.name} => {dst.name}")
    click.echo(f"   Original : {len(data):>10,} bytes")
    click.echo(f"   Packed   : {len(result):>10,} bytes  ({ratio:.1f}%)")


# ── unpack ──────────────────────────────────────────────────────────


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("-k", "--key", required=True, help="解密密钥（字符串）。")
@click.option("-o", "--output", default=None, help="输出文件路径。")
@click.option("-f", "--force", is_flag=True, help="覆盖已存在的输出文件。")
def unpack_cmd(file: str, key: str, output: str | None, force: bool) -> None:
    """解密并解压 .zpx 文件还原为原始文件。"""
    src = Path(file)

    if src.suffix.lower() != EXTENSION:
        click.echo(f"[!] Expected a {EXTENSION} file, got {src.suffix!r}", err=True)
        sys.exit(1)

    # 默认：去除 .zpx，恢复为 .txt
    dst = _resolve_output(src, output, ".txt")
    if dst.exists() and not force:
        click.echo(f"[-] Output file {dst} already exists. Use -f to overwrite.", err=True)
        sys.exit(1)

    blob = src.read_bytes()
    try:
        original = unpack(blob, _read_key(key))
    except ValueError as exc:
        click.echo(f"[-] Unpack failed: {exc}", err=True)
        sys.exit(1)

    dst.write_bytes(original)
    click.echo(f"[+] Unpacked {src.name} => {dst.name}")
    click.echo(f"   Restored : {len(original):>10,} bytes")


# ── hash ────────────────────────────────────────────────────────────


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-a",
    "--algorithm",
    type=click.Choice(list(ALGORITHMS)),
    default="sha256",
    show_default=True,
    help="哈希算法。",
)
def hash_cmd(file: str, algorithm: str) -> None:
    """打印文件的哈希摘要。"""
    algo = cast(Algorithm, algorithm)  # click.Choice 已做验证
    data = Path(file).read_bytes()
    hex_digest = digest(data, algo)
    click.echo(f"{algo.upper()}  {hex_digest}  {file}")


# ── info ────────────────────────────────────────────────────────────


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
def info(file: str) -> None:
    """显示 .zpx 文件的头部信息。"""
    src = Path(file)
    blob = src.read_bytes()
    try:
        hdr: Header = parse_header(blob)
    except ValueError as exc:
        click.echo(f"[-] {exc}", err=True)
        sys.exit(1)

    payload_size = len(blob) - HEADER_SIZE
    click.echo(f"File        : {src.name}")
    click.echo(f"Version     : {hdr.version}")
    click.echo(f"Flags       : 0x{hdr.flags:02X}")
    click.echo(f"Key length  : {hdr.key_length} bytes")
    click.echo(f"Orig. size  : {hdr.original_size:,} bytes")
    click.echo(f"Checksum    : {hdr.checksum.hex()}")
    click.echo(f"Payload     : {payload_size:,} bytes")


# ── 程序入口 ─────────────────────────────────────────────────────

# 注册子命令短名称
cli.add_command(pack_cmd, "pack")
cli.add_command(unpack_cmd, "unpack")
cli.add_command(hash_cmd, "hash")
cli.add_command(info, "info")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
