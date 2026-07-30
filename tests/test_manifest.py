from pathlib import Path

import yaml

from launch_gnc_testkit.manifest import load_manifest, manifest_run_id, validate_manifest


EXAMPLE = Path(__file__).parents[1] / "examples" / "minimal_manifest.yaml"


def test_example_manifest_is_valid():
    manifest = load_manifest(EXAMPLE)
    report = validate_manifest(manifest)
    assert report.ok, report.to_markdown()


def test_run_id_ignores_created_at_and_declared_id():
    manifest = load_manifest(EXAMPLE)
    first = manifest_run_id(manifest)
    manifest["run"] = {"id": first, "created_at": "2099-01-01T00:00:00Z"}
    assert manifest_run_id(manifest) == first


def test_run_id_ignores_local_trace_path():
    manifest = load_manifest(EXAMPLE)
    first = manifest_run_id(manifest)
    manifest["trace"]["path"] = "/another/machine/run.ndjson"
    assert manifest_run_id(manifest) == first


def test_invalid_non_finite_manifest_returns_report():
    manifest = load_manifest(EXAMPLE)
    manifest["scenario"]["time_step_s"] = float("nan")
    report = validate_manifest(manifest)
    assert not report.ok
    assert any(item.code == "run-id-unavailable" for item in report.findings)
