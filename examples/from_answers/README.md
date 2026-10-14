# Examples from the archived answers

Each script takes one question I answered on Stack Overflow and solves it again with `nestpath`, beside a version without it: my answer's own approach, rewritten in today's style, or, where the answer used a helper that `nestpath` now replaces, the plain idiom a reader would reach for instead (`pandas.json_normalize`, mostly). Where the plain version is just as good, the script's docstring says so. The question, my answer as posted and the other answers are archived with their attribution in [stackoverflow-driftr](https://github.com/fwSara95h/stackoverflow-driftr), and each docstring links the folder. The data in every script is invented in the shape of the question's; none of it is the asker's.

Run one with `python examples/from_answers/<answer>.py`: it prints its result and checks that the two versions agree where they should. `tests/test_examples.py` runs them all, so CI does too, and keeps this table in step with the folder. Scripts that build a DataFrame need the `pandas` extra.

| Script | Answer | Question (archived) | What it shows |
| --- | --- | --- | --- |
| [75466591.py](75466591.py) | 75466591 | [Dealing with optional python dictionary fields](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/70988817-dealing-with-optional-python-dictionary-fields) | Optional nested fields read with a default |
| [75205202.py](75205202.py) | 75205202 | [Applying keys sequentially to a dict from a list](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A1-building-updating-and-reading-dicts-key-path/75197965-applying-keys-sequentially-to-a-dict-from-a-list) | A spec of key paths, with defaults, applied to each scraped record |
| [75934500.py](75934500.py) | 75934500 | [How to flatten list of dictionaries](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A2-flattening-and-walking-nested-structures/75934227-how-to-flatten-list-of-dictionaries) | A tree of lists and dicts flattened to one list per top-level key |
| [75196824.py](75196824.py) | 75196824 | [Convert nested dict to dataframe, syntax error?](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A5-pandas-building-and-reshaping-dataframes/75184221-convert-nested-dict-to-dataframe-syntax-error) | Nested metric results to one DataFrame row each |
| [75911088.py](75911088.py) | 75911088 | [sort a list that contains dictionaries with same key](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75907811-sort-a-list-that-contains-dictionaries-with-same-key) | A list of dicts sorted by one nested key, ties broken by the next |
| [75928321.py](75928321.py) | 75928321 | [How to group the same values into same key?](https://github.com/fwSara95h/stackoverflow-driftr/tree/main/A3-reshaping-lists-of-dicts-sort-group-dedupe-m/75927144-how-to-group-the-same-values-into-same-key) | Rows grouped by one nested field and then another |

> [!NOTE]
> **75934500.** The question asked for one flat list per top-level key with each dict key in it, ahead of the items it holds; my answer's generator walked only the values, so the lists it printed left the keys out — four of the twelve items in the question's first list. The script prints both: the values, as the answer gave them, and the question's lists, keys included.
