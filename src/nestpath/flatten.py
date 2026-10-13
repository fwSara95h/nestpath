"""Flattening: :func:`flatten` for one object, :func:`flatten_rows` for records.

Sources: ``recFlatten`` and ``flattenObj`` in ``legacy/pastebin_v3Fep60B.py`` (paste v3Fep60B,
2023-01-21); ``flattenDict`` in answer 75196824 on question 75184221 and the other ``flattenDict``
in answer 75590907 on question 75569289; the list column unnested in answer 75808253 on question
75802736 (all chapter A5 of stackoverflow-driftr).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any, Literal

from nestpath.paths import _LEAVES, Key, Path, _children, get

_MISSING = object()


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

    Each record is flattened with :func:`flatten`, which the remaining keyword arguments (``sep``,
    ``lists``, ``collapse_single``) go to. ``explode`` names lists to turn into rows: for every
    element of the list at such a path, a copy of the record in which the element takes the list's
    place is flattened, so ``{"id": 1, "obs": [{"v": 5}, {"v": 7}]}`` with ``explode=("obs",)``
    gives ``{"id": 1, "obs_v": 5}`` and ``{"id": 1, "obs_v": 7}``: the position becomes the row,
    the record's other fields repeat on each, and a list of scalars becomes a plain column. An
    entry of ``explode`` is one key (``"obs"``) or a tuple path (``("a", "obs")``); a bare string
    in place of the sequence raises ``TypeError`` rather than exploding its characters.

    Several explode paths are applied in order, each to the rows produced so far: for independent
    lists that is their cross product, the first path outermost, and a later path may point inside
    an earlier path's element (``explode=("obs", ("obs", "component"))``). A path that is missing,
    ``None`` or an empty list yields no rows for that record unless ``keep_empty=True``, which
    yields one row carrying the record's other fields with the exploded slot left out (a list
    position becomes ``None`` instead, so its neighbours keep their indices), so that a DataFrame
    shows NaN in that row's exploded columns. A path that reaches something other than a list — a
    dict, a string, a number — raises ``TypeError`` rather than being treated as one element.
    Records are never modified. To hoist an element's fields to the top instead of prefixing them
    with the path (``v`` rather than ``obs_v``), add ``collapse_single=True``.

    >>> records = [{"id": 1, "obs": [{"v": 5}, {"v": 7}]}, {"id": 2, "obs": []}]
    >>> flatten_rows(records, explode=("obs",))
    [{'id': 1, 'obs_v': 5}, {'id': 1, 'obs_v': 7}]
    >>> flatten_rows(records, explode=("obs",), keep_empty=True)
    [{'id': 1, 'obs_v': 5}, {'id': 1, 'obs_v': 7}, {'id': 2}]
    >>> flatten_rows(records, explode=("obs",), collapse_single=True)
    [{'id': 1, 'v': 5}, {'id': 1, 'v': 7}]
    >>> flatten_rows([{"a": [1, 2], "b": ["x", "y"]}], explode=("a", "b"))
    [{'a': 1, 'b': 'x'}, {'a': 1, 'b': 'y'}, {'a': 2, 'b': 'x'}, {'a': 2, 'b': 'y'}]

    Source: ``flattenObj`` (paste v3Fep60B) applied per record, as answer 75196824 does with
    ``[flattenDict(result) for result in ...]`` before ``pd.DataFrame(rows)``; ``explode`` is the
    unnesting of a list column that answer 75808253 did with ``pd.json_normalize(data,
    ['tax_info', []])``, whose comments explain why several nested lists are flattened before the
    DataFrame is built rather than after: pandas cannot know how they should align.
    """
    explode_paths = _explode_paths(explode)
    rows: list[dict[str, Any]] = []
    for record in records:
        variants = [record]
        for path in explode_paths:
            variants = [v for variant in variants for v in _explode(variant, path, keep_empty)]
        rows.extend(flatten(variant, **flatten_kwargs) for variant in variants)
    return rows


def _explode_paths(explode: Sequence[Path | Key]) -> tuple[Path, ...]:
    """Normalise ``explode`` to a tuple of paths: a key becomes a one-step path."""
    if isinstance(explode, _LEAVES):
        raise TypeError('explode must be a sequence of paths, as in explode=("obs",), not a string')
    result: list[Path] = []
    for entry in explode:
        if isinstance(entry, tuple):
            path: Path = entry
        elif isinstance(entry, str | int):
            path = (entry,)
        else:
            raise TypeError(f"explode entry {entry!r} must be a key or a tuple path")
        if not path:
            raise ValueError("an explode path needs at least one step")
        result.append(path)
    return tuple(result)


def _explode(record: Any, path: Path, keep_empty: bool) -> Iterator[Any]:
    """Yield a copy of ``record`` per element of the list at ``path``, the element in its place."""
    elements = get(record, *path)
    if elements is None:
        empty = True
    elif isinstance(elements, Mapping) or _children(elements) is None:
        raise TypeError(f"explode path {path!r} reached a {type(elements).__name__}, not a list")
    else:
        empty = len(elements) == 0
    if empty:
        if keep_empty:
            yield _without(record, path)
        return
    for element in elements:
        yield _with(record, path, element)


def _copy(obj: Any) -> dict[Any, Any] | list[Any]:
    """A shallow copy of a container to rebuild along an explode path."""
    if isinstance(obj, Mapping):
        return dict(obj)
    if isinstance(obj, Sequence) and not isinstance(obj, _LEAVES):
        return list(obj)
    raise TypeError(f"cannot rebuild a {type(obj).__name__} along an explode path")


def _with(obj: Any, path: Path, value: Any) -> Any:
    """``obj`` with ``value`` at ``path``, the containers along the path shallow-copied."""
    if not path:
        return value
    step, rest = path[0], path[1:]
    copy = _copy(obj)
    copy[step] = _with(obj[step], rest, value)
    return copy


def _without(obj: Any, path: Path) -> Any:
    """``obj`` without the slot at ``path``: a mapping key removed, a list position set to None."""
    step, rest = path[0], path[1:]
    child = get(obj, step, default=_MISSING)
    if child is _MISSING:
        return obj  # nothing there to leave out
    copy = _copy(obj)
    if rest:
        copy[step] = _without(child, rest)
    elif isinstance(copy, dict):
        del copy[step]
    else:
        copy[step] = None
    return copy
