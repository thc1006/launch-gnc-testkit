from pathlib import Path

from launch_gnc_testkit.adapters.bpc import convert_file
from launch_gnc_testkit.manifest import load_manifest, validate_manifest
from launch_gnc_testkit.trace import load_trace
from launch_gnc_testkit.validate import validate_trace


SOURCE = Path(__file__).parents[1] / "examples/bpc_trajectory.json"


def test_bpc_prelaunch_nan_becomes_null_truth(tmp_path):
    output = tmp_path / "trace.ndjson"
    manifest = tmp_path / "manifest.yaml"
    records, _ = convert_file(SOURCE, output, manifest_path=manifest)
    assert records[0]["truth"] is None
    assert records[1]["truth"]["position_m"] == [0.0, 0.0, 100.0]
    assert validate_trace(load_trace(output)).ok


def test_bpc_json_manifest_round_trip(tmp_path):
    output = tmp_path / "trace.ndjson"
    manifest_path = tmp_path / "manifest.json"
    _records, manifest = convert_file(SOURCE, output, manifest_path=manifest_path)
    loaded = load_manifest(manifest_path)
    assert loaded == manifest
    assert validate_manifest(loaded).ok


def test_bpc_manifest_rejects_unknown_extension(tmp_path):
    output = tmp_path / "trace.ndjson"
    manifest_path = tmp_path / "manifest.txt"
    try:
        convert_file(SOURCE, output, manifest_path=manifest_path)
    except Exception as exc:
        assert "must end in" in str(exc)
    else:
        raise AssertionError("unknown manifest extension was accepted")
    assert not output.exists()


def test_bpc_manifest_has_trace_digest_and_portable_run_id(tmp_path):
    left_trace = tmp_path / "left.ndjson"
    right_trace = tmp_path / "nested" / "right.ndjson"
    _left_records, left = convert_file(SOURCE, left_trace)
    _right_records, right = convert_file(SOURCE, right_trace)
    assert left["trace"]["digest"] == right["trace"]["digest"]
    assert left["run"]["id"] == right["run"]["id"]
    assert left["random"]["root_seed"] == "unknown"
