import copy

from launch_gnc_testkit.compare import ComparisonRule, compare_traces


BASE = [
    {
        "step_index": 0,
        "time_s": 0.0,
        "truth": {
            "position_m": [0.0, 0.0, 0.0],
            "attitude_quaternion": [1.0, 0.0, 0.0, 0.0],
        },
        "mode": "a",
    },
    {
        "step_index": 1,
        "time_s": 1.0,
        "truth": {
            "position_m": [1.0, 0.0, 0.0],
            "attitude_quaternion": [1.0, 0.0, 0.0, 0.0],
        },
        "mode": "b",
    },
]


def codes(report):
    return {item.code for item in report.findings}


def test_empty_and_row_count_paths():
    assert "no-overlap" in codes(compare_traces([], [], []))
    report = compare_traces(BASE, BASE[:1], [], row_count_abs_tol=0)
    assert "row-count" in codes(report)


def test_invalid_global_parameters():
    assert "invalid-row-tolerance" in codes(
        compare_traces(BASE, BASE, [], row_count_abs_tol=-1)
    )
    assert "invalid-continuity-factor" in codes(
        compare_traces(BASE, BASE, [], continuity_factor=0)
    )


def test_missing_required_and_allowed_field():
    actual = copy.deepcopy(BASE)
    del actual[1]["mode"]
    required = compare_traces(actual, BASE, [ComparisonRule("mode", "exact")])
    assert "missing-field" in codes(required)
    allowed = compare_traces(
        actual,
        BASE,
        [ComparisonRule("mode", "exact", allow_missing=True)],
    )
    assert allowed.ok
    assert allowed.findings[0].severity.value == "warning"


def test_exact_and_numeric_conversion_mismatch():
    actual = copy.deepcopy(BASE)
    actual[1]["mode"] = "wrong"
    assert "exact-mismatch" in codes(
        compare_traces(actual, BASE, [ComparisonRule("mode", "exact")])
    )
    actual[1]["time_s"] = "not-a-number"
    assert "numeric-conversion" in codes(
        compare_traces(actual, BASE, [ComparisonRule("time_s", "scalar")])
    )


def test_numeric_shape_and_non_finite_paths():
    actual = copy.deepcopy(BASE)
    actual[1]["truth"]["position_m"] = [1.0, 0.0]
    assert "numeric-conversion" in codes(
        compare_traces(
            actual,
            BASE,
            [ComparisonRule("truth.position_m", "vector")],
        )
    )

    nested = copy.deepcopy(BASE)
    for row in nested:
        row["matrix"] = [[0.0, 0.0, 0.0]]
    assert "shape" in codes(
        compare_traces(nested, nested, [ComparisonRule("matrix", "vector")])
    )

    non_finite = copy.deepcopy(BASE)
    non_finite[1]["time_s"] = float("inf")
    assert "non-finite" in codes(
        compare_traces(non_finite, BASE, [ComparisonRule("time_s", "scalar")])
    )


def test_scalar_and_quaternion_shape_paths():
    assert "shape" in codes(
        compare_traces(
            BASE,
            BASE,
            [ComparisonRule("truth.position_m", "scalar")],
        )
    )
    assert "shape" in codes(
        compare_traces(
            BASE,
            BASE,
            [ComparisonRule("truth.position_m", "quaternion")],
        )
    )


def test_relative_tolerance_and_tail_continuity():
    actual = copy.deepcopy(BASE)
    actual[1]["time_s"] = 1.05
    assert compare_traces(
        actual,
        BASE,
        [ComparisonRule("time_s", "scalar", rel_tol=0.1)],
    ).ok

    actual.append(
        {
            "step_index": 2,
            "time_s": 2.0,
            "truth": {
                "position_m": [1_000.0, 0.0, 0.0],
                "attitude_quaternion": [1.0, 0.0, 0.0, 0.0],
            },
        }
    )
    report = compare_traces(
        actual,
        BASE,
        [ComparisonRule("truth.position_m", "vector", abs_tol=0.1)],
        row_count_abs_tol=1,
    )
    assert "tail-discontinuity" in codes(report)


def test_tail_unchecked_is_warning():
    actual = copy.deepcopy(BASE)
    actual.append({"step_index": 2, "time_s": 2.0, "truth": {}})
    report = compare_traces(
        actual,
        BASE,
        [ComparisonRule("truth.position_m", "vector", abs_tol=0.1)],
        row_count_abs_tol=1,
    )
    assert report.ok
    assert "tail-unchecked" in codes(report)


def test_non_finite_rule_and_global_parameters_are_rejected():
    report = compare_traces(
        BASE,
        BASE,
        [ComparisonRule("time_s", "scalar", abs_tol=float("nan"))],
    )
    assert "invalid-rule" in codes(report)
    assert "invalid-row-tolerance" in codes(
        compare_traces(BASE, BASE, [], row_count_abs_tol=True)
    )
    assert "invalid-continuity-factor" in codes(
        compare_traces(BASE, BASE, [], continuity_factor=float("nan"))
    )


def test_non_unit_nonzero_quaternion_is_rejected():
    actual = copy.deepcopy(BASE)
    actual[1]["truth"]["attitude_quaternion"] = [2.0, 0.0, 0.0, 0.0]
    report = compare_traces(
        actual,
        BASE,
        [ComparisonRule("truth.attitude_quaternion", "quaternion")],
    )
    assert "invalid-quaternion" in codes(report)
