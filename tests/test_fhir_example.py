"""The FHIR example as the specification (plan-A step 3).

These tests run ``examples/fhir/bundle_to_tables.py`` on the seven committed Synthea bundles and
pin the shapes, a handful of cells, the ``value[x]`` rule and the ``fullUrl`` join. They are red
until the core API exists (step 4): that is the point of writing the example first. pandas is the
optional extra the example needs, so the module is skipped when it is not installed.

The expected numbers come from the bundles themselves (``examples/fhir/data/README.md`` lists them
per file); row order is file-name order, so the first rows belong to ``Brock407_Lockman863``.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from nestpath import select_fields

pd = pytest.importorskip("pandas")

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "fhir"

BROCK = "urn:uuid:a406f356-c8b4-54ad-e79c-54a5e15ffc19"
DUDLEY = "urn:uuid:30889246-5f7d-9305-542f-55cb89e1f4de"

OBSERVATIONS_PER_PATIENT = {
    ("Lockman863", "Brock407"): 74,
    ("Graham902", "Dallas143"): 133,
    ("Torphy630", "Dudley365"): 82,
    ("Little434", "Lou594"): 95,
    ("Wiegand701", "Martha161"): 126,
    ("Schimmel440", "Stanton715"): 31,
    ("Lubowitz58", "Tanner110"): 72,
}
CONDITIONS_PER_PATIENT = {
    "Lockman863": 15,
    "Graham902": 7,
    "Torphy630": 5,
    "Little434": 16,
    "Wiegand701": 8,
    "Schimmel440": 1,
    "Lubowitz58": 13,
}


@pytest.fixture(scope="module")
def example():
    """Import ``examples/fhir/bundle_to_tables.py`` (and its sibling ``spec``) as modules."""
    sys.path.insert(0, str(EXAMPLE_DIR))
    try:
        return importlib.import_module("bundle_to_tables")
    finally:
        sys.path.remove(str(EXAMPLE_DIR))


@pytest.fixture(scope="module")
def bundles(example) -> list[dict]:
    return example.load_bundles()


@pytest.fixture(scope="module")
def tables(example, bundles) -> dict[str, pd.DataFrame]:
    return example.bundle_to_tables(bundles)


def test_seven_bundles_with_one_patient_each(bundles) -> None:
    assert len(bundles) == 7
    assert all(bundle["type"] == "transaction" for bundle in bundles)
    assert sum(len(bundle["entry"]) for bundle in bundles) == 1418


def test_one_table_per_type_with_the_spec_columns(example, tables) -> None:
    spec = example.COLUMNS
    assert set(tables) == {"Patient", "Observation", "Condition"}
    for resource_type, frame in tables.items():
        assert tuple(frame.columns) == spec[resource_type]
    assert tables["Patient"].shape == (7, 7)
    assert tables["Observation"].shape == (613, 9)
    assert tables["Condition"].shape == (65, 7)


def test_patient_cells_and_the_absent_optional_element(tables) -> None:
    patients = tables["Patient"].set_index("fullUrl")
    dudley = patients.loc[DUDLEY]
    assert dudley["id"] == "30889246-5f7d-9305-542f-55cb89e1f4de"
    assert (dudley["family"], dudley["given"]) == ("Torphy630", "Dudley365")
    assert (dudley["gender"], dudley["birthDate"]) == ("male", "1960-03-25")
    assert dudley["deceasedDateTime"] == "1961-08-23T10:39:49+00:00"
    assert patients["deceasedDateTime"].notna().sum() == 1  # the other six are empty cells
    tanner = patients.loc["urn:uuid:bd4e49cb-391b-d08a-c7ab-b585e7bd5758"]
    assert tanner["given"] == "Tanner110"  # one given name: ("name", 0, "given", 0) still hits
    assert pd.isna(tanner["deceasedDateTime"])
    assert set(patients["gender"]) == {"male", "female"}  # the "unknown" default never fires here


def test_value_x_rule_on_the_observation_table(tables) -> None:
    observations = tables["Observation"]
    value_type = observations["valueType"]
    assert (value_type == "Quantity").sum() == 518
    assert (value_type == "CodeableConcept").sum() == 43
    assert value_type.isna().sum() == 52  # blood-pressure panels: component[] only
    assert observations["value"].isna().sum() == 52
    assert observations["unit"].isna().sum() == 43 + 52  # only a Quantity has a unit

    first = observations.iloc[0]  # Brock407's body height at his first encounter
    assert first["fullUrl"] == "urn:uuid:a406f356-c8b4-54ad-6043-17b503fb1717"
    assert first["subject"] == BROCK
    assert (first["code"], first["display"]) == ("8302-2", "Body Height")
    assert (first["value"], first["valueType"], first["unit"]) == (180.2, "Quantity", "cm")
    assert first["effectiveDateTime"] == "2018-02-16T13:04:01+00:00"

    smoking = observations[observations["valueType"] == "CodeableConcept"].iloc[0]
    assert (smoking["code"], smoking["display"]) == ("72166-2", "Tobacco smoking status")
    assert smoking["value"] == "Ex-smoker (finding)"  # valueCodeableConcept.text
    assert pd.isna(smoking["unit"])

    panel = observations[observations["code"] == "85354-9"].iloc[0]
    assert panel["display"] == "Blood pressure panel with all children optional"
    assert pd.isna(panel["value"]) and pd.isna(panel["valueType"]) and pd.isna(panel["unit"])


def test_condition_cells_and_abatement(tables) -> None:
    conditions = tables["Condition"]
    first = conditions.iloc[0]
    assert first["fullUrl"] == "urn:uuid:a406f356-c8b4-54ad-12e1-efe4c9edf814"
    assert first["subject"] == BROCK
    assert (first["code"], first["display"]) == ("314529007", "Medication review due (situation)")
    assert first["onsetDateTime"] == "2010-01-29T13:04:01+00:00"
    assert first["abatementDateTime"] == "2018-02-16T13:04:01+00:00"
    assert conditions["abatementDateTime"].isna().sum() == 24  # still active
    assert conditions["onsetDateTime"].notna().all()


def test_subject_references_join_back_to_patients(example, tables) -> None:
    patient_urls = set(tables["Patient"]["fullUrl"])
    assert set(tables["Observation"]["subject"]) == patient_urls
    assert set(tables["Condition"]["subject"]) == patient_urls
    assert example.observations_per_patient(tables).to_dict() == OBSERVATIONS_PER_PATIENT
    joined = tables["Condition"].merge(
        tables["Patient"][["fullUrl", "family"]], left_on="subject", right_on="fullUrl"
    )
    assert joined.groupby("family", sort=False).size().to_dict() == CONDITIONS_PER_PATIENT


def test_select_fields_on_one_resource_gives_plain_python(example, bundles) -> None:
    spec = importlib.import_module("spec")
    patients = {
        entry["resource"]["name"][0]["given"][0]: entry["resource"]
        for bundle in bundles
        for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "Patient"
    }
    assert select_fields(patients["Dudley365"], spec.PATIENT) == {
        "id": "30889246-5f7d-9305-542f-55cb89e1f4de",
        "family": "Torphy630",
        "given": "Dudley365",
        "gender": "male",
        "birthDate": "1960-03-25",
        "deceasedDateTime": "1961-08-23T10:39:49+00:00",
    }
    assert select_fields(patients["Stanton715"], spec.PATIENT)["deceasedDateTime"] is None
    assert select_fields({"resourceType": "Patient"}, spec.PATIENT) == {
        "id": None,
        "family": None,
        "given": None,
        "gender": "unknown",
        "birthDate": None,
        "deceasedDateTime": None,
    }


def test_choose_value_covers_the_three_forms_in_order(example) -> None:
    spec = importlib.import_module("spec")
    assert spec.choose_value({"valueQuantity": {"value": 72, "unit": "/min"}}) == (72, "Quantity")
    assert spec.choose_value({"valueString": "blue"}) == ("blue", "string")
    concept = {"valueCodeableConcept": {"text": "Never smoked tobacco (finding)"}}
    assert spec.choose_value(concept) == ("Never smoked tobacco (finding)", "CodeableConcept")
    assert spec.choose_value({"valueBoolean": True}) == (None, None)  # out of scope
    assert spec.choose_value({"component": [{"valueQuantity": {"value": 120}}]}) == (None, None)
    both = {"valueQuantity": {"value": 1}, "valueString": "one"}  # not valid FHIR; the order rule
    assert spec.choose_value(both) == (1, "Quantity")


def test_empty_input_gives_empty_tables_with_the_columns(example) -> None:
    tables = example.bundle_to_tables([])
    for resource_type, frame in tables.items():
        assert tuple(frame.columns) == example.COLUMNS[resource_type]
        assert len(frame) == 0


def test_main_writes_three_csvs(example, tmp_path, capsys) -> None:
    example.main([str(example.DATA_DIR), str(tmp_path)])
    for name, rows in (("patients", 7), ("observations", 613), ("conditions", 65)):
        frame = pd.read_csv(tmp_path / f"{name}.csv")
        assert len(frame) == rows
    header = (tmp_path / "observations.csv").read_text(encoding="utf-8").splitlines()[0]
    assert header == ",".join(example.COLUMNS["Observation"])
    out = capsys.readouterr().out
    assert "Observation   613 rows x 9 columns" in out
    assert "Observations per patient" in out and "Lubowitz58" in out
