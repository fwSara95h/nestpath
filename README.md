# nestpath

<!-- commit-date-notice -->
> [!NOTE]
> **Commit dates.** The material under `legacy/` was imported in October 2026 from my own pastebin pastes. Each imported commit is dated when its paste was first published (2022–2023), the way version-control migrations keep original dates, and holds the text as it stood when the archive was taken; every such commit names its source, both dates and the real import time, and [PROVENANCE.md](PROVENANCE.md) lists them all. Everything else is dated when it was actually committed.

A nested-data toolkit in the making: path access with defaults, flattening with controllable list handling, and field selection from a spec, for turning deeply nested dict/list/JSON structures into rows. It is being rebuilt from helper scripts I kept on pastebin and from 105 answers I wrote on Stack Overflow in 2022–2023 as [Driftr95](https://stackoverflow.com/users/6146136/driftr95); the answers themselves live, with their questions, in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr) (chapters `A1`–`A5`). Right now this repository holds the five legacy pastes, the FHIR example written first as the specification, and the seven functions of the core API (`get`, `getter`, `paths`, `flatten`, `flatten_rows`, `select_fields`, `to_frame`) with their tests; the example runs. The Status section below is kept honest as the library takes shape.

## Install

Not on PyPI yet. From the repository:

```
pip install "nestpath @ git+https://github.com/fwSara95h/nestpath"
```

For development: clone, then `pip install -e ".[dev,pandas]"` and `pytest`. Python 3.11 or newer; the core has no dependencies, `pandas` is an optional extra.

## In thirty seconds

**All of this runs.** Paths are tuples of keys and indices; a path that misses gives the default instead of a `KeyError`/`IndexError`.

```python
from nestpath import flatten_rows, get, select_fields, to_frame

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

to_frame(observations, [("id", ("id",)), ("value", ("valueQuantity", "value"))])
#    id  value
# 0  o1   72.0
# 1  o2   64.2
```

`to_frame` needs the `pandas` extra; with a spec its columns are exactly the spec's names, even for zero records, and without one it is `pandas.DataFrame(flatten_rows(...))`. `flatten_rows(records, explode=("component",))` gives one row per element of a list instead of one per record.

## Status

**The core API exists and the FHIR example runs.** What is here today:

- `legacy/` — the original helper functions as they were published on pastebin (`getNestedVal`, `getObjPaths`, `getVal_byPath`, `flattenObj`, `recFlatten`, `alterTextVals`, `deepParseJson`), kept verbatim as the record of where the library comes from.
- `PROVENANCE.md` — what each imported file is, where it came from, and when.
- `src/nestpath/` — **implemented, with tests:** `get` (path access with a default; strings and bytes are values, never containers), `getter` (the same as a `key=` function), `paths` (every path to a leaf, or every path), `flatten` (one level, keys joined with `sep`, lists indexed into the keys or kept as values, `collapse_single` for the legacy habit of dropping a lone nested level, colliding keys raising `KeyCollisionError` instead of overwriting), `flatten_rows` (one row per record, or per element of each `explode`d list — several paths give the cross product — with `keep_empty` for records whose list is empty), `select_fields` (a `(name, path[, default])` spec applied to a record) and `to_frame` (a DataFrame from a spec, with the spec's columns even for zero records, or from `flatten_rows`; pandas is the optional extra, imported only there). Every docstring names the paste or answer the function comes from.
- `examples/fhir/` — the FHIR example, written first as the specification the library had to satisfy: seven synthetic Synthea R4 bundles (`data/`, with their source and terms), the column specs as data with the `value[x]` rule stated (`spec.py`), and the script that turns the bundles into Patient, Observation and Condition tables (`bundle_to_tables.py`). It runs — `python examples/fhir/bundle_to_tables.py` writes three CSVs and prints the shapes and the Observations-per-patient join — with `spec.py` and `bundle_to_tables.py` unchanged since they were written; its README says what it shows and what it does not claim.
- `tests/` — the smoke test (import, version, exported names); `test_paths.py`, `test_fields.py`, `test_flatten.py` and `test_pandas_ext.py` (75 tests, including five Hypothesis properties: `get` follows every path `paths` yields and reaches exactly the leaves, `flatten` never loses a leaf, `collapse_single` keeps every leaf or raises, exploded rows are the cross product of their lists); `test_from_answers.py`, nine tests that each take the situation of an archived answer — optional fields, keys applied from a spec, a tree flattened to its values, nested metrics to rows, sorting and grouping by nested keys, uneven records to CSV, a dict column to columns, a list column to rows — on an invented fixture, with the question folder linked; and `test_fhir_example.py`, ten tests that run the example on the committed bundles — 96 tests in all. `.github/workflows/ci.yml` runs `ruff check` and `pytest` on Python 3.11 to 3.14.

Planned, in this order: worked examples drawn from the answers, each linking to its question folder; then a tagged v0.1. Nothing above this line claims any of that exists yet.

## Provenance and licence

The repository is under the MIT licence (`LICENSE`). The pastes are my own code; `PROVENANCE.md` lists each one with its dates and hash. Examples that quote an answer or a question carry the attribution from the archive repository (CC BY-SA 4.0).
