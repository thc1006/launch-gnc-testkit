import json

import pytest

from launch_gnc_testkit.errors import ArtifactFormatError
from launch_gnc_testkit.trace import get_path, iter_trace, load_trace, write_trace


RECORDS = [{"step_index": 0, "time_s": 0.0}]


def test_jsonl_alias_and_iterator(tmp_path):
    path = tmp_path / "trace.jsonl"
    write_trace(RECORDS, path)
    assert list(iter_trace(path)) == RECORDS


def test_blank_ndjson_lines_are_ignored(tmp_path):
    path = tmp_path / "trace.ndjson"
    path.write_text('\n{"step_index": 0, "time_s": 0.0}\n\n', encoding="utf-8")
    assert load_trace(path) == RECORDS


def test_ndjson_record_must_be_object(tmp_path):
    path = tmp_path / "trace.ndjson"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="not an object"):
        load_trace(path)


def test_json_root_must_be_list_of_objects(tmp_path):
    path = tmp_path / "trace.json"
    path.write_text(json.dumps({"time_s": 0}), encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="list of objects"):
        load_trace(path)


def test_invalid_and_unsupported_input(tmp_path):
    invalid = tmp_path / "trace.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ArtifactFormatError, match="cannot read trace"):
        load_trace(invalid)
    with pytest.raises(ArtifactFormatError, match="unsupported"):
        load_trace(tmp_path / "trace.csv")


def test_parquet_dependency_error(tmp_path):
    with pytest.raises(ArtifactFormatError, match="parquet"):
        load_trace(tmp_path / "trace.parquet")
    with pytest.raises(ArtifactFormatError, match="parquet"):
        write_trace(RECORDS, tmp_path / "trace.parquet")


def test_unsupported_output_and_get_path(tmp_path):
    with pytest.raises(ArtifactFormatError, match="unsupported"):
        write_trace(RECORDS, tmp_path / "trace.csv")
    assert get_path({"a": {"b": 3}}, "a.b") == 3
    with pytest.raises(KeyError):
        get_path({"a": {}}, "a.b")
