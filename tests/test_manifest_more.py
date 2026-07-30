import copy

import pytest

from launch_gnc_testkit.errors import ArtifactFormatError, ManifestValidationError
from launch_gnc_testkit.manifest import (
    load_manifest,
    manifest_run_id,
    require_valid_manifest,
    validate_manifest,
    write_manifest,
)


MANIFEST = {
    "schema_version": "0.1.0",
    "run": {"created_at": "2026-07-30T00:00:00Z"},
    "scenario": {"id": "case", "version": "1", "time_step_s": 0.1},
    "coordinates": {
        "world_frame": "ENU",
        "body_frame": "BODY",
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
    "random": {"root_seed": 1, "derivation": "named"},
    "simulator": {"name": "sim"},
    "controller": {"name": "controller"},
    "trace": {"format": "ndjson", "path": "run.ndjson"},
}


def with_id():
    value = copy.deepcopy(MANIFEST)
    value["run"]["id"] = manifest_run_id(value)
    return value


def test_json_and_yaml_write_round_trip(tmp_path):
    value = with_id()
    for name in ("manifest.json", "manifest.yaml", "manifest.yml"):
        path = tmp_path / name
        write_manifest(value, path)
        assert load_manifest(path) == value


def test_manifest_extensions_are_explicit(tmp_path):
    with pytest.raises(ArtifactFormatError, match="input must end"):
        load_manifest(tmp_path / "manifest.txt")
    with pytest.raises(ArtifactFormatError, match="output must end"):
        write_manifest(with_id(), tmp_path / "manifest.txt")


def test_bad_yaml_and_non_object_root(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("[", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="cannot load"):
        load_manifest(bad)
    root = tmp_path / "root.json"
    root.write_text("[]", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="root must be"):
        load_manifest(root)


def test_write_rejects_non_finite(tmp_path):
    value = with_id()
    value["scenario"]["time_step_s"] = float("nan")
    with pytest.raises(ArtifactFormatError, match="non-finite"):
        write_manifest(value, tmp_path / "manifest.yaml")


def test_declared_id_mismatch_and_require_valid():
    value = with_id()
    value["run"]["id"] = "0" * 24
    report = validate_manifest(value)
    assert any(item.code == "run-id-mismatch" for item in report.findings)
    with pytest.raises(ManifestValidationError):
        require_valid_manifest(value)


def test_warnings_do_not_fail_manifest():
    value = with_id()
    value["coordinates"]["body_frame"] = "ENU"
    value["trace"] = {"format": "json", "path": "run.ndjson"}
    value["run"]["id"] = manifest_run_id(value)
    report = validate_manifest(value)
    assert report.ok
    assert {item.code for item in report.findings} == {
        "ambiguous-frames",
        "trace-extension",
    }


def test_invalid_created_at_format_is_rejected():
    value = with_id()
    value["run"]["created_at"] = "not-a-date"
    value["run"]["id"] = manifest_run_id(value)
    assert not validate_manifest(value).ok
