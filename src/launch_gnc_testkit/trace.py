from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from .canonical import atomic_write
from .errors import ArtifactFormatError


def _strict_dump(value: Any, handle, *, indent: int | None = None) -> None:
    json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=indent)


def load_trace(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    suffix = source.suffix.lower()
    try:
        if suffix in {".ndjson", ".jsonl"}:
            records = []
            with source.open("r", encoding="utf-8-sig") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ArtifactFormatError(
                            f"record {line_number} in {source} is not an object"
                        )
                    records.append(value)
            return records
        if suffix == ".json":
            value = json.loads(source.read_text(encoding="utf-8-sig"))
            if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                raise ArtifactFormatError("JSON trace must be a list of objects")
            return value
        if suffix == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError as exc:
                raise ArtifactFormatError(
                    "Parquet support requires launch-gnc-testkit[parquet]"
                ) from exc
            return pq.read_table(source).to_pylist()
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactFormatError(f"cannot read trace {source}: {exc}") from exc
    raise ArtifactFormatError(f"unsupported trace format: {source.suffix}")


def iter_trace(path: str | Path) -> Iterator[dict[str, Any]]:
    yield from load_trace(path)


def write_trace(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    destination = Path(path)
    materialized = list(records)
    suffix = destination.suffix.lower()
    if suffix in {".ndjson", ".jsonl"}:
        def writer(handle) -> None:
            for record in materialized:
                _strict_dump(record, handle)
                handle.write("\n")
        atomic_write(destination, writer)
        return
    if suffix == ".json":
        atomic_write(destination, lambda handle: _strict_dump(materialized, handle, indent=2))
        return
    if suffix == ".parquet":
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise ArtifactFormatError(
                "Parquet support requires launch-gnc-testkit[parquet]"
            ) from exc

        def writer(handle) -> None:
            table = pa.Table.from_pylist(materialized)
            pq.write_table(table, handle)

        atomic_write(destination, writer, mode="wb", encoding=None)
        return
    raise ArtifactFormatError(f"unsupported trace format: {destination.suffix}")


def get_path(record: dict[str, Any], dotted_path: str) -> Any:
    value: Any = record
    for part in dotted_path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise KeyError(dotted_path)
    return value
