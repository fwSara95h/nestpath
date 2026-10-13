"""Tests for :mod:`nestpath.fields`: ``select_fields``.

The ``patient`` fixture is in ``conftest.py``. The behaviour is the ``filters`` idiom of answer
75205202 — a list of ``(name, path[, default])`` applied to a record — with tuple paths only.
"""

from __future__ import annotations

import pytest

from nestpath import select_fields

SPEC = [
    ("id", ("id",)),
    ("family", ("name", 0, "family")),
    ("given", ("name", 0, "given", 0)),
    ("gender", ("gender",), "unknown"),
    ("prefix", ("name", 0, "prefix", 0), ""),
]


def test_select_fields_reads_a_row_in_spec_order(patient) -> None:
    assert select_fields(patient, SPEC) == {
        "id": "example-1",
        "family": "Rivera",
        "given": "Ana",
        "gender": "female",
        "prefix": "",
    }
    assert list(select_fields(patient, SPEC)) == ["id", "family", "given", "gender", "prefix"]


def test_select_fields_misses_use_the_entry_default_then_missing() -> None:
    assert select_fields({}, SPEC) == {
        "id": None,
        "family": None,
        "given": None,
        "gender": "unknown",
        "prefix": "",
    }
    assert select_fields({}, SPEC, missing="?") == {
        "id": "?",
        "family": "?",
        "given": "?",
        "gender": "unknown",
        "prefix": "",
    }
    assert select_fields(None, SPEC)["id"] is None  # a non-container record misses everything


def test_select_fields_present_none_is_a_hit() -> None:
    assert select_fields({"gender": None}, SPEC)["gender"] is None  # not "unknown"


def test_select_fields_same_spec_applied_to_many_records() -> None:
    records = [{"id": "a", "gender": "male"}, {"id": "b"}, {}]
    rows = [select_fields(record, SPEC) for record in records]
    assert [row["id"] for row in rows] == ["a", "b", None]
    assert [row["gender"] for row in rows] == ["male", "unknown", "unknown"]


def test_select_fields_empty_spec_gives_empty_row(patient) -> None:
    assert select_fields(patient, []) == {}


def test_select_fields_rejects_non_tuple_paths(patient) -> None:
    with pytest.raises(TypeError, match="must be a tuple"):
        select_fields(patient, [("id", "id")])  # a string would be read as ("i", "d")
    with pytest.raises(TypeError, match="must be a tuple"):
        select_fields(patient, [("family", ["name", 0, "family"])])


def test_select_fields_rejects_malformed_and_duplicate_entries(patient) -> None:
    with pytest.raises(ValueError, match="must be"):
        select_fields(patient, [("id",)])
    with pytest.raises(ValueError, match="must be"):
        select_fields(patient, [("id", ("id",), None, "extra")])
    with pytest.raises(ValueError, match="appears twice"):
        select_fields(patient, [("id", ("id",)), ("id", ("gender",))])
