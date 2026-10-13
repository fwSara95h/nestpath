"""Tests for :mod:`nestpath.flatten`: ``flatten`` and ``flatten_rows``.

Fixtures are invented data in the library's target shapes; the ``patient`` fixture is in
``conftest.py``. The behaviours pinned here are those of paste v3Fep60B (``recFlatten`` /
``flattenObj``: indices as keys, a ``sep``-joined key per leaf) and of the two ``flattenDict``
answers, 75196824 (the single-dict collapse, and rows from a list of records) and 75590907 (lists
kept as values), plus the deliberate changes: empty containers are values rather than dropped, a
non-container root is an error rather than ``{"": obj}``, and colliding keys raise rather than
overwrite. ``flatten_rows``' ``explode`` is the unnesting of a list column from answer 75808253,
done before the DataFrame exists. The Hypothesis properties at the end are plan-A step 5's:
``flatten`` never loses a leaf, ``collapse_single`` either keeps every leaf or raises, and
exploded rows are the cross product of the lists.
"""

from __future__ import annotations

import copy
import itertools
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nestpath import KeyCollisionError, flatten, flatten_rows, get, paths

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


# --- flatten_rows: normal ------------------------------------------------------------------

RECORDS = [
    {"id": 1, "obs": [{"v": 5, "u": "kg"}, {"v": 7, "u": "kg"}], "tags": ["a", "b"]},
    {"id": 2, "obs": [{"v": 9, "u": "cm"}], "tags": []},
    {"id": 3, "obs": [], "tags": ["c"]},
]


def test_flatten_rows_without_explode_is_flatten_per_record() -> None:
    assert flatten_rows(RECORDS) == [flatten(record) for record in RECORDS]
    assert flatten_rows(RECORDS, sep=".", lists="keep") == [
        flatten(record, sep=".", lists="keep") for record in RECORDS
    ]
    assert flatten_rows(RECORDS)[0] == {
        "id": 1,
        "obs_0_v": 5,
        "obs_0_u": "kg",
        "obs_1_v": 7,
        "obs_1_u": "kg",
        "tags_0": "a",
        "tags_1": "b",
    }


def test_flatten_rows_explode_gives_one_row_per_element() -> None:
    assert flatten_rows(RECORDS, explode=("obs",)) == [
        {"id": 1, "obs_v": 5, "obs_u": "kg", "tags_0": "a", "tags_1": "b"},
        {"id": 1, "obs_v": 7, "obs_u": "kg", "tags_0": "a", "tags_1": "b"},
        {"id": 2, "obs_v": 9, "obs_u": "cm", "tags": []},
    ]  # the position became the row, the other fields repeat, record 3 has no obs


def test_flatten_rows_explode_scalars_make_a_plain_column() -> None:
    rows = flatten_rows(RECORDS, explode=("tags",), lists="keep")
    assert [(row["id"], row["tags"]) for row in rows] == [(1, "a"), (1, "b"), (3, "c")]
    assert rows[0]["obs"] == RECORDS[0]["obs"]  # the other list stays a value under "keep"


def test_flatten_rows_explode_entries_are_keys_or_tuple_paths() -> None:
    nested = [{"id": 1, "a": {"obs": [{"v": 5}, {"v": 7}], "k": True}}]
    assert flatten_rows(nested, explode=(("a", "obs"),)) == [
        {"id": 1, "a_obs_v": 5, "a_k": True},
        {"id": 1, "a_obs_v": 7, "a_k": True},
    ]
    assert flatten_rows(RECORDS, explode=("obs",)) == flatten_rows(RECORDS, explode=(("obs",),))
    assert flatten_rows([[[1, 2], [3]]], explode=(0,)) == [{"0": 1, "1_0": 3}, {"0": 2, "1_0": 3}]


def test_flatten_rows_several_paths_give_the_cross_product_first_outermost() -> None:
    record = {"id": 1, "a": [1, 2, 3], "b": ["x", "y"]}
    rows = flatten_rows([record], explode=("a", "b"))
    assert [(row["a"], row["b"]) for row in rows] == [
        (1, "x"),
        (1, "y"),
        (2, "x"),
        (2, "y"),
        (3, "x"),
        (3, "y"),
    ]
    assert all(row["id"] == 1 for row in rows)
    assert [(row["a"], row["b"]) for row in flatten_rows([record], explode=("b", "a"))] == [
        (1, "x"),
        (2, "x"),
        (3, "x"),
        (1, "y"),
        (2, "y"),
        (3, "y"),
    ]


def test_flatten_rows_later_path_may_point_inside_an_earlier_element() -> None:
    panels = [
        {
            "id": 1,
            "obs": [
                {"code": "bp", "component": [{"v": 120}, {"v": 80}]},
                {"code": "hr", "component": [{"v": 70}]},
            ],
        }
    ]
    assert flatten_rows(panels, explode=("obs", ("obs", "component"))) == [
        {"id": 1, "obs_code": "bp", "obs_component_v": 120},
        {"id": 1, "obs_code": "bp", "obs_component_v": 80},
        {"id": 1, "obs_code": "hr", "obs_component_v": 70},
    ]


def test_flatten_rows_collapse_single_hoists_the_element() -> None:
    records = [{"id": 1, "obs": [{"v": 5}, {"v": 7}]}]
    assert flatten_rows(records, explode=("obs",), collapse_single=True) == [
        {"id": 1, "v": 5},
        {"id": 1, "v": 7},
    ]


# --- flatten_rows: missing -----------------------------------------------------------------


def test_flatten_rows_empty_none_or_missing_list_yields_no_rows() -> None:
    records = [{"id": 1, "obs": []}, {"id": 2, "obs": None}, {"id": 3}]
    assert flatten_rows(records, explode=("obs",)) == []
    assert flatten_rows(records, explode=(("a", "obs"),)) == []  # missing from the first step


def test_flatten_rows_keep_empty_keeps_the_record_without_the_slot() -> None:
    records = [{"id": 1, "obs": []}, {"id": 2, "obs": None}, {"id": 3}]
    records.append({"id": 4, "obs": [{"v": 5}]})
    assert flatten_rows(records, explode=("obs",), keep_empty=True) == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
        {"id": 4, "obs_v": 5},
    ]
    nested = [{"id": 1, "a": {"obs": [], "k": True}}, {"id": 2}]
    assert flatten_rows(nested, explode=(("a", "obs"),), keep_empty=True) == [
        {"id": 1, "a_k": True},
        {"id": 2},
    ]
    rows = flatten_rows([{"m": [[1, 2], []]}], explode=(("m", 1),), keep_empty=True)
    assert rows == [{"m_0_0": 1, "m_0_1": 2, "m_1": None}]  # a list position keeps its index


def test_flatten_rows_keep_empty_with_the_cross_product() -> None:
    record = {"id": 1, "a": [], "b": ["x", "y"]}
    assert flatten_rows([record], explode=("a", "b")) == []
    assert flatten_rows([record], explode=("a", "b"), keep_empty=True) == [
        {"id": 1, "b": "x"},
        {"id": 1, "b": "y"},
    ]


# --- flatten_rows: edge --------------------------------------------------------------------


def test_flatten_rows_non_list_at_the_path_raises() -> None:
    for value in ({"v": 5}, "abc", 5, b"xy", {1, 2}):
        with pytest.raises(TypeError, match="not a list"):
            flatten_rows([{"id": 1, "obs": value}], explode=("obs",))
    with pytest.raises(TypeError, match="mapping or a sequence"):
        flatten_rows([5])  # a record that is not a container: flatten's error


def test_flatten_rows_rejects_a_bare_string_explode_and_malformed_paths() -> None:
    with pytest.raises(TypeError, match="not a string"):
        flatten_rows(RECORDS, explode="obs")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one step"):
        flatten_rows(RECORDS, explode=((),))
    with pytest.raises(TypeError, match="key or a tuple path"):
        flatten_rows(RECORDS, explode=(["obs"],))  # type: ignore[arg-type]


def test_flatten_rows_does_not_modify_the_records() -> None:
    records = copy.deepcopy(RECORDS)
    rows = flatten_rows(records, explode=("obs", "tags"), keep_empty=True)
    assert records == RECORDS
    rows[0]["id"] = 99
    assert records[0]["id"] == 1


def test_flatten_rows_accepts_any_iterable_and_empty_input() -> None:
    assert flatten_rows([]) == []
    assert flatten_rows([], explode=("obs",)) == []
    assert flatten_rows(record for record in RECORDS[:1]) == [flatten(RECORDS[0])]
    assert flatten_rows(({"a": 1},)) == [{"a": 1}]


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


@given(
    st.lists(st.integers(), max_size=4),
    st.lists(st.text(max_size=2), max_size=4),
    st.text(max_size=5),
)
def test_flatten_rows_explodes_into_the_cross_product(a: list, b: list, label: str) -> None:
    record = {"label": label, "a": a, "b": b, "n": {"k": 1}}
    rows = flatten_rows([record], explode=("a", "b"))
    assert len(rows) == len(a) * len(b)
    assert [(row["a"], row["b"]) for row in rows] == list(itertools.product(a, b))
    assert all((row["label"], row["n_k"]) == (label, 1) for row in rows)
    kept = flatten_rows([record], explode=("a", "b"), keep_empty=True)
    assert len(kept) == max(len(a), 1) * max(len(b), 1)
