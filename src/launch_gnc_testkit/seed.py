from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable


def _typed_value(value: int | str | bytes) -> dict[str, str]:
    if isinstance(value, bytes):
        return {"type": "bytes", "value": value.hex()}
    if isinstance(value, int):
        if value < 0:
            raise ValueError("seed integers must be non-negative")
        return {"type": "int", "value": str(value)}
    return {"type": "str", "value": value}


def _seed_material(
    namespace: str,
    root_seed: int | str | bytes,
    path: tuple[str | int, ...],
) -> bytes:
    descriptor = {
        "namespace": namespace,
        "root": _typed_value(root_seed),
        "path": [_typed_value(item) for item in path],
    }
    return json.dumps(
        descriptor,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class SeedTree:
    """Order-independent, type-safe named seed derivation.

    Every component receives a seed derived from the root and its semantic path.
    Adding an unrelated component does not shift any existing stream. Integer,
    string, and byte roots are deliberately domain-separated.
    """

    root_seed: int | str | bytes
    namespace: str = "launch-gnc-testkit/v1"

    def derive(self, *path: str | int, bits: int = 128) -> int:
        if bits <= 0 or bits % 8:
            raise ValueError("bits must be a positive multiple of 8")
        material = _seed_material(self.namespace, self.root_seed, path)
        output = bytearray()
        counter = 0
        while len(output) < bits // 8:
            output.extend(hashlib.sha256(material + counter.to_bytes(4, "big")).digest())
            counter += 1
        return int.from_bytes(output[: bits // 8], "big")

    def derive_many(self, paths: Iterable[tuple[str | int, ...]], bits: int = 128) -> dict:
        return {tuple(path): self.derive(*path, bits=bits) for path in paths}

    def numpy_seed_sequence(self, *path: str | int):
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("NumPy is required for SeedSequence integration") from exc
        value = self.derive(*path, bits=128)
        words = [(value >> shift) & 0xFFFFFFFF for shift in range(0, 128, 32)]
        return np.random.SeedSequence(words)
