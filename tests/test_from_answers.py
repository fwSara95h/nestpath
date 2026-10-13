"""Tests derived from the archived answers (plan-A step 5).

Each test takes the situation of one of my 2022-2023 Stack Overflow answers — the kind of nested
data the asker had and the result they wanted — and solves it with ``nestpath``. Every fixture is
invented from scratch in an equivalent shape; none copies an asker's data. The docstring of each
test names the answer and links its folder in the archive repository, where the question, my
answer and the other answers are kept with their attribution:
https://github.com/fwSara95h/stackoverflow-driftr. Tests that end in a DataFrame skip when pandas
is not installed; the rest need only the core.
"""

from __future__ import annotations

import csv
from itertools import groupby

import pytest

from nestpath import flatten, flatten_rows, get, getter, paths, select_fields, to_frame


def test_optional_fields_read_with_a_default_75466591() -> None:
    """Answer 75466591: a nested field that is sometimes absent, read without ``AttributeError``.

    The asker chained ``.get("optional").get("value1")`` and got ``AttributeError`` whenever the
    outer field was missing; ``get`` with a default walks the whole path and gives the default on
    any miss, including an outer value that is not a dict at all.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/70988817-dealing-with-optional-python-dictionary-fields
    """
    with_shipping = {"customer": {"name": "Ana"}, "shipping": {"carrier": "post", "days": 3}}
    without = {"customer": {"name": "Ben"}}
    odd = {"customer": {"name": "Cy"}, "shipping": "pickup"}  # present, but not a dict

    assert get(with_shipping, "shipping", "carrier", default="pickup") == "post"
    assert get(without, "shipping", "carrier", default="pickup") == "pickup"
    assert get(odd, "shipping", "carrier", default="pickup") == "pickup"  # not a TypeError
    assert get(without, "shipping", "carrier") is None

    carrier = getter("shipping", "carrier", default="pickup")  # the valGetter form
    assert [carrier(order) for order in (with_shipping, without, odd)] == [
        "post",
        "pickup",
        "pickup",
    ]


def test_keys_applied_sequentially_from_a_spec_75205202() -> None:
    """Answer 75205202: a list of ``(name, keys[, default])`` applied to each scraped record.

    The asker had ``filters = [("age", "age0"), ("name", ["name0", "first0"])]`` and could not
    follow two keys in one loop; ``select_fields`` is that loop with tuple paths and per-field
    defaults, and the same spec applies to every record.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/75197965-applying-keys-sequentially-to-a-dict-from-a-list
    """
    listing = {
        "title": {"text": "Copper kettle", "lang": "en"},
        "price": {"amount": 25, "currency": "EUR"},
        "seller": {"name": {"first": "Mara", "last": "Ortiz"}},
    }
    spec = [
        ("title", ("title", "text")),
        ("price", ("price", "amount")),
        ("seller", ("seller", "name", "first")),
        ("colour", ("attributes", "colour"), "n/a"),  # a field this listing does not have
    ]
    assert select_fields(listing, spec) == {
        "title": "Copper kettle",
        "price": 25,
        "seller": "Mara",
        "colour": "n/a",
    }
    bare = {"title": {"text": "Spoon"}}
    assert select_fields(bare, spec) == {
        "title": "Spoon",
        "price": None,
        "seller": None,
        "colour": "n/a",
    }


def test_flatten_a_tree_into_its_values_75934500() -> None:
    """Answer 75934500: every leaf of an arbitrarily nested list/dict tree, in order, as a list.

    The asker had a list of dicts whose values were lists of strings and more dicts and wanted
    the strings in one flat list. ``flatten`` keeps the keys as well; its values in order are
    what the answer's recursive generator yielded.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A2-flattening-and-walking-nested-structures/75934227-how-to-flatten-list-of-dictionaries
    """
    chapters = [
        {
            "intro": [
                {"welcome": ["hello", "who this is for"]},
                "how to read",
                {"setup": [{"install": ["pip", "from source"]}]},
            ]
        },
        {"usage": ["run it"]},
    ]
    assert list(flatten(chapters).values()) == [
        "hello",
        "who this is for",
        "how to read",
        "pip",
        "from source",
        "run it",
    ]
    by_chapter = {
        key: list(flatten(value).values()) for part in chapters for key, value in part.items()
    }
    assert by_chapter == {
        "intro": ["hello", "who this is for", "how to read", "pip", "from source"],
        "usage": ["run it"],
    }
    assert [get(chapters, *path) for path in paths(chapters)] == list(flatten(chapters).values())


def test_nested_metrics_to_one_row_each_75196824() -> None:
    """Answer 75196824: a list of metric results, each a dict nested four deep, as a DataFrame.

    The asker's ``result`` held ``current`` and ``reference`` blocks, each with a ``stats`` level
    and two groups of statistics, and wanted one row per metric with columns like
    ``cur_pearson_target_prediction_correlation``. ``collapse_single`` drops the levels that hold a
    single dict (``result``, ``stats``), as the answer's ``flattenDict`` did; the answer's
    ``rename`` is a rename of the columns afterwards.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75184221-convert-nested-dict-to-dataframe-syntax-error
    """
    pd = pytest.importorskip("pandas")

    def block(a: float | None, b: float | None) -> dict:
        return {"stats": {"spread": {"mean": a, "max": b}, "shift": {"mean": None, "max": b}}}

    metrics = [
        {
            "name": "ColumnDrift",
            "result": {"current": block(0.1, 0.4), "reference": block(0.2, 0.5)},
        },
        {"name": "RowCount", "result": {"current": block(None, 1.0), "reference": block(0.3, 1.0)}},
    ]
    frame = to_frame(metrics, collapse_single=True).rename(
        columns=lambda name: name.replace("current_", "cur_").replace("reference_", "ref_")
    )
    assert frame.columns.tolist() == [
        "name",
        "cur_spread_mean",
        "cur_spread_max",
        "cur_shift_mean",
        "cur_shift_max",
        "ref_spread_mean",
        "ref_spread_max",
        "ref_shift_mean",
        "ref_shift_max",
    ]
    assert frame.shape == (2, 9)
    assert frame.loc[0, "cur_spread_max"] == 0.4
    assert pd.isna(frame.loc[1, "cur_spread_mean"]) and frame.loc[1, "ref_spread_mean"] == 0.3
    without_name = to_frame([m["result"] for m in metrics], collapse_single=True)  # the drop
    assert without_name.shape == (2, 8)


def test_sort_a_list_of_dicts_by_shared_keys_75911088() -> None:
    """Answer 75911088: sort dicts by one key, ties broken by the next.

    The answer used ``key=lambda d: [d.get(k) for k in keysList]``; ``getter`` is that for a
    nested path with a default, and a tuple of getters sorts by several.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75907811-sort-a-list-that-contains-dictionaries-with-same-key
    """
    runs = [
        {"id": "r1", "result": {"score": 80, "time": 12.5}},
        {"id": "r2", "result": {"score": 95, "time": 11.0}},
        {"id": "r3", "result": {"score": 80, "time": 9.8}},
        {"id": "r4"},  # never scored
    ]
    by_score = sorted(runs, key=getter("result", "score", default=-1), reverse=True)
    assert [run["id"] for run in by_score] == ["r2", "r1", "r3", "r4"]

    keys = [getter("result", "score", default=-1), getter("result", "time", default=float("inf"))]
    by_score_then_time = sorted(runs, key=lambda run: tuple(key(run) for key in keys))
    assert [run["id"] for run in by_score_then_time] == ["r4", "r3", "r1", "r2"]
    assert max(runs, key=getter("result", "score", default=-1))["id"] == "r2"


def test_group_rows_under_nested_keys_75928321() -> None:
    """Answer 75928321: rows grouped into ``{outer: {inner: [rows]}}`` by two of their fields.

    The answer filled the nested dict with ``setdefault``; with the grouping fields nested inside
    the rows, ``getter`` supplies the keys — to the same loop, or to ``itertools.groupby``.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75927144-how-to-group-the-same-values-into-same-key
    """
    visits = [
        {"id": 1, "when": {"year": 2024}, "site": {"code": "A"}},
        {"id": 2, "when": {"year": 2024}, "site": {"code": "B"}},
        {"id": 3, "when": {"year": 2023}, "site": {"code": "A"}},
        {"id": 4, "when": {"year": 2024}, "site": {"code": "A"}},
    ]
    year, site = getter("when", "year"), getter("site", "code")

    grouped: dict[int, dict[str, list[dict]]] = {}
    for visit in visits:
        grouped.setdefault(year(visit), {}).setdefault(site(visit), []).append(visit)
    assert {
        y: {s: [v["id"] for v in rows] for s, rows in inner.items()} for y, inner in grouped.items()
    } == {
        2024: {"A": [1, 4], "B": [2]},
        2023: {"A": [3]},
    }

    by_year = {
        y: [v["id"] for v in rows] for y, rows in groupby(sorted(visits, key=year), key=year)
    }
    assert by_year == {2023: [3], 2024: [1, 2, 4]}


def test_json_records_with_uneven_fields_to_csv_75587185(tmp_path) -> None:
    """Answer 75587185: JSON records with nested dicts, fields missing from some, written as CSV.

    The asker wanted a header with every field that appears anywhere and empty cells where a record
    lacks one; the answer flattened each record with ``" > "`` as the separator and let pandas take
    the union of the keys. ``to_frame`` without a spec does the same.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75586203-how-to-convert-json-file-to-csv-file-in-python
    """
    pd = pytest.importorskip("pandas")
    postings = [
        {
            "details": [{"city": "Leeds"}, {"start": "2025-09-01"}],
            "contact": {"name": "R. Vega", "role": "lead"},
            "apply": "jobs@example.test",
        },
        {
            "details": [{"start": "2025-10-01"}],
            "contact": {"name": "S. Kim", "role": "lead", "phone": "000"},
            "link": "https://example.test/apply",
        },
    ]
    frame = to_frame(postings, sep=" > ")
    assert frame.columns.tolist() == [
        "details > 0 > city",
        "details > 1 > start",
        "contact > name",
        "contact > role",
        "apply",
        "details > 0 > start",
        "contact > phone",
        "link",
    ]
    assert pd.isna(frame.loc[1, "details > 0 > city"]) and pd.isna(frame.loc[0, "link"])

    path = tmp_path / "postings.csv"
    frame.to_csv(path, index=False)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["contact > name"] == "R. Vega" and rows[0]["link"] == ""
    assert rows[1]["details > 0 > start"] == "2025-10-01" and rows[1]["apply"] == ""


def test_dict_column_to_chosen_and_flattened_columns_75590907() -> None:
    """Answer 75590907: a DataFrame column of nested dicts, as specific columns or flattened.

    Two ways from the answer: ``map`` a per-path getter for the few paths wanted, or flatten
    every dict and put the result beside the original column; lists stay values as the answer's
    ``flattenDict`` left them.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75569289-flatten-and-extract-keywords-from-json-field-in-csv
    """
    pd = pytest.importorskip("pandas")
    changes = pd.DataFrame(
        {
            "change": [
                {
                    "version": {"from": "1.0", "to": "1.1"},
                    "paths": {"added": ["/a"], "removed": []},
                },
                {
                    "version": {"from": "1.1", "to": "2.0"},
                    "paths": {"added": ["/b", "/c"], "removed": ["/a"]},
                },
            ]
        }
    )
    wanted = [("version", "to"), ("paths", "added")]
    for path in wanted:
        changes[".".join(path)] = changes["change"].map(getter(*path))
    assert changes["version.to"].tolist() == ["1.1", "2.0"]
    assert changes["paths.added"].tolist() == [["/a"], ["/b", "/c"]]

    flat = to_frame(changes["change"], sep=".", lists="keep")
    assert flat.columns.tolist() == ["version.from", "version.to", "paths.added", "paths.removed"]
    side_by_side = pd.concat([changes[["change"]], flat], axis=1)
    assert side_by_side.shape == (2, 5)
    assert side_by_side.loc[1, "paths.removed"] == ["/a"]


def test_unnest_a_list_column_into_rows_75808253() -> None:
    """Answer 75808253: a column holding a list of dicts per row, one row per element.

    The asker's lists were stringified (``ast.literal_eval`` first); the answer then used
    ``pandas.json_normalize`` with a record path, which handles one such column. ``explode`` does
    it before the frame exists — and ``keep_empty`` keeps the order whose list is empty, which the
    record-path approach drops.
    Folder: https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75802736-how-to-unnest-a-list-of-json-objects-in-dataframe-column
    """
    pd = pytest.importorskip("pandas")
    orders = [
        {"order": "o1", "taxes": []},
        {"order": "o2", "taxes": [{"title": "State", "rate": 0.06, "amount": {"value": "1.20"}}]},
        {
            "order": "o3",
            "taxes": [
                {"title": "State", "rate": 0.05, "amount": {"value": "2.00"}},
                {"title": "City", "rate": 0.01, "amount": {"value": "0.40"}},
            ],
        },
    ]
    rows = flatten_rows(orders, explode=("taxes",))
    assert [(row["order"], row["taxes_title"]) for row in rows] == [
        ("o2", "State"),
        ("o3", "State"),
        ("o3", "City"),
    ]
    frame = to_frame(orders, explode=("taxes",), keep_empty=True)
    assert frame.columns.tolist() == ["order", "taxes_title", "taxes_rate", "taxes_amount_value"]
    assert frame["order"].tolist() == ["o1", "o2", "o3", "o3"]
    assert pd.isna(frame.loc[0, "taxes_title"])
    per_order = frame.groupby("order", sort=False)["taxes_rate"].sum().to_dict()
    assert per_order == pytest.approx({"o1": 0.0, "o2": 0.06, "o3": 0.06})
