"""Flattening: :func:`flatten` for one object, :func:`flatten_rows` for records.

Sources: ``recFlatten`` and ``flattenObj`` in ``legacy/pastebin_v3Fep60B.py`` (paste v3Fep60B,
2023-01-21); ``flattenDict`` in answer 75196824 on question 75184221 (chapter A5 of
stackoverflow-driftr).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Literal

from nestpath.paths import Key, Path

_NOT_IMPLEMENTED = "planned for v0.1; see the Status section of the README"


class KeyCollisionError(ValueError):
    """Two different paths flattened to the same key.

    ``{"a_b": 1, "a": {"b": 2}}`` with ``sep="_"`` would produce the key ``a_b`` twice;
    nestpath raises instead of letting one value silently overwrite the other.
    """


def flatten(
    obj: Any,
    *,
    sep: str = "_",
    lists: Literal["index", "keep"] = "index",
    collapse_single: bool = False,
) -> dict[str, Any]:
    """Return ``obj`` as a one-level dict whose keys are the paths joined with ``sep``.

    ``lists="index"`` turns list positions into key parts (``a_0_b``); ``lists="keep"`` leaves
    lists in place as values. ``collapse_single=True`` reproduces the legacy ``flattenObj``
    habit (``ignore_singles``) of dropping a level that holds a single nested container; it is
    off by default. Colliding keys raise :class:`KeyCollisionError`.

    Source: ``flattenObj`` / ``recFlatten`` (paste v3Fep60B) and ``flattenDict`` in answer 75196824.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


def flatten_rows(
    records: Iterable[Any],
    *,
    explode: Sequence[Path | Key] = (),
    keep_empty: bool = False,
    **flatten_kwargs: Any,
) -> list[dict[str, Any]]:
    """Return one flat dict per record, or per element of each exploded list.

    ``explode=("observations",)`` gives one row per element of that list, each row carrying the
    record's other fields; several explode paths give the cross product of their elements. An
    empty or missing exploded list yields no rows unless ``keep_empty=True``, which yields one
    row with ``None`` in the exploded columns. Remaining keyword arguments go to :func:`flatten`.

    Source: ``flattenObj`` (paste v3Fep60B) applied per record; the pattern of answers 75196824
    and 75934500.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)
