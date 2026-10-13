"""Tests for :mod:`nestpath.pandas_ext`: ``to_frame``.

Fixtures are invented data in the library's target shapes. The two branches pinned here are
answer 75590907's (chosen paths with defaults → columns: ``spec``) and answer 75196824's
(flatten every record, then ``pd.DataFrame(rows)``: no spec), plus the requirement the FHIR example
surfaced: with a spec, zero records still give the spec's columns. Every assertion about an empty
cell uses ``pd.isna`` because pandas 3 stores ``None`` in a string column as NaN; the module is
skipped when pandas is not installed, and one test checks the error message for that case.
"""

from __future__ import annotations

import sys

import pytest

from nestpath import flatten_rows, to_frame

pd = pytest.importorskip("pandas")

SPEC = [
    ("id", ("id",)),
    ("family", ("name", 0, "family")),
    ("gender", ("gender",), "unknown"),
    ("deceased", ("deceasedDateTime",)),
]

PATIENTS = [
    {"id": "p1", "name": [{"family": "Rivera"}], "gender": "female"},
    {"id": "p2", "name": [{"family": "Ortiz"}], "gender": "male", "deceasedDateTime": "2001-01-01"},
    {"id": "p3"},
]

RECORDS = [
    {"id": 1, "obs": [{"v": 5, "u": "kg"}, {"v": 7, "u": "kg"}], "tags": ["a", "b"]},
    {"id": 2, "obs": [{"v": 9, "u": "cm"}], "tags": []},
    {"id": 3, "obs": [], "tags": ["c"]},
]


# --- with a spec ---------------------------------------------------------------------------


def test_spec_gives_exactly_the_spec_columns_in_order(patient) -> None:
    frame = to_frame(PATIENTS + [patient], SPEC)
    assert frame.columns.tolist() == ["id", "family", "gender", "deceased"]
    assert frame.shape == (4, 4)
    assert frame["id"].tolist() == ["p1", "p2", "p3", "example-1"]
    assert frame["family"].tolist()[:2] == ["Rivera", "Ortiz"]
    assert frame.loc[2, "gender"] == "unknown"  # the entry's own default
    assert frame.loc[1, "deceased"] == "2001-01-01"


def test_spec_absent_elements_are_empty_cells_on_pandas_2_and_3() -> None:
    frame = to_frame(PATIENTS, SPEC)
    assert pd.isna(frame.loc[2, "family"])
    assert frame["deceased"].isna().tolist() == [True, False, True]
    assert frame["deceased"].notna().sum() == 1
    all_missing = to_frame([{}, {}], SPEC)
    assert all_missing.shape == (2, 4)
    assert all_missing["family"].isna().all()
    assert all_missing["gender"].tolist() == ["unknown", "unknown"]


def test_spec_with_zero_records_keeps_the_columns() -> None:
    empty = to_frame([], SPEC)
    assert empty.columns.tolist() == ["id", "family", "gender", "deceased"]
    assert empty.shape == (0, 4)
    assert len(empty) == 0
    assert to_frame(iter(()), SPEC).columns.tolist() == ["id", "family", "gender", "deceased"]


def test_spec_kwargs_go_to_select_fields() -> None:
    frame = to_frame(PATIENTS, SPEC, missing="?")
    assert frame.loc[2, "family"] == "?"
    assert frame.loc[2, "gender"] == "unknown"  # an entry default beats missing
    with pytest.raises(TypeError, match="explode"):
        to_frame(PATIENTS, SPEC, explode=("name",))  # a flatten_rows option, not a spec option


def test_spec_is_validated_even_for_zero_records() -> None:
    with pytest.raises(TypeError, match="must be a tuple"):
        to_frame([], [("id", "id")])
    with pytest.raises(ValueError, match="appears twice"):
        to_frame([], [("id", ("id",)), ("id", ("gender",))])


# --- without a spec ------------------------------------------------------------------------


def test_no_spec_is_a_frame_of_flatten_rows() -> None:
    frame = to_frame(RECORDS)
    expected = pd.DataFrame(flatten_rows(RECORDS))
    pd.testing.assert_frame_equal(frame, expected)
    assert frame.columns.tolist() == [
        "id",
        "obs_0_v",
        "obs_0_u",
        "obs_1_v",
        "obs_1_u",
        "tags_0",
        "tags_1",
        "tags",
        "obs",
    ]  # first appearance across the rows: record 2's "tags": [] and record 3's "obs": [] last
    assert frame.shape == (3, 9)


def test_no_spec_ragged_rows_give_nan_cells() -> None:
    frame = to_frame([{"a": 1, "b": 2}, {"a": 3}])
    assert frame.shape == (2, 2)
    assert pd.isna(frame.loc[1, "b"])
    assert frame["a"].tolist() == [1, 3]


def test_no_spec_zero_records_give_an_empty_frame_without_columns() -> None:
    empty = to_frame([])
    assert empty.shape == (0, 0)
    assert to_frame([], explode=("obs",)).shape == (0, 0)


def test_no_spec_kwargs_go_to_flatten_rows() -> None:
    exploded = to_frame(RECORDS, explode=("obs",), lists="keep")
    assert exploded.columns.tolist() == ["id", "obs_v", "obs_u", "tags"]
    assert exploded["id"].tolist() == [1, 1, 2]
    assert exploded["obs_v"].tolist() == [5, 7, 9]
    assert exploded.loc[2, "tags"] == []
    kept = to_frame(RECORDS, explode=("obs",), keep_empty=True, lists="keep")
    assert kept["id"].tolist() == [1, 1, 2, 3]
    assert pd.isna(kept.loc[3, "obs_v"])
    with pytest.raises(TypeError, match="sep must be a str"):
        to_frame(RECORDS, sep=None)


def test_no_spec_collapse_single_reproduces_the_metrics_shape() -> None:
    # the shape of answer 75196824 with invented numbers: one row per metric, columns from the
    # nested "result" dict with its only level dropped
    metrics = [
        {"metric": "corr", "result": {"cur": {"p": 0.1, "q": None}, "ref": {"p": 0.7}}},
        {"metric": "drift", "result": {"cur": {"p": 0.2, "q": 0.3}, "ref": {"p": 0.4}}},
    ]
    frame = to_frame(metrics, collapse_single=True)
    assert frame.columns.tolist() == ["metric", "cur_p", "cur_q", "ref_p"]
    assert frame["metric"].tolist() == ["corr", "drift"]
    assert pd.isna(frame.loc[0, "cur_q"]) and frame.loc[1, "cur_q"] == 0.3


# --- edge ----------------------------------------------------------------------------------


def test_records_may_be_any_iterable_consumed_once() -> None:
    frame = to_frame((record for record in PATIENTS), SPEC)
    assert frame.shape == (3, 4)
    assert to_frame(record for record in RECORDS).shape == (3, 9)


def test_missing_pandas_raises_a_helpful_import_error(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pandas", None)  # makes "import pandas" fail
    with pytest.raises(ImportError, match=r"nestpath\[pandas\]"):
        to_frame(PATIENTS, SPEC)
