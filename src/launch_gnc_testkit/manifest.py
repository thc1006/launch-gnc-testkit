from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .canonical import atomic_write, canonical_json_bytes, digest_object
from .errors import ArtifactFormatError, ManifestValidationError
from .report import Report, Severity

SCHEMA_VERSION = "0.1.0"


def _manifest_schema() -> dict[str, Any]:
    resource = files("launch_gnc_testkit.schemas").joinpath("manifest.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def load_manifest(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml"):
        raise ArtifactFormatError(
            f"manifest input must end in .json, .yaml, or .yml: {source}"
        )
    try:
        text = source.read_text(encoding="utf-8-sig")
        if suffix == ".json":
            value = json.loads(text)
        else:
            value = yaml.safe_load(text)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ArtifactFormatError(f"cannot load manifest {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactFormatError("manifest root must be an object")
    return value


def write_manifest(manifest: dict[str, Any], path: str | Path) -> None:
    """Write a manifest atomically, choosing strict JSON or YAML by suffix."""

    # YAML can encode NaN and custom scalar types that are not portable JSON.
    # Validate the shared artifact model before either serializer is used.
    canonical_json_bytes(manifest)
    destination = Path(path)
    suffix = destination.suffix.lower()
    if suffix == ".json":

        def write_json(handle) -> None:
            json.dump(
                manifest,
                handle,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            handle.write("\n")

        atomic_write(destination, write_json)
        return
    if suffix in (".yaml", ".yml"):
        atomic_write(
            destination,
            lambda handle: yaml.safe_dump(
                manifest, handle, sort_keys=False, allow_unicode=True
            ),
        )
        return
    raise ArtifactFormatError(
        f"manifest output must end in .json, .yaml, or .yml: {destination}"
    )


def _identity_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return the portable content identity of a run manifest.

    Creation time, the declared ID, and the local trace pathname are transport
    metadata. They must not make the same run acquire a different identity on a
    different machine. A trace digest, when present, remains part of the identity.
    """

    identity = copy.deepcopy(manifest)
    run = identity.get("run")
    if isinstance(run, dict):
        run.pop("id", None)
        run.pop("created_at", None)
    trace = identity.get("trace")
    if isinstance(trace, dict):
        trace.pop("path", None)
    return identity


def manifest_run_id(manifest: dict[str, Any]) -> str:
    return digest_object(_identity_manifest(manifest))[:24]


def validate_manifest(manifest: dict[str, Any]) -> Report:
    report = Report("Manifest validation")
    validator = jsonschema.Draft202012Validator(
        _manifest_schema(), format_checker=jsonschema.FormatChecker()
    )
    for error in sorted(
        validator.iter_errors(manifest),
        key=lambda item: tuple(str(part) for part in item.path),
    ):
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        report.add("schema", error.message, location=location)

    try:
        calculated = manifest_run_id(manifest)
    except ArtifactFormatError as exc:
        calculated = None
        report.add("run-id-unavailable", str(exc), location="$")
    report.summary["calculated_run_id"] = calculated
    declared = manifest.get("run", {}).get("id") if isinstance(manifest.get("run"), dict) else None
    if calculated and declared and declared != calculated:
        report.add(
            "run-id-mismatch",
            "declared run.id does not match the portable manifest content",
            location="$.run.id",
            declared=declared,
            calculated=calculated,
        )

    frame = manifest.get("coordinates", {})
    if (
        isinstance(frame, dict)
        and frame.get("world_frame")
        and frame.get("world_frame") == frame.get("body_frame")
    ):
        report.add(
            "ambiguous-frames",
            "world and body frames use the same identifier; declare distinct semantics",
            Severity.WARNING,
            "$.coordinates",
        )

    trace = manifest.get("trace", {})
    if isinstance(trace, dict):
        trace_format = trace.get("format")
        path = str(trace.get("path", ""))
        expected_suffix = {
            "parquet": ".parquet",
            "ndjson": ".ndjson",
            "jsonl": ".jsonl",
            "json": ".json",
        }.get(trace_format)
        if expected_suffix and not path.lower().endswith(expected_suffix):
            report.add(
                "trace-extension",
                f"{trace_format} trace path does not end in {expected_suffix}",
                Severity.WARNING,
                "$.trace.path",
            )
    return report


def require_valid_manifest(manifest: dict[str, Any]) -> None:
    report = validate_manifest(manifest)
    if not report.ok:
        raise ManifestValidationError(report.to_markdown())
