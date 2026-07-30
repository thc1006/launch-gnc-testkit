from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..canonical import sha256_file
from ..errors import ArtifactFormatError
from ..manifest import SCHEMA_VERSION, manifest_run_id, write_manifest
from ..trace import write_trace

SOURCE_REPOSITORY = "ARRC-Rocket/BalloonPoppingChallenge"
DEFAULT_SOURCE_COMMIT = "aa5ee7dcf1e715b9aeb7e90ca807a01b6c97062f"


def _finite_vector(values: Any, size: int) -> list[float] | None:
    if not isinstance(values, list) or len(values) != size:
        return None
    try:
        converted = [float(item) for item in values]
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(item) for item in converted):
        return None
    return converted


def _finite_time(value: Any, index: int) -> float:
    if isinstance(value, bool):
        raise ArtifactFormatError(f"BPC record {index} has a boolean time")
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ArtifactFormatError(f"BPC record {index} has an invalid time: {value!r}") from exc
    if not math.isfinite(converted):
        raise ArtifactFormatError(f"BPC record {index} has a non-finite time")
    return converted


def convert_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for index, source in enumerate(records):
        if not isinstance(source, dict):
            raise ArtifactFormatError(f"BPC trajectory record {index} is not an object")
        state = source.get("rocket_states")
        truth = None
        if isinstance(state, list) and len(state) == 13:
            position = _finite_vector(state[0:3], 3)
            velocity = _finite_vector(state[3:6], 3)
            quaternion = _finite_vector(state[6:10], 4)
            angular_rate = _finite_vector(state[10:13], 3)
            if all(item is not None for item in (position, velocity, quaternion, angular_rate)):
                truth = {
                    "position_m": position,
                    "velocity_mps": velocity,
                    "attitude_quaternion": quaternion,
                    "angular_rate_rps": angular_rate,
                }
        converted.append(
            {
                "step_index": index,
                "time_s": _finite_time(source.get("time"), index),
                "truth": truth,
                "extensions": {
                    "org.arrc.balloon_popping": {
                        "balloon_states": source.get("balloon_states"),
                        "balloon_status": source.get("balloon_status"),
                    }
                },
            }
        )
    return converted


def default_manifest(
    trace_path: str,
    *,
    trace_digest: str | None = None,
    source_commit: str = DEFAULT_SOURCE_COMMIT,
    root_seed: int | str = "unknown",
    time_step_s: float | None = None,
) -> dict[str, Any]:
    trace = {"format": Path(trace_path).suffix.lstrip("."), "path": trace_path}
    if trace_digest:
        trace["digest"] = trace_digest
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run": {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "scenario": {
            "id": "arrc-balloon-popping-import",
            "version": "unknown",
            "time_step_s": time_step_s or 0.01,
        },
        "coordinates": {
            "world_frame": "ENU",
            "body_frame": "ARRC_ROCKET_BODY",
            "vertical_reference": "MSL",
            "quaternion_order": "wxyz",
        },
        "units": {
            "time": "s",
            "length": "m",
            "angle": "rad",
            "angular_rate": "rad/s",
            "velocity": "m/s",
        },
        "random": {"root_seed": root_seed, "derivation": "source-defined"},
        "simulator": {
            "name": "BalloonPoppingChallenge/ActiveRocketPy",
            "version": "0.1.0",
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": source_commit,
        },
        "controller": {"name": "unknown"},
        "trace": trace,
        "extensions": {"org.arrc.balloon_popping": {}},
    }
    manifest["run"]["id"] = manifest_run_id(manifest)
    return manifest


def _infer_time_step(records: list[dict[str, Any]]) -> float:
    if len(records) < 2:
        return 0.01
    differences = [
        current["time_s"] - previous["time_s"]
        for previous, current in zip(records, records[1:])
    ]
    if any(not math.isfinite(step) or step <= 0 for step in differences):
        raise ArtifactFormatError("BPC trajectory timestamps must be strictly increasing")
    expected = differences[0]
    tolerance = max(1e-12, abs(expected) * 1e-9)
    if any(abs(step - expected) > tolerance for step in differences[1:]):
        raise ArtifactFormatError("BPC trajectory does not use a constant environment timestep")
    return expected


def convert_file(
    source_path: str | Path,
    trace_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
    source_commit: str = DEFAULT_SOURCE_COMMIT,
    root_seed: int | str = "unknown",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        raw = json.loads(Path(source_path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactFormatError(f"cannot load BPC trajectory {source_path}: {exc}") from exc
    if not isinstance(raw, list):
        raise ArtifactFormatError("BPC trajectory must be a JSON list")
    if manifest_path and Path(manifest_path).suffix.lower() not in (".json", ".yaml", ".yml"):
        raise ArtifactFormatError(
            f"manifest output must end in .json, .yaml, or .yml: {manifest_path}"
        )
    records = convert_records(raw)
    time_step = _infer_time_step(records)
    write_trace(records, trace_path)
    manifest = default_manifest(
        str(trace_path),
        trace_digest=sha256_file(trace_path),
        source_commit=source_commit,
        root_seed=root_seed,
        time_step_s=time_step,
    )
    if manifest_path:
        write_manifest(manifest, manifest_path)
    return records, manifest
