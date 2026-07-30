from pathlib import Path

from launch_gnc_testkit.cli import main


ROOT = Path(__file__).parents[1]


def test_validate_manifest_cli():
    assert main(["validate-manifest", str(ROOT / "examples/minimal_manifest.yaml")]) == 0


def test_compare_cli():
    trace = str(ROOT / "examples/reference_trace.ndjson")
    rules = str(ROOT / "examples/comparison_rules.yaml")
    assert main(["compare", trace, trace, "--rules", rules]) == 0


def test_validate_manifest_json_cli(capsys):
    assert (
        main(
            [
                "validate-manifest",
                str(ROOT / "examples/minimal_manifest.yaml"),
                "--format",
                "json",
            ]
        )
        == 0
    )
    assert '"ok": true' in capsys.readouterr().out


def test_cli_reports_expected_error_without_traceback(tmp_path, capsys):
    result = main(
        [
            "convert-bpc",
            str(ROOT / "examples/bpc_trajectory.json"),
            str(tmp_path / "trace.ndjson"),
            "--manifest-out",
            str(tmp_path / "manifest.txt"),
        ]
    )
    assert result == 2
    error = capsys.readouterr().err
    assert error.startswith("gnctest:")
    assert "Traceback" not in error
