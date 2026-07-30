import json
from pathlib import Path

import pytest

from launch_gnc_testkit.canonical import atomic_write, canonical_json_bytes, digest_object
from launch_gnc_testkit.errors import ArtifactFormatError


def test_canonical_is_order_independent():
    assert digest_object({"b": 2, "a": 1}) == digest_object({"a": 1, "b": 2})


def test_non_finite_is_rejected():
    with pytest.raises(ArtifactFormatError):
        canonical_json_bytes({"x": float("nan")})


def test_atomic_write_leaves_complete_file(tmp_path):
    path = tmp_path / "out.json"
    atomic_write(path, lambda handle: json.dump({"ok": True}, handle))
    assert json.loads(path.read_text()) == {"ok": True}


def test_non_json_type_has_domain_error():
    with pytest.raises(ArtifactFormatError):
        canonical_json_bytes({"x": object()})


def test_failed_atomic_write_keeps_existing_destination(tmp_path):
    path = tmp_path / "out.json"
    path.write_text('{"old": true}', encoding="utf-8")

    def fail(handle):
        handle.write('{"new":')
        raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        atomic_write(path, fail)
    assert json.loads(path.read_text()) == {"old": True}
    assert not list(tmp_path.glob(".partial_*"))


def test_normalized_text_and_file_digest(tmp_path):
    from launch_gnc_testkit.canonical import normalized_text_digest, sha256_file

    assert normalized_text_digest(b"\xef\xbb\xbfa\r\n") == normalized_text_digest(b"a\n")
    path = tmp_path / "x.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
