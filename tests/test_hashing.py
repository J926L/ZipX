"""zipx.hashing (哈希摘要工具) 的测试。"""

import hashlib
from pathlib import Path

import pytest

from zipx.hashing import ALGORITHMS, Algorithm, digest, digest_file


class TestDigest:
    def test_sha256_default(self) -> None:
        data = b"hello"
        expected = hashlib.sha256(data).hexdigest()
        assert digest(data) == expected

    @pytest.mark.parametrize("algo", ALGORITHMS)
    def test_all_algorithms(self, algo: Algorithm) -> None:
        data = b"test data"
        expected = hashlib.new(algo, data).hexdigest()
        assert digest(data, algo) == expected

    def test_empty_data(self) -> None:
        expected = hashlib.sha256(b"").hexdigest()
        assert digest(b"") == expected

    def test_unsupported_algorithm(self) -> None:
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            digest(b"x", "sha512")  # type: ignore[arg-type]


class TestDigestFile:
    def test_file_digest(self, tmp_path: Path) -> None:
        f = tmp_path / "sample.txt"
        content = b"file content for hashing"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert digest_file(str(f)) == expected

    def test_file_md5(self, tmp_path: Path) -> None:
        f = tmp_path / "sample.txt"
        content = b"md5 test"
        f.write_bytes(content)
        expected = hashlib.md5(content).hexdigest()
        assert digest_file(str(f), "md5") == expected
