# ZipX

轻量级 CLI 文件加密与压缩工具，结合 **RLE 压缩** 与 **XOR 加密**。

## 功能

| 功能           | 说明                                                |
| -------------- | --------------------------------------------------- |
| **RLE 压缩**   | 游程编码，对重复字节序列高效压缩                    |
| **XOR 加密**   | 对称加密，使用循环密钥异或                          |
| **哈希摘要**   | 支持 MD5 / SHA-1 / SHA-256                          |
| **完整性校验** | 打包文件包含 magic bytes + checksum，解包时自动验证 |

## 安装

```powershell
# 安装依赖并生成虚拟环境
uv sync
```

## 使用

### 压缩加密（pack）

```powershell
# 将 TXT/Markdown 文件压缩加密为 .zpx
uv run zipx pack README.md -k "my-secret-key"
# 输出: README.zpx

# 指定输出路径
uv run zipx pack notes.txt -k "key123" -o encrypted.zpx
```

### 解密还原（unpack）

```powershell
# 解密还原 .zpx 文件
uv run zipx unpack README.zpx -k "my-secret-key"
# 输出: README.txt

# 指定输出路径
uv run zipx unpack encrypted.zpx -k "key123" -o notes_restored.txt
```

### 哈希摘要（hash）

```powershell
# 默认 SHA-256
uv run zipx hash README.md

# 指定算法
uv run zipx hash README.md -a md5
uv run zipx hash README.md -a sha1
```

### 查看文件信息（info）

```powershell
uv run zipx info README.zpx
```

输出示例：

```
File        : README.zpx
Version     : 1
Original Size: 2,359 bytes
Checksum    : a1b2c3d4
Payload Size: 1,890 bytes
```

## 支持的文件格式

`.txt` · `.md` · `.markdown` · `.text` · `.rst`

## .zpx 文件格式

```
Offset  Size  Field
------  ----  -----
0       4     Magic "ZPX\0"
4       1     Version (0x01)
5       1     Flags (reserved)
6       2     Key length (LE uint16)
8       4     Original size (LE uint32)
12      4     SHA-256 checksum (first 4 bytes)
16      …     Payload (RLE compressed + XOR encrypted)
```

## 开发

```powershell
# 运行测试
uv run pytest -v
```

## 项目结构

```
src/zipx/
├── __init__.py   # 包入口
├── cli.py        # Click CLI 入口
├── crypto.py     # XOR 加密/解密
├── hashing.py    # MD5/SHA 哈希
├── pipeline.py   # 打包/解包流水线
└── rle.py        # RLE 压缩/解压
```
