from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import IO, Any, Callable

from .errors import ArtifactFormatError


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ArtifactFormatError(f"non-finite number at {path}: {value!r}")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_non_finite(child, f"{path}[{index}]")


def canonical_json_bytes(value: Any) -> bytes:
    """Return a deterministic strict-JSON representation.

    This is intentionally smaller than RFC 8785: it sorts object keys, removes
    insignificant whitespace, emits UTF-8, and rejects NaN/Infinity. It does not
    claim ECMAScript-compatible number canonicalization.
    """

    _reject_non_finite(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ArtifactFormatError(f"value is not strict-JSON serializable: {exc}") from exc
    return text.encode("utf-8")


def digest_object(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def normalized_text_digest(raw: bytes) -> str:
    """Digest text after removing a UTF-8 BOM and normalizing physical line endings."""

    normalized = raw.removeprefix(b"\xef\xbb\xbf")
    normalized = normalized.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    normalized = normalized.removesuffix(b"\n")
    return hashlib.sha256(normalized).hexdigest()


def sha256_file(path: str | os.PathLike[str], chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(
    destination: str | os.PathLike[str],
    writer: Callable[[IO[Any]], None],
    *,
    mode: str = "w",
    encoding: str | None = "utf-8",
    permissions: int | None = None,
) -> None:
    """Write in the destination directory and atomically replace on success."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".partial_", suffix=".tmp")
    try:
        kwargs = {} if "b" in mode else {"encoding": encoding}
        with os.fdopen(fd, mode, **kwargs) as handle:
            writer(handle)
            handle.flush()
            os.fsync(handle.fileno())
        if permissions is not None:
            os.chmod(temporary, permissions)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
