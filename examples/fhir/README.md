# FHIR example: Bundles to tables

```
python examples/fhir/bundle_to_tables.py
```

reads the seven synthetic FHIR R4 Bundles in [`data/`](data/README.md) and writes `out/patients.csv`, `out/observations.csv` and `out/conditions.csv` — one row per Patient, Observation and Condition resource, 7 / 613 / 65 rows — then prints the shapes and the number of Observations per patient. It needs the pandas extra (`pip install -e ".[pandas]"`).

**Status (2026-10-13): written as the specification, and now running.** The example was written before the library, as the thing `nestpath` had to satisfy: it calls `get`, `select_fields` and `to_frame` the way they were meant to behave. All three exist now, so the script runs and `tests/test_fhir_example.py` (ten tests on these bundles) is green — with `spec.py` and `bundle_to_tables.py` unchanged since they were written, which was the point of writing them first. The repository README's Status section says what works.

## What it shows

**Specs as data.** [`spec.py`](spec.py) holds one list per resource type, each entry `(column, path)` or `(column, path, default)` with the path a tuple of keys and indices into the resource: `("name", 0, "family")` is `name[0].family`. The spec is the whole description of a table; `bundle_to_tables.py` applies it with `select_fields` inside `to_frame` and adds nothing of its own except `fullUrl` (below). Column names are FHIR's own element names where a column is one element (`birthDate`, `effectiveDateTime`, `onsetDateTime`) and say what they hold where it is a chosen sub-element (`family`, `subject`, `code`, `display`).

**Defaults for absent elements.** A path that misses gives the entry's default, or `None`, which pandas writes as an empty cell: `deceasedDateTime` is present on one of the seven patients, `abatementDateTime` on 41 of the 65 conditions (the other 24 are still active), `unit` only where the value is a Quantity. `gender` carries the one non-`None` default, `"unknown"`, a code from FHIR's own AdministrativeGender set; it never fires on these seven patients.

**One row per Observation, with the `value[x]` rule stated.** An Observation carries at most one value element, named `value` plus its type, and no single path can express that. `OBSERVATION_VALUE` in `spec.py` lists the three forms this example handles, in order — `valueQuantity.value`, `valueString`, `valueCodeableConcept.text` — and `choose_value` takes the first path that hits, filling `value` and `valueType`. The 52 blood-pressure panels, whose values sit in `component[]`, have no top-level value and get empty cells in both columns; so would any of the eight other `value[x]` types, which are out of scope.

**The `fullUrl` / reference join.** Resources are read from `entry[].resource`, and each entry's `fullUrl` is kept as the first column. `subject.reference` is copied as a string — `urn:uuid:…` in these transaction bundles, `Patient/<id>` in a server's searchset — and never resolved; joining `Observation.subject` to `Patient.fullUrl` is how a row finds its patient, which is what the script's last lines do:

```
Patient         7 rows x 7 columns -> …/examples/fhir/out/patients.csv
Observation   613 rows x 9 columns -> …/examples/fhir/out/observations.csv
Condition      65 rows x 7 columns -> …/examples/fhir/out/conditions.csv

Observations per patient (Observation.subject joined to Patient.fullUrl):
family       given
Lockman863   Brock407       74
Graham902    Dallas143     133
Torphy630    Dudley365      82
Little434    Lou594         95
Wiegand701   Martha161     126
Schimmel440  Stanton715     31
Lubowitz58   Tanner110      72
```

Seven bundles in, one table per type out, rows in file-name order: a directory of bundles is how Synthea output and bulk exports arrive.

## The tables

Patient — `fullUrl, id, family, given, gender, birthDate, deceasedDateTime` (three of the seven rows):

| fullUrl | id | family | given | gender | birthDate | deceasedDateTime |
| --- | --- | --- | --- | --- | --- | --- |
| urn:uuid:30889246-5f7d-9305-542f-55cb89e1f4de | 30889246-5f7d-9305-542f-55cb89e1f4de | Torphy630 | Dudley365 | male | 1960-03-25 | 1961-08-23T10:39:49+00:00 |
| urn:uuid:ee4b7339-ca58-b6af-c199-04b6d5761c73 | ee4b7339-ca58-b6af-c199-04b6d5761c73 | Schimmel440 | Stanton715 | male | 2026-05-27 |  |
| urn:uuid:bd4e49cb-391b-d08a-c7ab-b585e7bd5758 | bd4e49cb-391b-d08a-c7ab-b585e7bd5758 | Lubowitz58 | Tanner110 | male | 1984-12-02 |  |

Observation — `fullUrl, id, subject, code, display, value, valueType, unit, effectiveDateTime` (one row of each `value[x]` outcome):

| fullUrl | id | subject | code | display | value | valueType | unit | effectiveDateTime |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| urn:uuid:a406f356-c8b4-54ad-6043-17b503fb1717 | a406f356-c8b4-54ad-6043-17b503fb1717 | urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19 | 8302-2 | Body Height | 180.2 | Quantity | cm | 2018-02-16T13:04:01+00:00 |
| urn:uuid:a406f356-c8b4-54ad-3647-73c89ead94dd | a406f356-c8b4-54ad-3647-73c89ead94dd | urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19 | 72166-2 | Tobacco smoking status | Ex-smoker (finding) | CodeableConcept |  | 2018-02-16T13:04:01+00:00 |
| urn:uuid:a406f356-c8b4-54ad-4a76-aae56fea6260 | a406f356-c8b4-54ad-4a76-aae56fea6260 | urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19 | 85354-9 | Blood pressure panel with all children optional |  |  |  | 2018-02-16T13:04:01+00:00 |

Condition — `fullUrl, id, subject, code, display, onsetDateTime, abatementDateTime` (one abated, one active):

| fullUrl | id | subject | code | display | onsetDateTime | abatementDateTime |
| --- | --- | --- | --- | --- | --- | --- |
| urn:uuid:a406f356-c8b4-54ad-12e1-efe4c9edf814 | a406f356-c8b4-54ad-12e1-efe4c9edf814 | urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19 | 314529007 | Medication review due (situation) | 2010-01-29T13:04:01+00:00 | 2018-02-16T13:04:01+00:00 |
| urn:uuid:a406f356-c8b4-54ad-b92e-0e96f1513380 | a406f356-c8b4-54ad-b92e-0e96f1513380 | urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19 | 224295006 | Only received primary school education (finding) | 2010-01-29T13:49:54+00:00 |  |

## What it does not claim

No terminology handling: codes and display strings are copied as found from `coding[0]`, and what a LOINC or SNOMED CT code means is not looked at. No profiles: the US Core `meta.profile` on every resource is ignored. No validation: the bundles are trusted as they come. No `value[x]` beyond the three forms above, and no `component[]`. No reference resolution: `subject` is a string you join on, and `encounter`, `performer` and the rest are not read at all. Only the first name, first given name and first coding of each resource; dates stay ISO strings rather than becoming datetimes; the seventeen other resource types in the bundles (Encounter, Procedure, Claim, …) are left in place and untouched.

## Where this points

Turning nested exchange formats — FHIR bundles, EHR exports, device telemetry — into typed tables is the first step of clinical data platform ingestion, and this example is that step and only that step: no terminology service, no de-identification, no persistence, no scale. One thing it surfaced for the library: `value[x]` is the one thing a path spec cannot say, and `choose_value` is an ordered list of alternative paths in disguise; whether `nestpath` grows such a primitive is a question for after v0.1, raised here and deferred on purpose.

## Data

Seven of the "100 Sample Synthetic Patient Records, FHIR R4" published by the Synthea project, committed byte for byte; [`data/README.md`](data/README.md) has the source, the archive's hash and date, each file's hash and counts, and the terms under which the data is used.
