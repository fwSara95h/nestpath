# nestpath

<!-- commit-date-notice -->
> [!NOTE]
> **Commit dates.** The material under `legacy/` was imported in October 2026 from my own pastebin pastes. Each imported commit is dated when its paste was first published (2022–2023), the way version-control migrations keep original dates, and holds the text as it stood when the archive was taken; every such commit names its source, both dates and the real import time, and [PROVENANCE.md](PROVENANCE.md) lists them all. Everything else is dated when it was actually committed.

A nested-data toolkit in the making: path access with defaults, flattening with controllable list handling, and field selection from a spec, for turning deeply nested dict/list/JSON structures into rows. It is being rebuilt from helper scripts I kept on pastebin and from 105 answers I wrote on Stack Overflow in 2022–2023 as [Driftr95](https://stackoverflow.com/users/6146136/driftr95); the answers themselves live, with their questions, in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr) (chapters `A1`–`A5`). Right now this repository holds the five legacy pastes and the package scaffold, nothing that runs yet; the Status section below is kept honest as the library takes shape.

## Install

Not on PyPI yet. From the repository:

```
pip install "nestpath @ git+https://github.com/fwSara95h/nestpath"
```

For development: clone, then `pip install -e ".[dev,pandas]"` and `pytest`. Python 3.11 or newer; the core has no dependencies, `pandas` is an optional extra.

## In thirty seconds

**This is the target, not a demo: none of it runs yet** (every function raises `NotImplementedError` until the Status section says otherwise). Paths are tuples of keys and indices; a path that misses gives the default instead of a `KeyError`/`IndexError`.

```python
from nestpath import flatten_rows, get, select_fields

patient = {
    "resourceType": "Patient",
    "id": "p1",
    "name": [{"family": "Rivera", "given": ["Ana", "Lucia"]}],
    "birthDate": "1984-03-09",
}

get(patient, "name", 0, "given", 0)  # 'Ana'
get(patient, "name", 0, "prefix", 0, default="")  # ''  (absent, so the default)

spec = [
    ("id", ("id",)),
    ("family", ("name", 0, "family")),
    ("given", ("name", 0, "given", 0)),
    ("gender", ("gender",), "unknown"),  # per-field default
]
select_fields(patient, spec)
# {'id': 'p1', 'family': 'Rivera', 'given': 'Ana', 'gender': 'unknown'}

observations = [
    {"id": "o1", "code": {"text": "Heart rate"}, "valueQuantity": {"value": 72, "unit": "/min"}},
    {"id": "o2", "code": {"text": "Body weight"}, "valueQuantity": {"value": 64.2, "unit": "kg"}},
]
flatten_rows(observations)
# [{'id': 'o1', 'code_text': 'Heart rate', 'valueQuantity_value': 72, 'valueQuantity_unit': '/min'},
#  {'id': 'o2', 'code_text': 'Body weight', 'valueQuantity_value': 64.2, 'valueQuantity_unit': 'kg'}]
```

## Status

**Scaffold only; nothing is implemented yet.** What is here today:

- `legacy/` — the original helper functions as they were published on pastebin (`getNestedVal`, `getObjPaths`, `getVal_byPath`, `flattenObj`, `recFlatten`, `alterTextVals`, `deepParseJson`), kept verbatim as the record of where the library comes from.
- `PROVENANCE.md` — what each imported file is, where it came from, and when.
- `pyproject.toml` and `src/nestpath/` — the package skeleton: the planned public API (`get`, `getter`, `paths`, `flatten`, `flatten_rows`, `select_fields`, `to_frame`) as signatures and docstrings that name the paste or answer each one comes from, every body a `NotImplementedError`.
- `tests/` — a smoke test (import, version, exported names); `.github/workflows/ci.yml` runs `ruff check` and `pytest` on Python 3.11 to 3.14.

Planned, in this order: an `examples/fhir/` walkthrough that turns a synthetic FHIR Bundle into Patient, Observation and Condition tables (written first, as the specification the library has to satisfy); `src/nestpath/` (`get`, `getter`, `flatten`, `flatten_rows`, `select_fields`) with tests; worked examples drawn from the archived answers, each linking to its question folder. Nothing above this line claims any of that exists yet.

## Provenance and licence

The repository is under the MIT licence (`LICENSE`). The pastes are my own code; `PROVENANCE.md` lists each one with its dates and hash. Examples that quote an answer or a question carry the attribution from the archive repository (CC BY-SA 4.0).
