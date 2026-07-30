from launch_gnc_testkit.report import Report, Severity


def test_report_rendering_extension_and_dict():
    left = Report("left")
    left.summary["rows"] = 2
    left.add("warning", "watch", Severity.WARNING, "$.x", value=3)
    right = Report("right")
    right.add("error", "broken")
    left.extend(right)
    assert not left.ok
    data = left.to_dict()
    assert data["findings"][0]["severity"] == Severity.WARNING
    text = left.to_markdown()
    assert "Status:** FAIL" in text
    assert "value: `3`" in text


def test_empty_report_passes():
    report = Report("empty")
    assert report.ok
    assert "No findings" in report.to_markdown()
