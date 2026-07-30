from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from .report import Report, Severity
from .trace import get_path

ComparisonKind = Literal["scalar", "vector", "quaternion", "exact"]


@dataclass(frozen=True)
class ComparisonRule:
    path: str
    kind: ComparisonKind
    abs_tol: float = 0.0
    rel_tol: float = 0.0
    allow_missing: bool = False


def _quaternion_angle(actual: np.ndarray, expected: np.ndarray) -> np.ndarray:
    actual_norm = np.linalg.norm(actual, axis=-1, keepdims=True)
    expected_norm = np.linalg.norm(expected, axis=-1, keepdims=True)
    actual = actual / actual_norm
    expected = expected / expected_norm
    dot = np.abs(np.sum(actual * expected, axis=-1))
    return 2.0 * np.arccos(np.clip(dot, -1.0, 1.0))


def _collect(records: list[dict[str, Any]], path: str):
    values = []
    missing = []
    for index, record in enumerate(records):
        try:
            values.append(get_path(record, path))
        except KeyError:
            missing.append(index)
            values.append(None)
    return values, missing


def _validate_rule(rule: ComparisonRule, report: Report) -> tuple[float, float] | None:
    valid = True
    if not isinstance(rule.path, str) or not rule.path:
        report.add("invalid-rule", "comparison path must be a non-empty string")
        valid = False
    if rule.kind not in ("scalar", "vector", "quaternion", "exact"):
        report.add(
            "invalid-rule",
            f"unsupported comparison kind {rule.kind!r}",
            location=rule.path if isinstance(rule.path, str) else None,
        )
        valid = False
    try:
        abs_tol = float(rule.abs_tol)
        rel_tol = float(rule.rel_tol)
    except (TypeError, ValueError, OverflowError):
        report.add(
            "invalid-rule",
            "comparison tolerances must be finite numbers",
            location=rule.path if isinstance(rule.path, str) else None,
        )
        return None
    if not math.isfinite(abs_tol) or not math.isfinite(rel_tol):
        report.add(
            "invalid-rule",
            "comparison tolerances must be finite numbers",
            location=rule.path,
        )
        valid = False
    elif abs_tol < 0 or rel_tol < 0:
        report.add(
            "invalid-rule",
            "comparison tolerances must be non-negative",
            location=rule.path,
        )
        valid = False
    return (abs_tol, rel_tol) if valid else None


def compare_traces(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    rules: list[ComparisonRule],
    *,
    row_count_abs_tol: int = 0,
    continuity_factor: float = 3.0,
) -> Report:
    report = Report("Trace comparison")
    report.summary.update(actual_rows=len(actual), expected_rows=len(expected))
    if (
        not isinstance(row_count_abs_tol, int)
        or isinstance(row_count_abs_tol, bool)
        or row_count_abs_tol < 0
    ):
        report.add(
            "invalid-row-tolerance",
            "row_count_abs_tol must be a non-negative integer",
        )
        return report
    if not isinstance(continuity_factor, (int, float)) or isinstance(
        continuity_factor, bool
    ):
        report.add("invalid-continuity-factor", "continuity_factor must be finite and positive")
        return report
    continuity_factor = float(continuity_factor)
    if not math.isfinite(continuity_factor) or continuity_factor <= 0:
        report.add("invalid-continuity-factor", "continuity_factor must be finite and positive")
        return report
    if not rules:
        report.add(
            "no-rules",
            "no comparison rules were supplied; only row counts can be checked",
            Severity.WARNING,
        )

    row_delta = len(actual) - len(expected)
    if abs(row_delta) > row_count_abs_tol:
        report.add(
            "row-count",
            f"row count differs by {row_delta}, tolerance is {row_count_abs_tol}",
        )
    overlap = min(len(actual), len(expected))
    if overlap == 0:
        report.add("no-overlap", "traces have no overlapping records")
        return report

    for rule in rules:
        tolerances = _validate_rule(rule, report)
        if tolerances is None:
            continue
        abs_tol, rel_tol = tolerances
        actual_values, actual_missing = _collect(actual[:overlap], rule.path)
        expected_values, expected_missing = _collect(expected[:overlap], rule.path)
        missing = sorted(set(actual_missing + expected_missing))
        row_indices = list(range(overlap))
        if missing:
            severity = Severity.WARNING if rule.allow_missing else Severity.ERROR
            report.add(
                "missing-field",
                f"{rule.path} is missing in {len(missing)} overlapping records",
                severity,
                rule.path,
                first_rows=missing[:5],
            )
            if not rule.allow_missing:
                continue
            keep = [index for index in range(overlap) if index not in missing]
            actual_values = [actual_values[index] for index in keep]
            expected_values = [expected_values[index] for index in keep]
            row_indices = keep
            if not keep:
                continue

        if rule.kind == "exact":
            mismatches = [
                row_indices[index]
                for index, (left, right) in enumerate(zip(actual_values, expected_values))
                if left != right
            ]
            if mismatches:
                report.add(
                    "exact-mismatch",
                    f"{rule.path} differs in {len(mismatches)} rows",
                    location=rule.path,
                    first_rows=mismatches[:5],
                )
            continue

        try:
            left = np.asarray(actual_values, dtype=float)
            right = np.asarray(expected_values, dtype=float)
        except (TypeError, ValueError, OverflowError) as exc:
            report.add("numeric-conversion", str(exc), location=rule.path)
            continue
        if left.shape != right.shape:
            report.add(
                "shape",
                f"shape {left.shape} does not match {right.shape}",
                location=rule.path,
            )
            continue
        if not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
            report.add(
                "non-finite",
                "comparison input contains NaN or Infinity",
                location=rule.path,
            )
            continue

        if rule.kind == "scalar":
            if left.ndim != 1:
                report.add("shape", "scalar rule requires one value per row", location=rule.path)
                continue
            error = np.abs(left - right)
            allowed = abs_tol + rel_tol * np.abs(right)
        elif rule.kind == "vector":
            if left.ndim != 2 or left.shape[0] != len(actual_values):
                report.add(
                    "shape",
                    "vector rule requires one flat vector per row",
                    location=rule.path,
                )
                continue
            error = np.linalg.norm(left - right, axis=-1)
            allowed = abs_tol + rel_tol * np.linalg.norm(right, axis=-1)
        elif rule.kind == "quaternion":
            if left.ndim != 2 or left.shape[1] != 4:
                report.add(
                    "shape",
                    "quaternion rule requires four values per row",
                    location=rule.path,
                )
                continue
            left_norm = np.linalg.norm(left, axis=-1)
            right_norm = np.linalg.norm(right, axis=-1)
            invalid = np.flatnonzero(
                ~np.isclose(left_norm, 1.0, rtol=0.0, atol=1e-6)
                | ~np.isclose(right_norm, 1.0, rtol=0.0, atol=1e-6)
            )
            if invalid.size:
                report.add(
                    "invalid-quaternion",
                    "quaternion comparison input is not unit-normalized",
                    location=rule.path,
                    first_rows=[row_indices[index] for index in invalid[:5]],
                )
                continue
            error = _quaternion_angle(left, right)
            allowed = np.full_like(error, abs_tol, dtype=float)
        else:  # pragma: no cover
            raise ValueError(rule.kind)

        exceed = np.flatnonzero(error > allowed)
        worst = float(np.max(error)) if error.size else 0.0
        report.summary[f"{rule.path}.max_error"] = worst
        if exceed.size:
            report.add(
                "tolerance",
                f"{rule.path} exceeds tolerance in {exceed.size} samples",
                location=rule.path,
                max_error=worst,
                first_rows=[row_indices[index] for index in exceed[:5]],
                abs_tol=abs_tol,
                rel_tol=rel_tol,
            )

    if len(actual) > overlap and overlap >= 2:
        position_rule = next(
            (rule for rule in rules if rule.kind == "vector" and "position" in rule.path),
            None,
        )
        if position_rule:
            try:
                position_abs_tol = float(position_rule.abs_tol)
                if not math.isfinite(position_abs_tol) or position_abs_tol < 0:
                    raise ValueError("invalid position tolerance")
                compared = np.asarray(
                    [get_path(row, position_rule.path) for row in actual[:overlap]], dtype=float
                )
                first_extra = np.asarray(get_path(actual[overlap], position_rule.path), dtype=float)
                if not np.all(np.isfinite(compared)) or not np.all(np.isfinite(first_extra)):
                    raise ValueError("non-finite position")
                steps = np.linalg.norm(np.diff(compared, axis=0), axis=-1)
                largest = float(np.max(steps)) if steps.size else position_abs_tol
                largest = largest or position_abs_tol or 1e-12
                jump = float(np.linalg.norm(first_extra - compared[-1]))
                if jump > continuity_factor * largest:
                    report.add(
                        "tail-discontinuity",
                        "first unmatched row is not a continuous extension",
                        location=position_rule.path,
                        jump=jump,
                        allowed=continuity_factor * largest,
                    )
            except (KeyError, TypeError, ValueError, OverflowError):
                report.add(
                    "tail-unchecked",
                    "unmatched tail could not be checked for continuity",
                    Severity.WARNING,
                    position_rule.path,
                )
    return report
