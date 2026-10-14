"""A tree of lists and dicts flattened to one list per top-level key (answer 75934500).

The asker, learning to traverse lists and dicts, had a list of dicts whose values mixed strings,
lists and further dicts, and wanted one flat list per top-level key, with every dict key in it
ahead of the items it holds. My answer's recursive generator yielded the values only (the README's
note says more): ``flatten`` gives those values in the same order, and
``paths(..., leaves_only=False)``, which walks the tree in pre-order, gives the list the question
asked for, keys included.

Question, my answer and the other answers, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A2-flattening-and-walking-nested-structures/75934227-how-to-flatten-list-of-dictionaries
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75934500.py
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from nestpath import flatten, get, paths

CHECKLISTS = [
    {
        "release": [
            {"build": ["compile", "package"]},
            "tag",
            {"test": ["unit", "integration"]},
            {"deploy": [{"staging": ["migrate", "smoke test"]}, "production"]},
        ]
    },
    {"rollback": ["restore backup"]},
]


def values_only(tree: Any) -> list[Any]:
    """Every leaf, in order: what the answer's generator yielded."""
    return list(flatten(tree).values())


def keys_and_values(tree: Any) -> list[Any]:
    """Every dict key ahead of what it holds, and every leaf: the list the question asked for."""
    leaves = set(paths(tree))
    items = []
    for path in paths(tree, leaves_only=False):  # pre-order: a key comes before its contents
        if isinstance(get(tree, *path[:-1]), Mapping):
            items.append(path[-1])
        if path in leaves:
            items.append(get(tree, *path))
    return items


def with_nestpath(parts: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """One list of values per top-level key."""
    return {key: values_only(tree) for part in parts for key, tree in part.items()}


def without_nestpath(parts: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """The same with the answer's recursive generator, rewritten in today's style."""

    def flatten_obj(obj: Any) -> Iterator[Any]:
        if hasattr(obj, "__iter__") and not isinstance(obj, str):
            for item in obj.values() if isinstance(obj, dict) else obj:
                yield from flatten_obj(item)
        else:
            yield obj

    return {key: list(flatten_obj(tree)) for part in parts for key, tree in part.items()}


def main() -> None:
    """Print the values as the answer gave them, then the question's lists with the keys."""
    values = with_nestpath(CHECKLISTS)
    assert values == without_nestpath(CHECKLISTS)
    print("values only, as the answer gave them:")
    for key, items in values.items():
        print(f"  {key} = {items}")
    print("keys included, as the question asked:")
    for part in CHECKLISTS:
        for key, tree in part.items():
            print(f"  {key} = {keys_and_values(tree)}")


if __name__ == "__main__":
    main()
