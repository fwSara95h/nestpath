"""Optional pandas bridge: :func:`to_frame`. pandas is imported lazily (extra ``nestpath[pandas]``).

Sources: the A5 answers in stackoverflow-driftr, in particular 75590907 (question 75569289)
and 75808253 (question 75802736), the evidence for when ``pandas.json_normalize`` is enough
and when it is not; the ``pd.DataFrame(rows)`` step of answer 75196824 (question 75184221).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from nestpath.fields import FieldSpec, select_fields
from nestpath.flatten import flatten_rows

if TYPE_CHECKING:
    import pandas as pd


def to_frame(
    records: Iterable[Any],
    spec: Sequence[FieldSpec] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Build a DataFrame from nested records, one row per record (or per exploded element).

    With ``spec`` — ``(name, path[, default])`` entries as :func:`nestpath.select_fields` takes
    them — each record becomes one row and the columns are exactly the spec's names, in its order,
    **even for zero records**, so the frame's shape is fixed before any data is seen; the keyword
    arguments go to ``select_fields`` (``missing=``). Without ``spec`` the frame is
    ``pandas.DataFrame(flatten_rows(records, **kwargs))``, so the keyword arguments are those of
    :func:`nestpath.flatten_rows` (``explode``, ``keep_empty``, ``sep``, ``lists``,
    ``collapse_single``), the columns are the flattened keys in order of first appearance across
    the rows — pandas' rule for a list of dicts — a key absent from a row is a NaN cell, and zero
    records give an empty frame with no columns, since nothing is there to name them. Dtypes and
    the index are left to pandas: with pandas 3 a column of strings is ``str`` dtype and a ``None``
    in it shows as NaN, so test for empty cells with ``pandas.isna``, not ``is None``. pandas is
    imported here, not at package import; without it ``to_frame`` raises ``ImportError``
    (``pip install 'nestpath[pandas]'``).

    When ``pandas.json_normalize`` is enough: the records share one shape and at most one list
    needs unnesting — its ``record_path``, as in answer 75808253, where one list column became
    rows, ``meta`` carrying the parent fields along. When it is not: the columns are a choice of
    paths with defaults for absent elements (answer 75590907 reads them one key list at a time
    with ``try_get``; that is ``spec`` here), or several lists must be unnested together —
    ``json_normalize`` takes one ``record_path``, and the comments on 75808253 say why the rows
    are built before the frame instead: pandas cannot know how two lists align.

    >>> patients = [{"id": "p1", "name": [{"family": "Rivera"}]}, {"id": "p2"}]
    >>> spec = [("id", ("id",)), ("family", ("name", 0, "family"))]
    >>> frame = to_frame(patients, spec)
    >>> frame.columns.tolist(), frame.shape
    (['id', 'family'], (2, 2))
    >>> frame["family"].isna().tolist()
    [False, True]
    >>> to_frame([], spec).columns.tolist()
    ['id', 'family']
    >>> to_frame(patients).columns.tolist()
    ['id', 'name_0_family']
    >>> to_frame([{"id": 1, "obs": [{"v": 5}, {"v": 7}]}], explode=("obs",)).to_dict("records")
    [{'id': 1, 'obs_v': 5}, {'id': 1, 'obs_v': 7}]

    Source: answer 75196824's ``rows = [flattenDict(...) for ...]; pd.DataFrame(rows)`` is the
    no-spec branch; answer 75590907's ``pd.DataFrame([{kSep.join(kl): try_get(d, *kl) for kl in
    extractKeys} for d in ...])`` is the spec branch.
    """
    try:
        import pandas as pd
    except ImportError as error:
        raise ImportError("to_frame needs pandas: pip install 'nestpath[pandas]'") from error
    if spec is None:
        return pd.DataFrame(flatten_rows(records, **kwargs))
    columns = list(select_fields({}, spec, **kwargs))  # validates the spec; names in its order
    rows = [select_fields(record, spec, **kwargs) for record in records]
    return pd.DataFrame(rows, columns=columns)
