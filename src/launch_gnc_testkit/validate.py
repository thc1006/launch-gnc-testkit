from __future__ import annotations

import math
from numbers import Real
from typing import Any

import numpy as np

from .report import Report, Severity

_VECTOR_FIELDS = {
    "truth.position_m": 3,
    "truth.velocity_mps": 3,
    "truth.angular_rate_rps": 3,
    "truth.attitude_quaternion": 4,
}


def _walk_non_finite(value: Any, path: str = "$"):
    if isinstance(value, Real) and not isinstance(value, bool):
        try:
            if not math.isfinite(float(value)):
                yield path, value
        except (TypeError, ValueError, OverflowError):
            return
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_non_finite(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk_non_finite(child, f"{path}[{index}]")


def _get(record: dict[str, Any], path: str):
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _finite_number(value: Any) -> bool:
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def validate_trace(
    records: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
    *,
    quaternion_norm_tolerance: float = 1e-6,
) -> Report:
    report = Report("Trace validation")
    report.summary["record_count"] = len(records)
    if not math.isfinite(quaternion_norm_tolerance) or quaternion_norm_tolerance < 0:
        report.add(
            "invalid-quaternion-tolerance",
            "quaternion_norm_tolerance must be finite and non-negative",
        )
        return report
    if not records:
        report.add("empty-trace", "trace contains no records")
        return report

    times: list[float] = []
    all_times_valid = True
    for index, record in enumerate(records):
        location = f"$[{index}]"
        if not isinstance(record, dict):
            report.add("record-type", "trace record is not an object", location=location)
            all_times_valid = False
            continue

        for path, value in _walk_non_finite(record, location):
            report.add("non-finite", f"non-finite value {value!r}", location=path)

        time_value = record.get("time_s")
        if not _finite_number(time_value):
            report.add("time", "time_s must be a finite number", location=f"{location}.time_s")
            all_times_valid = False
        else:
            times.append(float(time_value))

        if "step_index" in record:
            step_index = record["step_index"]
            if not isinstance(step_index, int) or isinstance(step_index, bool):
                report.add(
                    "step-index-type",
                    "step_index must be an integer",
                    location=f"{location}.step_index",
                )
            elif step_index != index:
                report.add(
                    "step-index",
                    f"step_index is {step_index!r}, expected {index}",
                    location=f"{location}.step_index",
                )

        for path, expected_size in _VECTOR_FIELDS.items():
            value = _get(record, path)
            if value is None:
                continue
            try:
                array = np.asarray(value, dtype=float)
            except (TypeError, ValueError, OverflowError) as exc:
                report.add(
                    "vector-type",
                    f"{path} cannot be converted to numbers: {exc}",
                    location=f"{location}.{path}",
                )
                continue
            if array.shape != (expected_size,):
                report.add(
                    "vector-shape",
                    f"{path} must have shape ({expected_size},), got {array.shape}",
                    location=f"{location}.{path}",
                )

        quaternion = _get(record, "truth.attitude_quaternion")
        if quaternion is not None:
            try:
                array = np.asarray(quaternion, dtype=float)
            except (TypeError, ValueError, OverflowError):
                array = np.array([])
            if array.shape == (4,) and np.all(np.isfinite(array)):
                norm = float(np.linalg.norm(array))
                if abs(norm - 1.0) > quaternion_norm_tolerance:
                    report.add(
                        "quaternion-norm",
                        f"quaternion norm {norm:.9g} is outside tolerance",
                        location=f"{location}.truth.attitude_quaternion",
                        norm=norm,
                        tolerance=quaternion_norm_tolerance,
                    )

    if all_times_valid and len(times) == len(records):
        differences = np.diff(times)
        bad = np.flatnonzero(differences <= 0)
        for index in bad[:10]:
            report.add(
                "time-order",
                "time_s must be strictly increasing",
                location=f"$[{index + 1}].time_s",
                previous=times[index],
                current=times[index + 1],
            )
        if bad.size > 10:
            report.add(
                "time-order-more",
                f"{bad.size - 10} additional non-increasing timestamps omitted",
                Severity.WARNING,
            )

    if manifest:
        scenario = manifest.get("scenario")
        scenario = scenario if isinstance(scenario, dict) else {}
        expected_step = scenario.get("time_step_s")
        if _finite_number(expected_step) and float(expected_step) > 0 and len(times) >= 2:
            drift = np.max(np.abs(np.diff(times) - float(expected_step)))
            report.summary["max_time_step_drift_s"] = float(drift)
            tolerance = max(1e-12, abs(float(expected_step)) * 1e-9)
            if drift > tolerance:
                report.add(
                    "time-step-drift",
                    f"maximum timestep drift {drift:.6g} s exceeds {tolerance:.6g} s",
                    location="$.time_s",
                )

        coordinates = manifest.get("coordinates")
        coordinates = coordinates if isinstance(coordinates, dict) else {}
        required = ["world_frame", "body_frame", "quaternion_order", "vertical_reference"]
        missing = [
            key
            for key in required
            if not isinstance(coordinates, dict) or not coordinates.get(key)
        ]
        if missing:
            report.add(
                "coordinate-contract",
                f"manifest is missing coordinate declarations: {', '.join(missing)}",
                location="manifest.coordinates",
            )
    return report
