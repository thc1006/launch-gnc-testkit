from pathlib import Path

from launch_gnc_testkit.compare import ComparisonRule, compare_traces
from launch_gnc_testkit.trace import load_trace


TRACE = Path(__file__).parents[1] / "examples/reference_trace.ndjson"
RULES = [
    ComparisonRule("time_s", "scalar", abs_tol=1e-12),
    ComparisonRule("truth.position_m", "vector", abs_tol=0.5),
    ComparisonRule("truth.attitude_quaternion", "quaternion", abs_tol=1e-3),
]


def test_trace_matches_itself():
    records = load_trace(TRACE)
    assert compare_traces(records, records, RULES).ok


def test_vector_displacement_uses_vector_norm():
    actual = load_trace(TRACE)
    expected = load_trace(TRACE)
    actual[1]["truth"]["position_m"] = [0.4, 0.4, 100.5]
    report = compare_traces(actual, expected, RULES)
    assert not report.ok


def test_quaternion_sign_is_equivalent():
    actual = load_trace(TRACE)
    expected = load_trace(TRACE)
    actual[1]["truth"]["attitude_quaternion"] = [-1.0, 0.0, 0.0, 0.0]
    assert compare_traces(actual, expected, RULES).ok


def test_zero_norm_quaternion_is_rejected():
    actual = load_trace(TRACE)
    expected = load_trace(TRACE)
    actual[1]["truth"]["attitude_quaternion"] = [0.0, 0.0, 0.0, 0.0]
    report = compare_traces(actual, expected, RULES)
    assert not report.ok
    assert any(item.code == "invalid-quaternion" for item in report.findings)


def test_negative_tolerance_is_rejected():
    records = load_trace(TRACE)
    report = compare_traces(
        records,
        records,
        [ComparisonRule("time_s", "scalar", abs_tol=-1.0)],
    )
    assert not report.ok
    assert any(item.code == "invalid-rule" for item in report.findings)
