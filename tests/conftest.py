"""Shared fixtures: invented data in the library's target shapes, never copied from a question."""

from __future__ import annotations

import pytest


@pytest.fixture
def patient() -> dict:
    """A small FHIR-shaped Patient. Synthetic; no real person."""
    return {
        "resourceType": "Patient",
        "id": "example-1",
        "name": [{"family": "Rivera", "given": ["Ana", "Lucia"]}],
        "gender": "female",
        "birthDate": "1984-03-09",
    }
