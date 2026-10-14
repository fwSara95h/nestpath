"""Nested metric results to one DataFrame row each (answer 75196824).

The asker had a list of metric results, each nested four levels deep, wanted one row per metric
with columns like ``cur_pearson_target_prediction_correlation``, and got ``TypeError: unhashable
type: 'dict'`` from using a result as a dict key. My answer flattened each result with a
``flattenDict`` that dropped the key of a level holding a single dict and renamed ``current`` and
``reference`` to ``cur`` and ``ref``; ``to_frame(..., collapse_single=True)`` is that flattening,
and the rename is a rename of the columns afterwards. ``pandas.json_normalize`` gives the same
frame once you name the single-dict levels to drop yourself, where ``collapse_single`` finds them
by their shape: for this data the plain version is just as good.

Question and my answer, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75184221-convert-nested-dict-to-dataframe-syntax-error
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75196824.py
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from nestpath import to_frame


def stats(day_mean: float | None, day_max: float, week_mean: float, week_max: float | None) -> dict:
    """One ``current`` or ``reference`` block: a lone ``stats`` level over two groups."""
    return {
        "stats": {
            "daily": {"mean": day_mean, "max": day_max},
            "weekly": {"mean": week_mean, "max": week_max},
        }
    }


REPORT = {
    "metrics": [
        {
            "metric": "TemperatureDrift",
            "result": {
                "current": stats(21.4, 25.0, 20.9, None),
                "reference": stats(20.1, 23.5, 20.3, 24.1),
            },
        },
        {
            "metric": "HumidityDrift",
            "result": {
                "current": stats(None, 61.0, 55.2, 64.0),
                "reference": stats(52.8, 60.5, 53.0, 62.2),
            },
        },
    ]
}

SHORT = {"current": "cur", "reference": "ref"}


def with_nestpath(report: dict[str, Any]) -> pd.DataFrame:
    """One row per metric: ``collapse_single`` drops ``result`` and ``stats``; steps renamed."""
    frame = to_frame(report["metrics"], sep=".", collapse_single=True)
    return frame.rename(columns=lambda name: "_".join(SHORT.get(s, s) for s in name.split(".")))


def without_nestpath(report: dict[str, Any]) -> pd.DataFrame:
    """The same with ``pandas.json_normalize``, the single-dict levels named by hand."""
    frame = pd.json_normalize(report["metrics"], sep=".")
    dropped = {"result", "stats"}
    return frame.rename(
        columns=lambda name: "_".join(SHORT.get(s, s) for s in name.split(".") if s not in dropped)
    )


def main() -> None:
    """Print the frame, transposed to fit; check the plain version gives the same frame."""
    frame = with_nestpath(REPORT)
    print(frame.T.to_string())
    pd.testing.assert_frame_equal(frame, without_nestpath(REPORT))


if __name__ == "__main__":
    main()
