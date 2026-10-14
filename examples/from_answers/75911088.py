"""A list of dicts sorted by one nested key, ties broken by the next (answer 75911088).

The asker had dicts that shared the same keys and wanted them sorted by the first key, ties broken
by the next. My answer used ``sorted`` with ``key=lambda d: [d.get(k) for k in keysList]``, which
reads the sort keys from a list. With the keys one level down the plain version below is just as
short; ``getter`` is the same key function for a path of any depth. Either way a record that lacks
a key needs a default: without one, ``None`` meets a number and ``sorted`` raises ``TypeError``, as
``main`` shows.

Question, my answer and the other answer, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75907811-sort-a-list-that-contains-dictionaries-with-same-key
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75911088.py
"""

from __future__ import annotations

from typing import Any

from nestpath import getter

RUNS = [
    {"id": "r1", "result": {"score": 80, "time": 12.5}},
    {"id": "r2", "result": {"score": 95, "time": 11.0}},
    {"id": "r3", "result": {"score": 80, "time": 9.8}},
    {"id": "r4", "result": {"score": 95}},  # no time recorded
    {"id": "r5"},  # never scored
]

LAST = float("inf")
SORT_BY = [("score", LAST), ("time", LAST)]  # keys under "result"; a missing one sorts last


def with_nestpath(runs: list[dict[str, Any]]) -> list[str]:
    """The run ids sorted by score, then time, with a getter per sort key."""
    keys = [getter("result", name, default=default) for name, default in SORT_BY]
    return [run["id"] for run in sorted(runs, key=lambda run: [key(run) for key in keys])]


def without_nestpath(runs: list[dict[str, Any]]) -> list[str]:
    """The same with the answer's list-of-keys ``lambda``, one level down and with defaults."""

    def sort_key(run: dict[str, Any]) -> list[Any]:
        return [run.get("result", {}).get(name, default) for name, default in SORT_BY]

    return [run["id"] for run in sorted(runs, key=sort_key)]


def main() -> None:
    """Print the order; check the plain version agrees; show what happens without defaults."""
    order = with_nestpath(RUNS)
    print("sorted by score, then time:", order)
    assert order == without_nestpath(RUNS)
    try:
        sorted(RUNS, key=lambda run: [run.get("result", {}).get(name) for name, _ in SORT_BY])
    except TypeError as error:
        print(f"the same keys without defaults: TypeError: {error}")


if __name__ == "__main__":
    main()
