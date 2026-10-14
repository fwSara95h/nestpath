"""A column of JSON text in a CSV turned into columns, chosen or all (answer 75590907).

The asker had a CSV with a column of JSON (a diff of an API description) and wanted its nested
parameters as columns of their own. My answer took the column as parsed (``json.loads`` first if
it is text) and offered two ways: map a ``try_get`` over a list of key paths to add the columns
wanted, each named after its path, or flatten every dict and put the result beside the original
column, keeping lists as values (its ``flattenDict`` also unwrapped one-element lists, which
``nestpath`` does not). ``to_frame`` with a spec is the first way in one call (``try_get`` is
``nestpath.get``); for the second, ``pandas.json_normalize`` gives the identical frame, so there
the plain version is just as good.

Question and my answer, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75569289-flatten-and-extract-keywords-from-json-field-in-csv
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75590907.py
"""

from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from nestpath import to_frame

DIFFS = [  # what the JSON column holds, row by row
    {
        "info": {"version": {"from": "1.0.0", "to": "1.1.0"}},
        "endpoints": {"added": [{"method": "GET", "path": "/items"}]},
        "components": {"schemas": {"added": ["Item", "ItemList"]}},
    },
    {
        "info": {"version": {"from": "1.1.0", "to": "2.0.0"}},
        "endpoints": {"added": [{"method": "POST", "path": "/items"}]},
        "components": {"schemas": {"added": ["NewItem"]}, "requestBodies": {"added": ["NewItem"]}},
    },
]
CSV_TEXT = pd.DataFrame(
    {"release": ["r1", "r2"], "diff": [json.dumps(diff) for diff in DIFFS]}
).to_csv(index=False)  # a CSV like the asker's: one column of JSON text

WANTED = [
    ("info", "version", "to"),
    ("endpoints", "added"),
    ("components", "requestBodies", "added"),  # absent from the first row
]
SPEC = [(".".join(path), path) for path in WANTED]  # each column named after its path


def with_nestpath(diffs: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The chosen paths as columns, and every path as a column with lists kept as values."""
    return to_frame(diffs, SPEC), to_frame(diffs, sep=".", lists="keep")


def without_nestpath(diffs: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The answer's ``try_get`` over the key paths, rewritten; and ``pandas.json_normalize``."""

    def try_get(obj: Any, *keys: Any, default: Any = None) -> Any:
        try:
            for key in keys:
                obj = obj[key]
        except (KeyError, IndexError, TypeError):
            return default
        return obj

    chosen = pd.DataFrame({name: [try_get(diff, *path) for diff in diffs] for name, path in SPEC})
    return chosen, pd.json_normalize(diffs.tolist(), sep=".")


def main() -> None:
    """Read the CSV, parse the JSON column, print both results; check the plain ones agree."""
    frame = pd.read_csv(io.StringIO(CSV_TEXT))
    diffs = frame["diff"].map(json.loads)
    chosen, flat = with_nestpath(diffs)
    print("chosen paths, beside the release:")
    print(pd.concat([frame[["release"]], chosen], axis=1).to_string())
    print("\nevery path, lists kept as values:")
    print(f"  {flat.columns.tolist()}")
    plain_chosen, plain_flat = without_nestpath(diffs)
    pd.testing.assert_frame_equal(chosen, plain_chosen)
    pd.testing.assert_frame_equal(flat, plain_flat)


if __name__ == "__main__":
    main()
