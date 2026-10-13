"""Tests for :mod:`nestpath.flatten`: ``flatten`` (and, below, ``flatten_rows``).

Fixtures are invented data in the library's target shapes; the ``patient`` fixture is in
``conftest.py``. The behaviours pinned here are those of paste v3Fep60B (``recFlatten`` /
``flattenObj``: indices as keys, a ``sep``-joined key per leaf) and of the two ``flattenDict``
answers, 75196824 (the single-dict collapse) and 75590907 (lists kept as values), plus the
deliberate changes: empty containers are values rather than dropped, a non-container root is an
error rather than ``{"": obj}``, and colliding keys raise rather than overwrite. The Hypothesis
properties at the end are plan-A step 5's: ``flatten`` never loses a leaf, and ``collapse_single``
either keeps every leaf or raises.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nestpath import KeyCollisionError, flatten, get, paths

# --- flatten: normal -----------------------------------------------------------------------


def test_flatten_joins_each_leaf_path_with_sep(patient) -> None:
    assert flatten(patient) == {
        "resourceType": "Patient",
        "id": "example-1",
        "name_0_family": "Rivera",
        "name_0_given_0": "Ana",
        "name_0_given_1": "Lucia",
        "gender": "female",
        "birthDate": "1984-03-09",
    }
    assert list(flatten(patient)) == [  # depth first, in container order
        "resourceType",
        "id",
        "name_0_family",
        "name_0_given_0",
        "name_0_given_1",
        "gender",
        "birthDate",
    ]


def test_flatten_sep_and_non_string_steps() -> None:
    nested = {"a": {"b": {"c": 1}}, 0: {"x": 2}, "k": (10, 20)}
    assert flatten(nested, sep=".") == {"a.b.c": 1, "0.x": 2, "k.0": 10, "k.1": 20}
    assert flatten(nested, sep="") == {"abc": 1, "0x": 2, "k0": 10, "k1": 20}
    assert flatten({("a", "b"): 1}) == {"('a', 'b')": 1}  # any key becomes its str()


def test_flatten_root_may_be_a_sequence() -> None:
    assert flatten([{"a": 1}, {"a": 2}]) == {"0_a": 1, "1_a": 2}
    assert flatten(({"a": 1},)) == {"0_a": 1}
    assert flatten([1, [2, 3]]) == {"0": 1, "1_0": 2, "1_1": 3}


def test_flatten_agrees_with_paths_and_get() -> None:
    nested = {"a": 1, "b": {"c": 2, "d": [3, {"e": 4}]}, "f": []}
    flat = flatten(nested)
    assert list(flat) == ["a", "b_c", "b_d_0", "b_d_1_e", "f"]
    for path in paths(nested):
        assert flat["_".join(map(str, path))] is get(nested, *path)


# --- flatten: lists="keep" -----------------------------------------------------------------


def test_flatten_keep_leaves_sequences_as_values(patient) -> None:
    assert flatten(patient, lists="keep") == {
        "resourceType": "Patient",
        "id": "example-1",
        "name": [{"family": "Rivera", "given": ["Ana", "Lucia"]}],  # nested dicts stay nested
        "gender": "female",
        "birthDate": "1984-03-09",
    }
    assert flatten({"a": {"b": (1, 2)}, "c": [3]}, lists="keep") == {"a_b": (1, 2), "c": [3]}


def test_flatten_keep_still_walks_a_root_sequence() -> None:
    assert flatten([{"a": [1, 2]}, {"a": [3]}], lists="keep") == {"0_a": [1, 2], "1_a": [3]}


# --- flatten: missing and edge -------------------------------------------------------------


def test_flatten_empty_containers_are_values_not_lost() -> None:
    assert flatten({"a": {}, "b": [], "c": {"d": []}}) == {"a": {}, "b": [], "c_d": []}
    assert flatten({}) == {}
    assert flatten([]) == {}


def test_flatten_present_none_and_scalars_are_kept() -> None:
    assert flatten({"a": None, "b": 0, "c": False, "d": ""}) == {
        "a": None,
        "b": 0,
        "c": False,
        "d": "",
    }


def test_flatten_strings_bytes_and_sets_are_values() -> None:
    assert flatten({"s": "ab", "v": b"xy", "u": {1}, "t": (1,)}) == {
        "s": "ab",  # not s_0, s_1
        "v": b"xy",
        "u": {1},  # a set cannot be indexed, so it is a value
        "t_0": 1,
    }


def test_flatten_non_container_root_raises() -> None:
    for root in (5, "abc", None, {1, 2}, b"xy"):
        with pytest.raises(TypeError, match="mapping or a sequence"):
            flatten(root)


def test_flatten_rejects_bad_sep_and_lists() -> None:
    with pytest.raises(TypeError, match="sep must be a str"):
        flatten({"a": 1}, sep=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lists must be"):
        flatten({"a": 1}, lists="explode")  # type: ignore[arg-type]


# --- flatten: collisions -------------------------------------------------------------------


def test_flatten_collision_from_the_separator_inside_a_key() -> None:
    with pytest.raises(KeyCollisionError, match=r"\('a_b',\) and \('a', 'b'\)") as info:
        flatten({"a_b": 1, "a": {"b": 2}})
    assert (info.value.key, info.value.first, info.value.second) == ("a_b", ("a_b",), ("a", "b"))
    assert isinstance(info.value, ValueError)
    assert flatten({"a_b": 1, "a": {"b": 2}}, sep=".") == {"a_b": 1, "a.b": 2}  # another sep


def test_flatten_collision_from_keys_with_the_same_str() -> None:
    with pytest.raises(KeyCollisionError, match="'1'"):
        flatten({1: "int", "1": "str"})
    with pytest.raises(KeyCollisionError):
        flatten({"a": [10], "a_0": 20})  # an index and a key read the same


def test_flatten_no_collision_when_the_joined_keys_differ() -> None:
    assert flatten({"a_b": 1, "a": {"c": 2}}) == {"a_b": 1, "a_c": 2}
    assert flatten({"a": {"b": 1}, "a_": {"b": 2}}) == {"a_b": 1, "a__b": 2}


# --- flatten: collapse_single --------------------------------------------------------------


def test_collapse_single_drops_the_step_of_a_lone_container() -> None:
    # the shape of answer 75196824: one dict value beside scalars, two dicts inside it
    metric = {"metric": "corr", "result": {"cur": {"p": 0.1, "q": None}, "ref": {"p": 0.7}}}
    assert flatten(metric, collapse_single=True) == {
        "metric": "corr",
        "cur_p": 0.1,
        "cur_q": None,
        "ref_p": 0.7,
    }
    assert flatten(metric) == {
        "metric": "corr",
        "result_cur_p": 0.1,
        "result_cur_q": None,
        "result_ref_p": 0.7,
    }
    assert flatten({"a": {"b": {"c": 1}}}, collapse_single=True) == {"c": 1}  # every level


def test_collapse_single_keeps_steps_where_two_containers_sit() -> None:
    assert flatten({"a": {"x": 1}, "b": {"x": 2}}, collapse_single=True) == {"a_x": 1, "b_x": 2}
    assert flatten({"a": {"x": 1}, "b": [2]}, collapse_single=True) == {"a_x": 1, "b_0": 2}


def test_collapse_single_counts_containers_by_the_lists_rule() -> None:
    record = {"id": 1, "tags": ["a", "b"]}
    assert flatten(record, collapse_single=True) == {"id": 1, "0": "a", "1": "b"}  # bare indices
    assert flatten(record, lists="keep", collapse_single=True) == record  # the list is a value
    assert flatten({"a": {}, "b": {"c": 1}}, collapse_single=True) == {"a": {}, "c": 1}


def test_collapse_single_collision_raises() -> None:
    with pytest.raises(KeyCollisionError, match=r"\('a',\) and \('b', 'a'\)"):
        flatten({"a": 1, "b": {"a": 2}}, collapse_single=True)


# --- the step-5 properties -----------------------------------------------------------------

scalars = st.none() | st.booleans() | st.integers() | st.text(max_size=3)
keys = st.text(alphabet="abcxyz", min_size=1, max_size=3)  # no separator: paths cannot collide
branches = st.recursive(
    scalars,
    lambda inner: st.lists(inner, max_size=4) | st.dictionaries(keys, inner, max_size=4),
    max_leaves=25,
)
roots = st.lists(branches, max_size=4) | st.dictionaries(keys, branches, max_size=4)


@given(roots)
def test_flatten_never_loses_a_leaf(tree: Any) -> None:
    leaves = [(path, get(tree, *path)) for path in paths(tree)]
    flat = flatten(tree)
    assert list(flat) == ["_".join(map(str, path)) for path, _ in leaves]
    for (_, leaf), value in zip(leaves, flat.values(), strict=True):
        assert value is leaf


@given(roots)
def test_collapse_single_keeps_every_leaf_or_raises(tree: Any) -> None:
    leaves = [get(tree, *path) for path in paths(tree)]
    try:
        flat = flatten(tree, collapse_single=True)
    except KeyCollisionError:
        return
    assert all(value is leaf for value, leaf in zip(flat.values(), leaves, strict=True))
