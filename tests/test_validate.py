import copy
from pathlib import Path

from launch_gnc_testkit.manifest import load_manifest
from launch_gnc_testkit.trace import load_trace
from launch_gnc_testkit.validate import validate_trace


ROOT = Path(__file__).parents[1]


def test_reference_trace_is_valid():
    report = validate_trace(
        load_trace(ROOT / "examples/reference_trace.ndjson"),
        load_manifest(ROOT / "examples/minimal_manifest.yaml"),
    )
    assert report.ok, report.to_markdown()


def test_non_increasing_time_is_rejected():
    records = load_trace(ROOT / "examples/reference_trace.ndjson")
    records[2]["time_s"] = records[1]["time_s"]
    assert not validate_trace(records).ok


def test_bad_quaternion_norm_is_rejected():
    records = load_trace(ROOT / "examples/reference_trace.ndjson")
    records[1]["truth"]["attitude_quaternion"] = [2.0, 0.0, 0.0, 0.0]
    assert not validate_trace(records).ok


def test_malformed_vector_is_reported_not_raised():
    records = load_trace(ROOT / "examples/reference_trace.ndjson")
    records[1]["truth"]["position_m"] = {"x": 1}
    report = validate_trace(records)
    assert not report.ok
    assert any(item.code == "vector-type" for item in report.findings)


def test_boolean_time_and_step_index_are_rejected():
    records = load_trace(ROOT / "examples/reference_trace.ndjson")
    records[0]["time_s"] = False
    records[0]["step_index"] = False
    report = validate_trace(records)
    assert {item.code for item in report.findings} >= {"time", "step-index-type"}


def test_invalid_validator_tolerance_and_manifest_shape_are_reported():
    records = load_trace(ROOT / "examples/reference_trace.ndjson")
    assert not validate_trace(records, quaternion_norm_tolerance=float("nan")).ok
    report = validate_trace(records, {"scenario": [], "coordinates": []})
    assert "coordinate-contract" in {item.code for item in report.findings}
