"""Field selection: :func:`select_fields` applies a ``(name, path[, default])`` spec to an object.

Source: the ``filters`` idiom in answer 75205202 on question 75197965 (chapter A1 of
stackoverflow-driftr), made explicit; path access as in :mod:`nestpath.paths`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nestpath.paths import Path, get

FieldSpec = tuple[str, Path] | tuple[str, Path, Any]
"""One output field: ``(name, path)`` or ``(name, path, default)``."""


def select_fields(obj: Any, spec: Sequence[FieldSpec], *, missing: Any = None) -> dict[str, Any]:
    """Return ``{name: value}`` for every ``spec`` entry, each value read with :func:`nestpath.get`.

    ``spec`` is a sequence of ``(name, path)`` or ``(name, path, default)`` entries, the path a
    tuple of keys and indices — the one canonical form; a string or list where the path should be
    raises ``TypeError`` rather than being read one character or element at a time. An entry's own
    default is used when its path misses; entries without one fall back to ``missing``. The result
    keeps the spec's order, so it is a row with a fixed set of columns; a name that appears twice
    raises ``ValueError``. A spec is data: build it once, apply it to every record.

    >>> patient = {"id": "p1", "name": [{"family": "Rivera", "given": ["Ana"]}]}
    >>> spec = [
    ...     ("id", ("id",)),
    ...     ("family", ("name", 0, "family")),
    ...     ("given", ("name", 0, "given", 0)),
    ...     ("gender", ("gender",), "unknown"),
    ... ]
    >>> select_fields(patient, spec)
    {'id': 'p1', 'family': 'Rivera', 'given': 'Ana', 'gender': 'unknown'}
    >>> select_fields({}, spec, missing="")
    {'id': '', 'family': '', 'given': '', 'gender': 'unknown'}

    Source: answer 75205202, where ``filters = [("age", "age0"), ("name", ["name0", "first0"]),
    ("gender", ["gender0"], "N/A")]`` is applied as ``{k[0]: getNestedVal(person, *k[1:3]) ...}``.
    """
    row: dict[str, Any] = {}
    for entry in spec:
        if len(entry) == 2:
            (name, path), default = entry, missing
        elif len(entry) == 3:
            name, path, default = entry
        else:
            raise ValueError(f"spec entry {entry!r} must be (name, path) or (name, path, default)")
        if not isinstance(path, tuple):
            raise TypeError(f"path for {name!r} must be a tuple, got {type(path).__name__}")
        if name in row:
            raise ValueError(f"field {name!r} appears twice in the spec")
        row[name] = get(obj, *path, default=default)
    return row
