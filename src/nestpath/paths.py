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


def get(obj: Any, *path: Key, default: Any = None) -> Any:
    """Return the value reached by following ``path`` into ``obj``, or ``default``.

    Walks mapping keys and sequence indices in order. A missing key, an index out of range or
    a step applied to a value that has neither (``KeyError``, ``IndexError``, ``TypeError``) is
    a *miss* and yields ``default``; a string key on a list and an integer index on a dict are
    misses too, never errors.

    Source: ``getVal_byPath`` (paste NRxKRJPn) and the ``getVal`` variants in answer 75466591.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


def getter(*path: Key, default: Any = None) -> Callable[[Any], Any]:
    """Return ``lambda obj: get(obj, *path, default=default)``.

    Usable as ``key=`` for :func:`sorted`, :func:`min` and :func:`max`, and in :func:`map`.

    Source: ``valGetter`` in answer 75466591.
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)


def paths(obj: Any, *, leaves_only: bool = True) -> Iterator[Path]:
    """Yield every path in a nested structure, as tuples.

    With ``leaves_only=True`` (the default) only paths ending at a non-container value are
    yielded; with ``False`` every intermediate path is yielded as well.

    Source: ``getObjPaths`` (paste NRxKRJPn).
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)
