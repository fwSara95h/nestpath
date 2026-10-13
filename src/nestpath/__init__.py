"""nestpath: path access, flattening and field selection for nested dict/list/JSON data.

Paths are tuples of dict keys and sequence indices, applied in order: ``("name", 0, "family")``
reads ``obj["name"][0]["family"]``. Dotted strings and attribute access are deliberately not
part of the API (keys may contain dots; dicts may have attribute-like keys).

The functions are being rebuilt from the author's pastebin helpers (``legacy/``) and her
2022-2023 Stack Overflow answers, archived in https://github.com/fwSara95h/stackoverflow-driftr.
Each docstring names the paste or answer it comes from. Until a function is implemented it
raises ``NotImplementedError``; the README's Status section says what works.
"""

from __future__ import annotations

from nestpath.fields import FieldSpec, select_fields
from nestpath.flatten import KeyCollisionError, flatten, flatten_rows
from nestpath.pandas_ext import to_frame
from nestpath.paths import Key, Path, get, getter, paths

__version__ = "0.1.0.dev0"

__all__ = [
    "FieldSpec",
    "Key",
    "KeyCollisionError",
    "Path",
    "__version__",
    "flatten",
    "flatten_rows",
    "get",
    "getter",
    "paths",
    "select_fields",
    "to_frame",
]
