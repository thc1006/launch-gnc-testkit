import json
from pathlib import Path

from launch_gnc_testkit.cli import main


ROOT = Path(__file__).parents[1]
TRACE = ROOT / "examples/reference_trace.ndjson"
MANIFEST = ROOT / "examples/minimal_manifest.yaml"


def test_inspect_digest_seed_and_object_commands(capsys):
    assert main(["inspect", str(TRACE)]) == 0
    assert json.loads(capsys.readouterr().out)["rows"] == 3

    assert main(["digest", str(TRACE)]) == 0
    assert len(capsys.readouterr().out.strip()) == 64

    assert main(["digest", str(MANIFEST), "--object"]) == 0
    assert len(capsys.readouterr().out.strip()) == 64

    assert main(["derive-seed", "root", "sensor", "gyro", "--bits", "64"]) == 0
    assert int(capsys.readouterr().out.strip()) >= 0


def test_validate_trace_and_output_file(tmp_path):
    output = tmp_path / "report.json"
    result = main(
        [
            "validate-trace",
            str(TRACE),
            "--manifest",
            str(MANIFEST),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    assert result == 0
    assert json.loads(output.read_text(encoding="utf-8"))["ok"] is True


def test_convert_command_with_numeric_seed(tmp_path):
    trace = tmp_path / "converted.ndjson"
    manifest = tmp_path / "manifest.yaml"
    assert (
        main(
            [
                "convert-bpc",
                str(ROOT / "examples/bpc_trajectory.json"),
                str(trace),
                "--manifest-out",
                str(manifest),
                "--root-seed",
                "42",
            ]
        )
        == 0
    )
    assert "root_seed: 42" in manifest.read_text(encoding="utf-8")


def test_bad_rules_are_reported(tmp_path, capsys):
    rules = tmp_path / "rules.yaml"
    rules.write_text("rules: nope\n", encoding="utf-8")
    result = main(["compare", str(TRACE), str(TRACE), "--rules", str(rules)])
    assert result == 2
    assert capsys.readouterr().err.startswith("gnctest:")
