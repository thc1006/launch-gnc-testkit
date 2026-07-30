from pathlib import Path

from launch_gnc_testkit.trace import load_trace, write_trace


EXAMPLE = Path(__file__).parents[1] / "examples" / "reference_trace.ndjson"


def test_ndjson_round_trip(tmp_path):
    records = load_trace(EXAMPLE)
    output = tmp_path / "copy.ndjson"
    write_trace(records, output)
    assert load_trace(output) == records


def test_json_round_trip(tmp_path):
    records = load_trace(EXAMPLE)
    output = tmp_path / "copy.json"
    write_trace(records, output)
    assert load_trace(output) == records


def test_non_finite_write_is_atomic(tmp_path):
    import pytest

    output = tmp_path / "trace.ndjson"
    output.write_text('{"old": true}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        write_trace([{"time_s": float("nan")}], output)
    assert output.read_text(encoding="utf-8") == '{"old": true}\n'
    assert not list(tmp_path.glob(".partial_*"))
