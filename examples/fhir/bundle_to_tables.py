"""Turn FHIR R4 Bundles into Patient, Observation and Condition tables with nestpath.

    python examples/fhir/bundle_to_tables.py [DATA_DIR] [OUT_DIR]

Reads every ``*.json`` Bundle in ``DATA_DIR`` (default: ``data/`` next to this file, in file-name
order), takes each entry's ``resource`` together with its ``fullUrl``, groups the resources by
``resourceType``, applies the spec of :mod:`spec` to each one with :func:`nestpath.select_fields`
(inside :func:`nestpath.to_frame`), adds the two ``value[x]`` columns to the Observation table, and
writes ``patients.csv``, ``observations.csv`` and ``conditions.csv`` to ``OUT_DIR`` (default:
``out/`` next to this file). It prints the three shapes and, as proof that the ``fullUrl`` column
does its job, the number of Observations per patient obtained by joining ``Observation.subject``
to ``Patient.fullUrl``. References stay strings; nothing is resolved, validated or re-coded.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import pandas as pd
from spec import COLUMNS, SPECS, choose_value

from nestpath import get, to_frame

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
OUT_DIR = HERE / "out"


def load_bundles(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    """Read every ``*.json`` file in ``data_dir`` as a Bundle, in file-name order."""
    paths = sorted(data_dir.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def entries(bundles: Iterable[Mapping[str, Any]]) -> Iterator[tuple[str | None, Any]]:
    """Yield ``(fullUrl, resource)`` for every entry of every bundle that carries a resource."""
    for bundle in bundles:
        for entry in get(bundle, "entry", default=()):
            resource = get(entry, "resource")
            if resource is not None:
                yield get(entry, "fullUrl"), resource


def bundle_to_tables(bundles: Iterable[Mapping[str, Any]]) -> dict[str, pd.DataFrame]:
    """Return ``{"Patient": frame, "Observation": frame, "Condition": frame}``, a row per resource.

    Each frame has the columns of ``spec.COLUMNS`` for its type, in that order: ``fullUrl`` from the
    entry, the spec's columns from :func:`nestpath.to_frame`, and for Observations ``value`` and
    ``valueType`` from :func:`spec.choose_value`. Entries of other resource types are skipped.
    """
    by_type: dict[str, list[tuple[str | None, Any]]] = {name: [] for name in SPECS}
    for full_url, resource in entries(bundles):
        resource_type = get(resource, "resourceType")
        if resource_type in by_type:
            by_type[resource_type].append((full_url, resource))

    tables: dict[str, pd.DataFrame] = {}
    for resource_type, pairs in by_type.items():
        resources = [resource for _, resource in pairs]
        frame = to_frame(resources, SPECS[resource_type])
        frame.insert(0, "fullUrl", [full_url for full_url, _ in pairs])
        if resource_type == "Observation":
            chosen = [choose_value(resource) for resource in resources]
            frame["value"] = [value for value, _ in chosen]
            frame["valueType"] = [value_type for _, value_type in chosen]
        tables[resource_type] = frame[list(COLUMNS[resource_type])]
    return tables


def observations_per_patient(tables: Mapping[str, pd.DataFrame]) -> pd.Series:
    """Count Observations per patient by joining ``Observation.subject`` to ``Patient.fullUrl``."""
    patients = tables["Patient"][["fullUrl", "family", "given"]]
    joined = tables["Observation"].merge(
        patients, left_on="subject", right_on="fullUrl", suffixes=("", "_patient")
    )
    return joined.groupby(["family", "given"], sort=False).size()


def main(argv: list[str] | None = None) -> None:
    """Run the example: bundles in, three CSVs out, shapes and the join on stdout."""
    args = sys.argv[1:] if argv is None else argv
    data_dir = Path(args[0]) if args else DATA_DIR
    out_dir = Path(args[1]) if len(args) > 1 else OUT_DIR
    tables = bundle_to_tables(load_bundles(data_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    for resource_type, frame in tables.items():
        path = out_dir / f"{resource_type.lower()}s.csv"
        frame.to_csv(path, index=False)
        print(f"{resource_type:<12}{frame.shape[0]:>5} rows x {frame.shape[1]} columns -> {path}")
    print("\nObservations per patient (Observation.subject joined to Patient.fullUrl):")
    print(observations_per_patient(tables).to_string())


if __name__ == "__main__":
    main()
