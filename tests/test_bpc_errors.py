import json

import pytest

from launch_gnc_testkit.adapters.bpc import convert_file, convert_records
from launch_gnc_testkit.errors import ArtifactFormatError


def test_record_must_be_object():
    with pytest.raises(ArtifactFormatError, match="not an object"):
        convert_records([[]])


def test_time_must_be_finite_number():
    for value in (True, "wrong", float("inf"), None):
        with pytest.raises(ArtifactFormatError):
            convert_records([{"time": value}])


def test_malformed_state_becomes_unknown_truth():
    records = convert_records(
        [
            {
                "time": 0.0,
                "rocket_states": ["bad"] * 13,
                "balloon_states": [],
                "balloon_status": [],
            }
        ]
    )
    assert records[0]["truth"] is None


def test_source_root_and_json_errors(tmp_path):
    root = tmp_path / "root.json"
    root.write_text("{}", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="must be a JSON list"):
        convert_file(root, tmp_path / "out.ndjson")
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="cannot load"):
        convert_file(invalid, tmp_path / "out.ndjson")


def test_non_increasing_initial_time_is_rejected(tmp_path):
    source = tmp_path / "trajectory.json"
    source.write_text(json.dumps([{"time": 1.0}, {"time": 1.0}]), encoding="utf-8")
    output = tmp_path / "out.ndjson"
    with pytest.raises(ArtifactFormatError, match="increasing"):
        convert_file(source, output)
    assert not output.exists()


def test_variable_timestep_is_rejected_before_write(tmp_path):
    source = tmp_path / "trajectory.json"
    source.write_text(
        json.dumps([{"time": 0.0}, {"time": 0.1}, {"time": 0.25}]),
        encoding="utf-8",
    )
    output = tmp_path / "out.ndjson"
    with pytest.raises(ArtifactFormatError, match="constant"):
        convert_file(source, output)
    assert not output.exists()
