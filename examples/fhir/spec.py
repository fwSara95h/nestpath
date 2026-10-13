"""The specification: which columns the FHIR example reads, as data.

Written before the library (plan-A step 3), this file is what ``nestpath`` has to satisfy. Each
spec below is a list in the shape :func:`nestpath.select_fields` takes — ``(column, path)`` or
``(column, path, default)``, the path a tuple of keys and indices applied to one FHIR *resource* —
so the same spec works on a resource taken out of a Bundle entry, out of a searchset, or fetched
on its own. ``fullUrl`` belongs to the Bundle *entry*, not to the resource, so it is the one column
that ``bundle_to_tables.py`` adds itself, in front of the spec's columns.

Column names are FHIR's own element names wherever a column is one element (``birthDate``,
``effectiveDateTime``); a column that holds a chosen sub-element says what it holds (``family`` is
``name[0].family``, ``subject`` is ``subject.reference``, left as a string and never resolved).
A path that misses gives the entry's default, or ``None``: that is how absent optional elements
(``deceasedDateTime`` on six of the seven patients, ``abatementDateTime`` on 24 of 65 conditions)
become empty cells instead of ``KeyError``.

The one thing a path cannot say is FHIR's ``value[x]``: an Observation carries at most one
value element, named ``value`` plus its type (``valueQuantity``, ``valueString``,
``valueCodeableConcept``, …). :data:`OBSERVATION_VALUE` states the rule as data and
:func:`choose_value` applies it.

Patterns: the ``filters`` idiom of answer 75205202 (a dict of names to paths, applied to each
record) and the default-on-miss ``getVal`` of answer 75466591, both in chapter A1 of
https://github.com/fwSara95h/stackoverflow-driftr.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nestpath import FieldSpec, Path, get

PATIENT: list[FieldSpec] = [
    ("id", ("id",)),
    ("family", ("name", 0, "family")),
    ("given", ("name", 0, "given", 0)),
    ("gender", ("gender",), "unknown"),  # a code in FHIR's AdministrativeGender set
    ("birthDate", ("birthDate",)),
    ("deceasedDateTime", ("deceasedDateTime",)),  # absent unless the patient died
]
"""Patient → one row per resource. ``given`` is the first given name only."""

OBSERVATION: list[FieldSpec] = [
    ("id", ("id",)),
    ("subject", ("subject", "reference")),
    ("code", ("code", "coding", 0, "code")),
    ("display", ("code", "coding", 0, "display")),
    ("unit", ("valueQuantity", "unit")),  # only a Quantity has a unit; None for the other forms
    ("effectiveDateTime", ("effectiveDateTime",)),
]
"""Observation → one row per resource; ``value``/``valueType`` come from :func:`choose_value`."""

OBSERVATION_VALUE: list[tuple[str, Path]] = [
    ("Quantity", ("valueQuantity", "value")),
    ("string", ("valueString",)),
    ("CodeableConcept", ("valueCodeableConcept", "text")),
]
"""The ``value[x]`` rule: alternatives tried in order; the first path that hits wins.

Three of FHIR's eleven ``value[x]`` types are handled. The other eight (``valueBoolean``,
``valueInteger``, ``valueRange``, ``valueRatio``, ``valueSampledData``, ``valueTime``,
``valueDateTime``, ``valuePeriod``) and Observations whose values sit in ``component[]`` (the
blood-pressure panels in the sample data) are out of scope and give ``None`` for both columns.
"""

CONDITION: list[FieldSpec] = [
    ("id", ("id",)),
    ("subject", ("subject", "reference")),
    ("code", ("code", "coding", 0, "code")),
    ("display", ("code", "coding", 0, "display")),
    ("onsetDateTime", ("onsetDateTime",)),
    ("abatementDateTime", ("abatementDateTime",)),  # absent while the condition is active
]
"""Condition → one row per resource."""

SPECS: dict[str, list[FieldSpec]] = {
    "Patient": PATIENT,
    "Observation": OBSERVATION,
    "Condition": CONDITION,
}
"""The resource types the example reads, each with its spec. Other types are left in place."""

COLUMNS: dict[str, tuple[str, ...]] = {
    "Patient": ("fullUrl", "id", "family", "given", "gender", "birthDate", "deceasedDateTime"),
    "Observation": (
        "fullUrl",
        "id",
        "subject",
        "code",
        "display",
        "value",
        "valueType",
        "unit",
        "effectiveDateTime",
    ),
    "Condition": (
        "fullUrl",
        "id",
        "subject",
        "code",
        "display",
        "onsetDateTime",
        "abatementDateTime",
    ),
}
"""The three tables' columns, in order: ``fullUrl`` from the entry, then the spec, with the two
chooser columns placed after ``display`` in the Observation table."""

_MISS = object()


def choose_value(observation: Mapping[str, Any]) -> tuple[Any, str | None]:
    """Return ``(value, valueType)`` for one Observation by the :data:`OBSERVATION_VALUE` rule.

    The alternatives are tried in order with :func:`nestpath.get`; the first path that hits gives
    the value and its type label (``"Quantity"``, ``"string"`` or ``"CodeableConcept"``). When none
    hits the result is ``(None, None)``.

    >>> choose_value({"valueQuantity": {"value": 72, "unit": "/min"}})
    (72, 'Quantity')
    >>> choose_value({"valueCodeableConcept": {"text": "Never smoked tobacco (finding)"}})
    ('Never smoked tobacco (finding)', 'CodeableConcept')
    >>> choose_value({"component": [{"code": {"text": "Systolic Blood Pressure"}}]})
    (None, None)
    """
    for value_type, path in OBSERVATION_VALUE:
        value = get(observation, *path, default=_MISS)
        if value is not _MISS:
            return value, value_type
    return None, None
