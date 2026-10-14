"""A column holding a list of dicts per row, unnested to one row per element (answer 75808253).

The asker had a DataFrame column whose cells were lists of tax records stored as Python-literal
text, not JSON, and wanted the records unnested and joined back to the rest of the frame. My
answer parsed the cells with ``ast.literal_eval`` and unnested them with
``pandas.json_normalize`` and a record path, which, given ``meta``, carries the other columns
along. ``to_frame`` with ``explode`` gives the same rows, brings every other field of the record
without listing it, and with ``keep_empty`` keeps the order whose list is empty, which a record
path drops. The asker then asked about several nested lists; my comment said pandas cannot know
how two lists align, which is why the rows are built before the frame: ``explode`` takes several
paths, a later one pointing inside an earlier one's element.

Question and my answer, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75802736-how-to-unnest-a-list-of-json-objects-in-dataframe-column
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75808253.py
"""

from __future__ import annotations

import ast
from typing import Any

import pandas as pd

from nestpath import to_frame


def tax(title: str, rate: float, value: str) -> dict[str, Any]:
    """One tax record, nested as the question's were."""
    return {
        "title": title,
        "rate": rate,
        "amount": {"value": value, "currency": "USD"},
        "included": False,
    }


ORDERS = pd.DataFrame(
    {
        "order": ["o1", "o2", "o3"],
        "placed": ["2025-03-01", "2025-03-02", "2025-03-02"],
        "tax_lines": [  # each cell a list as Python-literal text, the way the asker's were stored
            str([]),
            str([tax("State tax", 0.06, "1.20")]),
            str([tax("State tax", 0.05, "2.00"), tax("City tax", 0.01, "0.40")]),
        ],
    }
)


def parsed(orders: pd.DataFrame) -> list[dict[str, Any]]:
    """The frame as records, each ``tax_lines`` cell parsed back into a list."""
    return orders.assign(tax_lines=orders["tax_lines"].map(ast.literal_eval)).to_dict("records")


def with_nestpath(orders: pd.DataFrame, *, keep_empty: bool = False) -> pd.DataFrame:
    """One row per tax record, the order's other fields carried along."""
    return to_frame(parsed(orders), explode=("tax_lines",), keep_empty=keep_empty)


def without_nestpath(orders: pd.DataFrame) -> pd.DataFrame:
    """The answer's ``json_normalize`` with a record path, and ``meta`` for the other columns."""
    return pd.json_normalize(
        parsed(orders),
        record_path="tax_lines",
        meta=["order", "placed"],
        record_prefix="tax_lines_",
        sep="_",
    )


def main() -> None:
    """Print the rows, the empty order kept; check the plain version gives the rest."""
    frame = with_nestpath(ORDERS, keep_empty=True)
    print(frame.to_string())
    rates = frame.groupby("order", sort=False)["tax_lines_rate"].sum().round(4)
    print("\ntax rate per order:", rates.to_dict())
    rows = with_nestpath(ORDERS)  # without keep_empty: what a record path gives
    plain = without_nestpath(ORDERS)
    pd.testing.assert_frame_equal(rows, plain[rows.columns])  # same rows; its own column order
    print("json_normalize's orders:", plain["order"].unique().tolist())


if __name__ == "__main__":
    main()
