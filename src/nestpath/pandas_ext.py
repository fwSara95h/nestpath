"""Optional pandas bridge: :func:`to_frame`. pandas is imported lazily (extra ``nestpath[pandas]``).

Sources: the A5 answers in stackoverflow-driftr, in particular 75590907 (question 75569289)
and 75808253 (question 75802736), the evidence for when ``pandas.json_normalize`` is enough
and when it is not.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from nestpath.fields import FieldSpec

if TYPE_CHECKING:
    import pandas as pd

_NOT_IMPLEMENTED = "planned for v0.1; see the Status section of the README"


def to_frame(
    records: Iterable[Any],
    spec: Sequence[FieldSpec] | None = None,
    **flatten_kwargs: Any,
) -> pd.DataFrame:
    """Build a DataFrame from nested records.

    Without ``spec``: ``pandas.DataFrame(flatten_rows(records, **flatten_kwargs))``. With
    ``spec``: one :func:`nestpath.select_fields` call per record, so the columns are exactly the
    spec's names in order.

    Source: answers 75590907 and 75808253 (the A5 chapter of the archive).
    """
    raise NotImplementedError(_NOT_IMPLEMENTED)
