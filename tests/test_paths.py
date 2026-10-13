"""Tests for :mod:`nestpath.paths`: ``get``, ``getter`` and ``paths``.

Fixtures are invented data in the library's target shapes; the ``patient`` fixture is in
``conftest.py``. The behaviours pinned here are those of answer 75466591 (optional fields read
with a default) and paste NRxKRJPn (``getVal_byPath``, ``getObjPaths``), plus the deliberate
changes: strings are values, never containers, and every leaf gets a path. The Hypothesis
property at the end is the one plan-A step 5 asks for: ``get`` follows every path ``paths``
yields, and reaches exactly the leaves.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nestpath import get, getter, paths

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


# --- paths ---------------------------------------------------------------------------------

NESTED = {"a": 1, "b": {"c": 2, "d": [3, {"e": 4}]}, "f": []}


def test_paths_yields_every_leaf_depth_first_in_order() -> None:
    assert list(paths(NESTED)) == [
        ("a",),
        ("b", "c"),
        ("b", "d", 0),
        ("b", "d", 1, "e"),
        ("f",),  # an empty container is a leaf
    ]
    assert list(paths(patient_like())) == [
        ("resourceType",),
        ("id",),
        ("name", 0, "family"),
        ("name", 0, "given", 0),
        ("name", 0, "given", 1),
        ("gender",),
        ("birthDate",),
    ]


def test_paths_with_intermediates_in_pre_order() -> None:
    assert list(paths(NESTED, leaves_only=False)) == [
        ("a",),
        ("b",),
        ("b", "c"),
        ("b", "d"),
        ("b", "d", 0),
        ("b", "d", 1),
        ("b", "d", 1, "e"),
        ("f",),
    ]


def test_paths_of_scalars_strings_and_empty_roots_are_nothing() -> None:
    assert list(paths(5)) == []
    assert list(paths("abc")) == []  # a string is a value, not three characters
    assert list(paths(None)) == []
    assert list(paths({})) == []
    assert list(paths([])) == []
    assert list(paths({}, leaves_only=False)) == []


def test_paths_container_rule() -> None:
    assert list(paths({"s": "ab", "t": (1, 2), "u": {1, 2}, "v": b"xy"})) == [
        ("s",),  # strings are leaves
        ("t", 0),  # tuples are sequences
        ("t", 1),
        ("u",),  # sets are leaves: get could not index into them
        ("v",),  # bytes are leaves
    ]
    assert list(paths({"a": {}, "b": [], "c": {"d": {}}})) == [("a",), ("b",), ("c", "d")]


def test_paths_is_lazy() -> None:
    it = paths(NESTED)
    assert next(it) == ("a",)
    assert next(it) == ("b", "c")


def test_every_path_can_be_followed_by_get() -> None:
    missing = object()
    for path in paths(NESTED, leaves_only=False):
        assert get(NESTED, *path, default=missing) is not missing


def patient_like() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "p1",
        "name": [{"family": "Rivera", "given": ["Ana", "Lucia"]}],
        "gender": "female",
        "birthDate": "1984-03-09",
    }


# --- the step-5 property: get follows every path that paths yields -------------------------

scalars = st.none() | st.booleans() | st.integers() | st.text(max_size=5)
keys = st.text(max_size=3)
trees = st.recursive(
    scalars,
    lambda inner: st.lists(inner, max_size=4) | st.dictionaries(keys, inner, max_size=4),
    max_leaves=25,
)


def reference_leaves(obj: Any, prefix: tuple = ()) -> list[tuple[tuple, Any]]:
    """An independent walk: ``(path, leaf)`` for every leaf, empty containers included."""
    if isinstance(obj, dict) and obj:
        return [pair for k, v in obj.items() for pair in reference_leaves(v, (*prefix, k))]
    if isinstance(obj, list) and obj:
        return [pair for i, v in enumerate(obj) for pair in reference_leaves(v, (*prefix, i))]
    return [(prefix, obj)] if prefix else []


@given(trees)
def test_get_reaches_exactly_the_leaves_that_paths_yields(tree: Any) -> None:
    expected = reference_leaves(tree)
    assert list(paths(tree)) == [path for path, _ in expected]
    missing = object()
    for path, leaf in expected:
        assert get(tree, *path, default=missing) is leaf


@given(trees)
def test_leaf_paths_are_a_subsequence_of_all_paths(tree: Any) -> None:
    every = list(paths(tree, leaves_only=False))
    leaves = list(paths(tree))
    assert set(leaves) <= set(every)
    assert len(every) == len(set(every))  # no path twice
    assert [p for p in every if p in set(leaves)] == leaves  # same relative order
