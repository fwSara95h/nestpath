# Examples from the archived answers

Each script takes one question I answered on Stack Overflow and solves it again with `nestpath`, beside a version without it: my answer's own approach, rewritten in today's style, or, where the answer used a helper that `nestpath` now replaces, the plain idiom a reader would reach for instead (`pandas.json_normalize`, mostly). Where the plain version is just as good, the script's docstring says so. The question, my answer as posted and the other answers are archived with their attribution in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr), and each docstring links the folder. The data in every script is invented in the shape of the question's; none of it is the asker's.

Run one with `python examples/from_answers/<answer>.py`: it prints its result and checks that the two versions agree where they should. `tests/test_examples.py` runs them all, so CI does too, and keeps this table in step with the folder. Scripts that build a DataFrame need the `pandas` extra.

| Script | Answer | Question (archived) | What it shows |
| --- | --- | --- | --- |
| [75466591.py](75466591.py) | 75466591 | [Dealing with optional python dictionary fields](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/70988817-dealing-with-optional-python-dictionary-fields) | Optional nested fields read with a default |
