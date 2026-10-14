"""The examples in ``examples/from_answers/`` run, and their README lists them (plan-A step 6).

Each script is run as ``__main__`` in this process, so its own checks — the version with
``nestpath`` and the one without agree where they should — are part of the suite; a script that
needs pandas is skipped when pandas is not installed. The README's table is written by hand, and
the last test keeps it in step with the folder: one row per script, naming the script's answer,
linking the archive folder its docstring links, and saying what the first line of its docstring
says.
"""

from __future__ import annotations

import ast
import re
import runpy
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "from_answers"
SCRIPTS = sorted(EXAMPLES.glob("*.py"))
ARCHIVE = "https://github.com/fwSara95h/stackoverflow-driftr/tree/main/"
ROW = re.compile(
    r"\| \[(?P<script>\d+\.py)\]\((?P=script)\) \| (?P<answer>\d+) "
    rf"\| \[[^]]+\]\((?P<folder>{re.escape(ARCHIVE)}[^)]+)\) "
    r"\| (?P<shows>[^|]+?) \|"
)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.stem)
def test_example_runs(script: Path, capsys: pytest.CaptureFixture[str]) -> None:
    try:
        runpy.run_path(str(script), run_name="__main__")
    except ModuleNotFoundError as error:
        if error.name == "pandas":
            pytest.skip("needs the pandas extra")
        raise
    assert capsys.readouterr().out  # every example prints its result


def test_readme_table_matches_the_scripts() -> None:
    readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")
    table = [line for line in readme.splitlines() if line.startswith("| [")]
    rows = {}
    for line in table:
        match = ROW.fullmatch(line)
        assert match, f"malformed row: {line}"
        assert match["script"] not in rows, f"listed twice: {match['script']}"
        rows[match["script"]] = match
    assert sorted(rows) == [script.name for script in SCRIPTS]
    for script in SCRIPTS:
        row = rows[script.name]
        docstring = ast.get_docstring(ast.parse(script.read_text(encoding="utf-8")))
        assert docstring, f"{script.name} has no docstring"
        assert row["answer"] == script.stem
        assert docstring.splitlines()[0] == f"{row['shows']} (answer {row['answer']})."
        assert row["folder"] in docstring
