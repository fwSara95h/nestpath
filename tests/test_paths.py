"""Tests for :mod:`nestpath.paths`: ``get`` and ``getter`` (``paths`` follows).

Fixtures are invented data in the library's target shapes; the ``patient`` fixture is in
``conftest.py``. The behaviours pinned here are those of answer 75466591 (optional fields read
with a default) and paste NRxKRJPn (``getVal_byPath``), plus the one deliberate change: strings
are values, never containers.
"""

from __future__ import annotations

import pytest

from nestpath import get, getter

# --- get: normal ---------------------------------------------------------------------------


def test_get_follows_keys_and_indices(patient) -> None:
    assert get(patient, "id") == "example-1"
    assert get(patient, "name", 0, "family") == "Rivera"
    assert get(patient, "name", 0, "given", 0) == "Ana"
    assert get(patient, "name", 0, "given", -1) == "Lucia"  # negative index


def test_get_without_steps_returns_the_object(patient) -> None:
    assert get(patient) is patient
    assert get(None) is None


def test_get_on_mappings_treats_every_step_as_a_key() -> None:
    assert get({0: "zero"}, 0) == "zero"  # an int key on a dict is a key, not an index
    assert get({("a", "b"): 1}, ("a", "b")) == 1  # a tuple argument is one tuple key
    assert get({"a": {"b": {"c": 3}}}, "a", "b", "c") == 3


def test_get_works_on_tuples_and_any_subscriptable() -> None:
    class Grid:
        def __getitem__(self, step):
            if step == "ok":
                return "hit"
            raise KeyError(step)

    assert get(("x", "y"), 1) == "y"
    assert get({"g": Grid()}, "g", "ok") == "hit"
    assert get({"g": Grid()}, "g", "no", default="miss") == "miss"


# --- get: missing --------------------------------------------------------------------------


def test_get_misses_give_the_default(patient) -> None:
    assert get(patient, "address") is None
    assert get(patient, "address", default="?") == "?"
    assert get(patient, "name", 5, "family", default="?") == "?"  # index out of range
    assert get(patient, "name", "family", default="?") == "?"  # string step on a list
    assert get(patient, "name", 0, "prefix", 0, default="") == ""  # missing, then indexed
    assert get(patient, "id", "x", default="?") == "?"  # step into a string value
    assert get(patient, "birthDate", 0, 0, default="?") == "?"


def test_get_steps_into_none_or_numbers_are_misses() -> None:
    assert get({"a": None}, "a", "b", default="?") == "?"
    assert get({"a": 5}, "a", 0, default="?") == "?"
    assert get(None, "a", default="?") == "?"
    assert get(5, 0, default="?") == "?"


def test_get_present_none_is_a_hit_not_a_miss() -> None:
    assert get({"a": None}, "a", default="?") is None
    assert get([None], 0, default="?") is None


# --- get: edge -----------------------------------------------------------------------------


def test_get_strings_and_bytes_are_values_not_containers() -> None:
    assert get("abc", 0) is None  # not "a"
    assert get({"s": "abc"}, "s", 0, default="?") == "?"
    assert get(b"abc", 0, default="?") == "?"
    assert get(bytearray(b"abc"), -1, default="?") == "?"


def test_get_unhashable_key_is_a_miss_but_other_errors_propagate() -> None:
    assert get({"a": 1}, ["a"], default="?") == "?"  # TypeError from the dict lookup

    class Broken:
        def __getitem__(self, step):
            raise ValueError("not a miss")

    with pytest.raises(ValueError, match="not a miss"):
        get(Broken(), "anything")


def test_get_default_can_be_any_object() -> None:
    sentinel = object()
    assert get({}, "a", default=sentinel) is sentinel
    assert get({}, "a", default=[]) == []


# --- getter --------------------------------------------------------------------------------


def test_getter_reads_a_path(patient) -> None:
    family = getter("name", 0, "family")
    assert family(patient) == "Rivera"
    assert family({}) is None


def test_getter_as_sort_key_and_in_map() -> None:
    rows = [{"score": 3, "id": "a"}, {"score": 1, "id": "b"}, {"id": "c"}]
    assert [r["id"] for r in sorted(rows, key=getter("score", default=0))] == ["c", "b", "a"]
    assert list(map(getter("score"), rows)) == [3, 1, None]
    assert max(rows, key=getter("score", default=-1))["id"] == "a"


def test_getter_default_is_bound_when_made() -> None:
    read = getter("missing", default="d")
    assert read({}) == "d"
    assert read({"missing": None}) is None  # present None is a hit
    assert getter()({"a": 1}) == {"a": 1}  # no steps: identity
