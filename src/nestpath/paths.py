"""Path access: :func:`get`, :func:`getter` and :func:`paths`.

A *path* is a tuple of steps applied in order, each step a mapping key or a sequence index
(negative indices allowed): ``("name", 0, "family")`` reads ``obj["name"][0]["family"]``.

Sources: ``getVal_byPath`` and ``getObjPaths`` in ``legacy/pastebin_NRxKRJPn.py`` (paste
NRxKRJPn, 2022-12-04); the ``getVal`` variants and ``valGetter`` in answer 75466591 on
question 70988817 (chapter A1 of stackoverflow-driftr).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

Key = str | int
"""One step of a path: a mapping key or a sequence index."""

Path = tuple[Key, ...]
"""A path: steps applied in order."""

_NOT_IMPLEMENTED = "planned for v0.1; see the Status section of the README"

_LEAVES = (str, bytes, bytearray)
"""Subscriptable types that are values, not containers: a step into one is a miss."""


def get(obj: Any, *path: Key, default: Any = None) -> Any:
    """Return the value reached by following ``path`` into ``obj``, or ``default``.

    Each step is applied as ``obj[step]`` to whatever the previous step reached — a dict or any
    other mapping (the step is a key, whatever its type), a list, tuple or any other
    subscriptable object (the step is an index, negative allowed). A step that raises
    ``KeyError``, ``IndexError`` or ``TypeError`` is a *miss* and yields ``default``: a missing
    key, an index out of range, a string step on a list, a step into ``None`` or a number. Strings
    and bytes are values, so a step into one is a miss too, never its first character. Any other
    exception propagates. A value that is present but ``None`` is a hit, not a miss. With no
    steps ``obj`` itself is returned. Paths are given as separate arguments — ``get(obj, *path)``
    for a tuple in hand — so a tuple argument is one step with a tuple key.

    >>> patient = {"name": [{"family": "Rivera", "given": ["Ana", "Lucia"]}]}
    >>> get(patient, "name", 0, "given", -1)
    'Lucia'
    >>> get(patient, "name", 0, "prefix", 0, default="")
    ''
    >>> get(patient, "name", "family") is None  # a string step on a list is a miss
    True

    Source: ``getVal_byPath`` (paste NRxKRJPn) and the ``getVal`` variants in answer 75466591,
    which are ``try: obj = obj[k] except: default`` in a loop; the string rule is the one change.
    """
    for step in path:
        if isinstance(obj, _LEAVES):
            return default
        try:
            obj = obj[step]
        except (KeyError, IndexError, TypeError):
            return default
    return obj


def getter(*path: Key, default: Any = None) -> Callable[[Any], Any]:
    """Return a function ``obj -> get(obj, *path, default=default)``.

    Usable as ``key=`` for :func:`sorted`, :func:`min` and :func:`max`, and in :func:`map`; the
    default is fixed when the getter is made.

    >>> rows = [{"score": 3}, {"score": 1}, {}]
    >>> sorted(rows, key=getter("score", default=0))
    [{}, {'score': 1}, {'score': 3}]
    >>> list(map(getter("score"), rows))
    [3, 1, None]

    Source: ``valGetter`` in answer 75466591 (which took the default at call time instead).
    """

    def get_path(obj: Any) -> Any:
        return get(obj, *path, default=default)

    return get_path


def paths(obj: Any, *, leaves_only: bool = True) -> Iterator[Path]:
    """Yield every path in a nested structure, as tuples.

    With ``leaves_only=True`` (the default) only paths ending at a non-container value are
    yielded; with ``False`` every intermediate path is yielded as well.

    Source: ``getObjPaths`` (paste NRxKRJPn).
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)
