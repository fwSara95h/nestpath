# nestpath

<!-- commit-date-notice -->
> [!NOTE]
> **Commit dates.** The material under `legacy/` was imported in October 2026 from my own pastebin pastes. Each imported commit is dated when its paste was first published (2022–2023), the way version-control migrations keep original dates, and holds the text as it stood when the archive was taken; every such commit names its source, both dates and the real import time, and [PROVENANCE.md](PROVENANCE.md) lists them all. Everything else is dated when it was actually committed.

A nested-data toolkit in the making: path access with defaults, flattening with controllable list handling, and field selection from a spec, for turning deeply nested dict/list/JSON structures into rows. It is being rebuilt from helper scripts I kept on pastebin and from 105 answers I wrote on Stack Overflow in 2022–2023 as [Driftr95](https://stackoverflow.com/users/6146136/driftr95); the answers themselves live, with their questions, in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr) (chapters `A1`–`A5`). Right now this repository holds the five legacy pastes and nothing else; the status section below is kept honest as the library takes shape.

## Status

Imported source material only. What is here today:

- `legacy/` — the original helper functions as they were published on pastebin (`getNestedVal`, `getObjPaths`, `getVal_byPath`, `flattenObj`, `recFlatten`, `alterTextVals`, `deepParseJson`), kept verbatim as the record of where the library comes from.
- `PROVENANCE.md` — what each imported file is, where it came from, and when.

Planned, in this order: an `examples/fhir/` walkthrough that turns a synthetic FHIR Bundle into Patient, Observation and Condition tables (written first, as the specification the library has to satisfy); `src/nestpath/` (`get`, `getter`, `flatten`, `flatten_rows`, `select_fields`) with tests; worked examples drawn from the archived answers, each linking to its question folder. Nothing above this line claims any of that exists yet.

## Provenance and licence

The pastes are my own code; `PROVENANCE.md` lists each one with its dates and hash. Library code under `src/` will be MIT. Examples that quote an answer or a question carry the attribution from the archive repository (CC BY-SA 4.0).
