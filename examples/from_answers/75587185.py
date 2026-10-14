"""JSON records with uneven nested fields written as CSV, one column per field (answer 75587185).

The asker had a JSON file of records holding a nested dict and a list of single-key dicts, with
fields missing from some records, and wanted a CSV whose header has every field and an empty cell
wherever a record lacks one. My answer flattened each record with ``flattenObj``, joining keys
with ``" > "``, and let pandas take the union of the keys; ``to_frame(records, sep=" > ")`` gives
the same columns. Both key the list by position, so a field found at different positions in
different records lands in two columns (the README's note says more), while
``pandas.json_normalize`` leaves the list as one column of lists, which is why the answer used its
own flattener. Merging each record's list into one dict first gives one column per field, and from
there ``json_normalize`` flattens the rest just as well; where positions in a list do matter,
``to_frame`` keeps them as columns and ``json_normalize`` cannot.

Question, my answer and the other answers, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75586203-how-to-convert-json-file-to-csv-file-in-python
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75587185.py
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from nestpath import to_frame

EVENTS = json.loads(
    """
    [
      {"details": [{"city": "Leeds"}, {"date": "2025-09-01"}, {"seats": "12 left"}],
       "contact email": "events@example.test",
       "organiser": {"name": "R. Vega", "role": "host", "email": "rvega@example.test"}},
      {"details": [{"seats": "3 left"}],
       "contact email": "",
       "sign-up link": "https://example.test/sign-up",
       "organiser": {"name": "S. Kim", "role": "host", "email": "skim@example.test"}}
    ]
    """
)


def merge_details(event: dict[str, Any]) -> dict[str, Any]:
    """A copy of the record with its ``details`` list merged into one dict (no key repeats)."""
    merged = {key: value for item in event.get("details", []) for key, value in item.items()}
    return {**event, "details": merged}


def with_nestpath(events: list[dict[str, Any]]) -> pd.DataFrame:
    """One row per record and one column per field, the list merged first."""
    return to_frame([merge_details(event) for event in events], sep=" > ")


def without_nestpath(events: list[dict[str, Any]]) -> pd.DataFrame:
    """The same with ``pandas.json_normalize`` once the list is merged."""
    return pd.json_normalize([merge_details(event) for event in events], sep=" > ")


def main() -> None:
    """Show the columns keyed by position and by json_normalize alone; print the merged CSV."""
    print("keyed by position, as the answer's flattenObj did:")
    print(f"  {to_frame(EVENTS, sep=' > ').columns.tolist()}")
    print("pandas.json_normalize alone, the list left as one column:")
    print(f"  {pd.json_normalize(EVENTS, sep=' > ').columns.tolist()}")
    frame = with_nestpath(EVENTS)
    print("the list merged first, one column per field:")
    print(frame.to_csv(index=False), end="")  # to_csv(path, index=False) writes the file instead
    plain = without_nestpath(EVENTS)
    pd.testing.assert_frame_equal(frame, plain[frame.columns])  # same cells; its own column order


if __name__ == "__main__":
    main()
