from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .adapters.bpc import convert_file
from .canonical import atomic_write, digest_object, sha256_file
from .compare import ComparisonRule, compare_traces
from .errors import GncTestkitError
from .manifest import load_manifest, validate_manifest
from .seed import SeedTree
from .trace import load_trace
from .validate import validate_trace


def _emit(report, output: str | None, output_format: str = "markdown") -> int:
    if output_format == "json":
        text = json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n"
    else:
        text = report.to_markdown()
    if output:
        atomic_write(output, lambda handle: handle.write(text))
    else:
        print(text, end="")
    return 0 if report.ok else 1


def _load_rules(path: str) -> tuple[list[ComparisonRule], int, float]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("comparison rules root must be an object")
    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError("comparison rules must be a list")
    rules = [ComparisonRule(**item) for item in raw_rules]
    return (
        rules,
        int(data.get("row_count_abs_tol", 0)),
        float(data.get("continuity_factor", 3.0)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gnctest")
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("validate-manifest")
    item.add_argument("manifest")
    item.add_argument("--output")
    item.add_argument("--format", choices=("markdown", "json"), default="markdown")

    item = sub.add_parser("validate-trace")
    item.add_argument("trace")
    item.add_argument("--manifest")
    item.add_argument("--output")
    item.add_argument("--format", choices=("markdown", "json"), default="markdown")

    item = sub.add_parser("compare")
    item.add_argument("actual")
    item.add_argument("expected")
    item.add_argument("--rules", required=True)
    item.add_argument("--output")
    item.add_argument("--format", choices=("markdown", "json"), default="markdown")

    item = sub.add_parser("inspect")
    item.add_argument("trace")

    item = sub.add_parser("digest")
    item.add_argument("path")
    item.add_argument("--object", action="store_true")

    item = sub.add_parser("derive-seed")
    item.add_argument("root")
    item.add_argument("path", nargs="+")
    item.add_argument("--bits", type=int, default=128)

    item = sub.add_parser("convert-bpc")
    item.add_argument("source")
    item.add_argument("trace")
    item.add_argument("--manifest-out")
    item.add_argument("--source-commit", default="aa5ee7dcf1e715b9aeb7e90ca807a01b6c97062f")
    item.add_argument("--root-seed", default="unknown")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "validate-manifest":
        return _emit(
            validate_manifest(load_manifest(args.manifest)), args.output, args.format
        )
    if args.command == "validate-trace":
        manifest = load_manifest(args.manifest) if args.manifest else None
        return _emit(
            validate_trace(load_trace(args.trace), manifest), args.output, args.format
        )
    if args.command == "compare":
        rules, row_tol, continuity = _load_rules(args.rules)
        report = compare_traces(
            load_trace(args.actual),
            load_trace(args.expected),
            rules,
            row_count_abs_tol=row_tol,
            continuity_factor=continuity,
        )
        return _emit(report, args.output, args.format)
    if args.command == "inspect":
        records = load_trace(args.trace)
        fields = sorted({key for record in records for key in record})
        print(json.dumps({"rows": len(records), "top_level_fields": fields}, indent=2))
        return 0
    if args.command == "digest":
        if args.object:
            value = yaml.safe_load(Path(args.path).read_text(encoding="utf-8-sig"))
            print(digest_object(value))
        else:
            print(sha256_file(args.path))
        return 0
    if args.command == "derive-seed":
        root: int | str = int(args.root) if args.root.isdecimal() else args.root
        print(SeedTree(root).derive(*args.path, bits=args.bits))
        return 0
    if args.command == "convert-bpc":
        root_seed: int | str = (
            int(args.root_seed) if args.root_seed.isdecimal() else args.root_seed
        )
        convert_file(
            args.source,
            args.trace,
            manifest_path=args.manifest_out,
            source_commit=args.source_commit,
            root_seed=root_seed,
        )
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except (GncTestkitError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"gnctest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
