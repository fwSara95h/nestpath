"""A spec of key paths, with defaults, applied to each scraped record (answer 75205202).

The asker was scraping records into dicts and kept a ``filters`` list of ``(name, key)`` pairs to
read from each one, but one field sat two keys deep and ``person[i[1]]`` cannot follow a list of
keys. My answer put the ``try``/``except`` inside a loop over the keys (``getNestedVal``), let an
entry carry a default as its third item, and built each result with a dict comprehension over the
filters; ``select_fields`` is that loop with the paths written as tuples. One difference: the
answer accepted a single key as a bare string and wrapped it in a list, while ``select_fields``
raises ``TypeError`` on a bare string rather than guess what it means.

Question, my answer and the other answers, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/75197965-applying-keys-sequentially-to-a-dict-from-a-list
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75205202.py
"""

from __future__ import annotations

from typing import Any

from nestpath import select_fields

PEOPLE = [
    {"name0": {"first0": "Ana", "last0": "Ruiz"}, "age0": "34", "location0": {"city0": "Porto"}},
    {"name0": {"first0": "Ben"}, "location0": {"city0": "Lyon"}},  # no age
    {"name0": "unknown", "age0": "51"},  # name scraped as plain text; no location
]

SPEC = [
    ("name", ("name0", "first0")),
    ("age", ("age0",)),
    ("city", ("location0", "city0"), "n/a"),  # a default for this field only
]


def with_nestpath(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per record, the spec's names as keys, ``None`` or the entry's default on a miss."""
    return [select_fields(person, SPEC) for person in people]


def without_nestpath(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The same with the answer's ``getNestedVal`` and ``filters``, rewritten in today's style."""

    def get_nested_val(obj: Any, key_path: Any, default: Any = None) -> Any:
        if isinstance(key_path, str) or not hasattr(key_path, "__iter__"):
            key_path = [key_path]  # a single key
        for key in key_path:
            try:
                obj = obj[key]
            except (KeyError, IndexError, TypeError):
                return default
        return obj

    filters = [
        ("name", ["name0", "first0"]),
        ("age", "age0"),
        ("city", ["location0", "city0"], "n/a"),
    ]
    return [{f[0]: get_nested_val(person, *f[1:3]) for f in filters} for person in people]


def main() -> None:
    """Print the rows; check the plain version agrees; show the bare-string path being refused."""
    rows = with_nestpath(PEOPLE)
    for row in rows:
        print(row)
    assert rows == without_nestpath(PEOPLE)
    try:
        select_fields(PEOPLE[0], [("age", "age0")])
    except TypeError as error:
        print(f"\na bare string as a path: TypeError: {error}")


if __name__ == "__main__":
    main()
