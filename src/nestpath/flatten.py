"""Flattening: :func:`flatten` for one object, :func:`flatten_rows` for records.

Sources: ``recFlatten`` and ``flattenObj`` in ``legacy/pastebin_v3Fep60B.py`` (paste v3Fep60B,
2023-01-21); ``flattenDict`` in answer 75196824 on question 75184221 and the other ``flattenDict``
in answer 75590907 on question 75569289 (both chapter A5 of stackoverflow-driftr).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any, Literal

from nestpath.paths import Key, Path, _children

_NOT_IMPLEMENTED = "planned for v0.1; see the Status section of the README"


class KeyCollisionError(ValueError):
    """Two different paths flattened to the same key.

    ``{"a_b": 1, "a": {"b": 2}}`` with ``sep="_"`` would produce the key ``a_b`` twice;
    nestpath raises instead of letting one value silently overwrite the other. The key and the
    two paths are kept as ``key``, ``first`` and ``second``.
    """

    def __init__(self, key: str, first: Path, second: Path) -> None:
        super().__init__(f"paths {first!r} and {second!r} both flatten to key {key!r}")
        self.key = key
        self.first = first
        self.second = second


def flatten(
    obj: Any,
    *,
    sep: str = "_",
    lists: Literal["index", "keep"] = "index",
    collapse_single: bool = False,
) -> dict[str, Any]:
    """Return ``obj`` as a one-level dict: each leaf under its path, the steps joined with ``sep``.

    ``obj`` must be a mapping or a sequence (``TypeError`` otherwise). Its leaves are found by the
    rule of :func:`nestpath.paths` — mappings and sequences other than strings and bytes are walked
    into, everything else is a value, and so is an empty container — and each leaf's key is its
    path with every step turned into a string and joined with ``sep``, in depth-first container
    order. So ``flatten(obj)[sep.join(map(str, path))] is get(obj, *path)`` for every path that
    ``paths(obj)`` yields: no leaf is lost, none is invented.

    ``lists="index"`` (the default) turns list positions into key parts (``a_0_b``);
    ``lists="keep"`` leaves every sequence below the root in place as a value, nested dicts inside
    it included. The root is always walked, whatever ``lists`` says: it is the thing being
    flattened, so a root list gives ``0_a``-style keys.

    ``collapse_single=True`` reproduces the habit of the legacy ``flattenObj`` (``ignore_singles``)
    and of ``flattenDict`` in answer 75196824: at any level where exactly one child is a non-empty
    container that would be walked into, that child's step is left out of the key, so
    ``{"metric": "m", "result": {"cur": 1, "ref": 2}}`` gives ``{"metric": "m", "cur": 1,
    "ref": 2}``. It is off by default, because dropping a step is what makes two paths meet on one
    key; under ``lists="index"`` a lone list collapses to bare indices.

    Two different paths that produce the same key raise :class:`KeyCollisionError` — whether the
    separator occurs in a key (``{"a_b": 1, "a": {"b": 2}}``), two keys read the same as strings
    (``{1: ..., "1": ...}``) or ``collapse_single`` removed the step that told them apart —
    instead of one value silently overwriting the other.

    >>> patient = {"id": "p1", "name": [{"family": "Rivera", "given": ["Ana"]}], "tags": []}
    >>> flatten(patient)
    {'id': 'p1', 'name_0_family': 'Rivera', 'name_0_given_0': 'Ana', 'tags': []}
    >>> flatten(patient, lists="keep")
    {'id': 'p1', 'name': [{'family': 'Rivera', 'given': ['Ana']}], 'tags': []}
    >>> flatten({"metric": "m", "result": {"cur": 1, "ref": 2}}, sep=".", collapse_single=True)
    {'metric': 'm', 'cur': 1, 'ref': 2}
    >>> flatten({"a_b": 1, "a": {"b": 2}})
    Traceback (most recent call last):
        ...
    nestpath.flatten.KeyCollisionError: paths ('a_b',) and ('a', 'b') both flatten to key 'a_b'

    Source: ``recFlatten`` / ``flattenObj`` (paste v3Fep60B), which walked dicts and lists with
    indices as keys but dropped empty containers and let colliding keys overwrite each other;
    ``flattenDict`` in answer 75196824, whose single-dict collapse is ``collapse_single``; and
    ``flattenDict`` in answer 75590907, whose lists-as-values behaviour is ``lists="keep"``. Not
    ported: ``ignore_indices`` (indices left out of the keys: collisions by design) and ``rename``
    (rename the columns afterwards).
    """
    if not isinstance(sep, str):
        raise TypeError(f"sep must be a str, got {type(sep).__name__}")
    if lists not in ("index", "keep"):
        raise ValueError(f'lists must be "index" or "keep", got {lists!r}')
    pairs = _children(obj)
    if pairs is None:
        raise TypeError(f"flatten needs a mapping or a sequence, got {type(obj).__name__}")
    flat: dict[str, Any] = {}
    origin: dict[str, Path] = {}
    for path, steps, leaf in _leaves(pairs, (), (), lists == "keep", collapse_single):
        key = sep.join(steps)
        if key in flat:
            raise KeyCollisionError(key, origin[key], path)
        flat[key] = leaf
        origin[key] = path
    return flat


def _walks_into(obj: Any, keep_lists: bool) -> bool:
    """Whether ``obj`` is a non-empty container that :func:`flatten` walks into."""
    if keep_lists and not isinstance(obj, Mapping):
        return False
    return _children(obj) is not None and len(obj) > 0


def _leaves(
    pairs: Iterable[tuple[Key, Any]],
    path: Path,
    steps: tuple[str, ...],
    keep_lists: bool,
    collapse: bool,
) -> Iterator[tuple[Path, tuple[str, ...], Any]]:
    """Yield ``(path, key steps, leaf)`` for every leaf below ``pairs``, depth first.

    ``path`` is what :func:`nestpath.get` follows; ``steps`` is what the key is joined from, the
    same thing as strings unless ``collapse`` dropped a step.
    """
    children = [(step, child, _walks_into(child, keep_lists)) for step, child in pairs]
    collapsed = None
    if collapse:
        containers = [i for i, (_, _, walks) in enumerate(children) if walks]
        if len(containers) == 1:
            collapsed = containers[0]
    for i, (step, child, walks) in enumerate(children):
        child_path = (*path, step)
        if not walks:
            yield child_path, (*steps, str(step)), child
            continue
        child_steps = steps if i == collapsed else (*steps, str(step))
        yield from _leaves(_children(child), child_path, child_steps, keep_lists, collapse)


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
