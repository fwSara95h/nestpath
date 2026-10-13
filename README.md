# nestpath

<!-- commit-date-notice -->
> [!NOTE]
> **Commit dates.** The material under `legacy/` was imported in October 2026 from my own pastebin pastes. Each imported commit is dated when its paste was first published (2022–2023), the way version-control migrations keep original dates, and holds the text as it stood when the archive was taken; every such commit names its source, both dates and the real import time, and [PROVENANCE.md](PROVENANCE.md) lists them all. Everything else is dated when it was actually committed.

A nested-data toolkit in the making: path access with defaults, flattening with controllable list handling, and field selection from a spec, for turning deeply nested dict/list/JSON structures into rows. It is being rebuilt from helper scripts I kept on pastebin and from 105 answers I wrote on Stack Overflow in 2022–2023 as [Driftr95](https://stackoverflow.com/users/6146136/driftr95); the answers themselves live, with their questions, in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr) (chapters `A1`–`A5`). Right now this repository holds the five legacy pastes, the FHIR example written first as the specification, and the first four functions of the core (`get`, `getter`, `paths`, `select_fields`) with their tests; flattening and the pandas bridge are still to come, and the Status section below is kept honest as the library takes shape.

## Install

Not on PyPI yet. From the repository:

```
pip install "nestpath @ git+https://github.com/fwSara95h/nestpath"
```

For development: clone, then `pip install -e ".[dev,pandas]"` and `pytest`. Python 3.11 or newer; the core has no dependencies, `pandas` is an optional extra.

## In thirty seconds

**This is the target, and part of it runs:** `get` and `select_fields` below work today; `flatten_rows` still raises `NotImplementedError` (the Status section says what works). Paths are tuples of keys and indices; a path that misses gives the default instead of a `KeyError`/`IndexError`.

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

**Path access and field selection work; flattening and the pandas bridge do not yet.** What is here today:

- `legacy/` — the original helper functions as they were published on pastebin (`getNestedVal`, `getObjPaths`, `getVal_byPath`, `flattenObj`, `recFlatten`, `alterTextVals`, `deepParseJson`), kept verbatim as the record of where the library comes from.
- `PROVENANCE.md` — what each imported file is, where it came from, and when.
- `src/nestpath/` — **implemented, with tests:** `get` (path access with a default; strings and bytes are values, never containers), `getter` (the same as a `key=` function), `paths` (every path to a leaf, or every path) and `select_fields` (a `(name, path[, default])` spec applied to a record). **Not yet:** `flatten`, `flatten_rows` and `to_frame`, whose bodies still raise `NotImplementedError`. Every docstring names the paste or answer the function comes from.
- `examples/fhir/` — the FHIR example, written first as the specification the library has to satisfy: seven synthetic Synthea R4 bundles (`data/`, with their source and terms), the column specs as data with the `value[x]` rule stated (`spec.py`), and the script that turns the bundles into Patient, Observation and Condition tables (`bundle_to_tables.py`). It calls the API as it is meant to behave, so it does not run yet; its README says what it shows and what it does not claim.
- `tests/` — the smoke test (import, version, exported names), `test_paths.py` and `test_fields.py` (28 tests, including two Hypothesis properties: `get` follows every path `paths` yields, and reaches exactly the leaves), and `test_fhir_example.py`, ten tests that run the example on the committed bundles and stay red on purpose until `to_frame` exists; `.github/workflows/ci.yml` runs `ruff check` and `pytest` on Python 3.11 to 3.14, so it is red for the same reason.

Planned, in this order: `flatten`, `flatten_rows` and `to_frame` with tests, which is what turns the FHIR test green; tests derived from the archived answers; worked examples drawn from them, each linking to its question folder. Nothing above this line claims any of that exists yet.

## Provenance and licence

The repository is under the MIT licence (`LICENSE`). The pastes are my own code; `PROVENANCE.md` lists each one with its dates and hash. Examples that quote an answer or a question carry the attribution from the archive repository (CC BY-SA 4.0).
