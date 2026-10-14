"""Rows grouped by one nested field and then another (answer 75928321).

The asker had rows as dicts (and as lists under a header row) and wanted them grouped as
``{outer: {inner: [rows]}}`` by two of their fields, for an assignment that ruled out imports. My
answer filled the nested dict with ``setdefault`` in one loop, reading the two fields with
``r.get(k)``; for flat rows that is the whole solution and ``nestpath`` adds nothing. With the
grouping fields nested inside the rows, ``getter`` supplies the keys and the loop stays the
answer's, and the same getters serve as ``key=`` for ``sorted`` and ``itertools.groupby``.

Question and my answer, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75927144-how-to-group-the-same-values-into-same-key
The data below is invented, with the grouping fields nested where the question's were flat; none of
it is the asker's.

    python examples/from_answers/75928321.py
"""

from __future__ import annotations

from itertools import groupby
from typing import Any

from nestpath import getter

VISITS = [
    {"id": 1, "when": {"year": 2024}, "site": {"code": "A"}},
    {"id": 2, "when": {"year": 2024}, "site": {"code": "B"}},
    {"id": 3, "when": {"year": 2023}, "site": {"code": "A"}},
    {"id": 4, "when": {"year": 2024}, "site": {"code": "A"}},
    {"id": 5, "when": {"year": 2023}},  # no site recorded
]

year = getter("when", "year")
site = getter("site", "code", default="unknown")

Grouped = dict[Any, dict[Any, list[dict[str, Any]]]]


def with_nestpath(visits: list[dict[str, Any]]) -> Grouped:
    """The answer's ``setdefault`` loop, with getters for the two nested fields."""
    grouped: Grouped = {}
    for visit in visits:
        grouped.setdefault(year(visit), {}).setdefault(site(visit), []).append(visit)
    return grouped


def without_nestpath(visits: list[dict[str, Any]]) -> Grouped:
    """The same loop reading the nested fields with chained ``.get``."""
    grouped: Grouped = {}
    for visit in visits:
        outer = visit.get("when", {}).get("year")
        inner = visit.get("site", {}).get("code", "unknown")
        grouped.setdefault(outer, {}).setdefault(inner, []).append(visit)
    return grouped


def ids(grouped: Grouped) -> dict[Any, dict[Any, list[int]]]:
    """The grouping with each row shown by its id."""
    return {
        outer: {inner: [row["id"] for row in rows] for inner, rows in inners.items()}
        for outer, inners in grouped.items()
    }


def main() -> None:
    """Print the grouping; check the plain version agrees; group by year with ``groupby``."""
    grouped = with_nestpath(VISITS)
    assert grouped == without_nestpath(VISITS)
    print("by year, then site:", ids(grouped))
    in_year_order = sorted(VISITS, key=year)  # groupby needs its input sorted by the same key
    by_year = {y: [v["id"] for v in rows] for y, rows in groupby(in_year_order, key=year)}
    print("by year, with itertools.groupby:", by_year)


if __name__ == "__main__":
    main()
