"""Optional nested fields read with a default (answer 75466591).

The asker's JSON records had optional fields that could hold dicts, and
``record.get("optional").get("value1")`` raised ``AttributeError`` whenever the field was absent.
Chaining ``.get(key, {})`` fixes that until a field is present but is not a dict. My answer turned
the walk into a function with a default (``getVal``, a ``try``/``except`` loop over the keys) and a
getter factory (``valGetter``); ``nestpath.get`` and ``nestpath.getter`` are those two, ported, and
an index into a list is one more step of the path.

Question, my answer and the other answers, archived with attribution:
https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/70988817-dealing-with-optional-python-dictionary-fields
The data below is invented in the question's shape; none of it is the asker's.

    python examples/from_answers/75466591.py
"""

from __future__ import annotations

from typing import Any

from nestpath import getter

ORDERS = [
    {"id": "o1", "shipping": {"carrier": "post", "events": [{"status": "sent"}]}},
    {"id": "o2"},  # no shipping at all
    {"id": "o3", "shipping": "pickup"},  # present, but a string rather than a dict
    {"id": "o4", "shipping": {"carrier": "courier", "events": []}},  # no events yet
]

carrier = getter("shipping", "carrier", default="none")
first_status = getter("shipping", "events", 0, "status", default="no events")


def with_nestpath(orders: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Each order's id, carrier and first shipping event, with a default for every miss."""
    return [(order["id"], carrier(order), first_status(order)) for order in orders]


def without_nestpath(orders: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """The same with the answer's ``try``/``except`` loop, rewritten in today's style."""

    def get_val(obj: Any, *keys: Any, default: Any = None) -> Any:
        try:
            for key in keys:
                obj = obj[key]
        except (KeyError, IndexError, TypeError):
            return default
        return obj

    return [
        (
            order["id"],
            get_val(order, "shipping", "carrier", default="none"),
            get_val(order, "shipping", "events", 0, "status", default="no events"),
        )
        for order in orders
    ]


def main() -> None:
    """Print each order's fields; check the plain version agrees; show where the chain breaks."""
    rows = with_nestpath(ORDERS)
    for row in rows:
        print(*row, sep="\t")
    assert rows == without_nestpath(ORDERS)
    try:
        [order.get("shipping", {}).get("carrier", "none") for order in ORDERS]
    except AttributeError as error:
        print(f"\nthe question's chained .get(key, {{}}) on o3: AttributeError: {error}")


if __name__ == "__main__":
    main()
