"""Field selection: :func:`select_fields` applies a ``(name, path[, default])`` spec to an object.

Source: the ``filters`` idiom in answer 75205202 on question 75197965 (chapter A1 of
stackoverflow-driftr), made explicit; path access as in :mod:`nestpath.paths`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nestpath.paths import Path

FieldSpec = tuple[str, Path] | tuple[str, Path, Any]
"""One output field: ``(name, path)`` or ``(name, path, default)``."""

_NOT_IMPLEMENTED = "planned for v0.1; see the Status section of the README"


def select_fields(obj: Any, spec: Sequence[FieldSpec], *, missing: Any = None) -> dict[str, Any]:
    """Return ``{name: value}`` for every ``spec`` entry, each value read with :func:`nestpath.get`.

    An entry's own default is used when its path misses; entries without one fall back to
    ``missing``. Paths are tuples only.

    Source: answer 75205202 (the ``filters`` idiom).
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)
