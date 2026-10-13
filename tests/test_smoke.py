"""Smoke test: the package imports, carries a version, and exposes the planned public API."""

from __future__ import annotations

import re

import nestpath

PUBLIC_API = {
    "get",
    "getter",
    "paths",
    "flatten",
    "flatten_rows",
    "select_fields",
    "to_frame",
    "KeyCollisionError",
}


def test_version_looks_like_a_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+(\.dev\d+)?", nestpath.__version__)


def test_public_api_is_exported() -> None:
    assert PUBLIC_API <= set(nestpath.__all__)
    for name in PUBLIC_API:
        assert callable(getattr(nestpath, name))
