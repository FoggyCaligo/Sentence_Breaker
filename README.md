# Sentence_Breaker

`Sentence_Breaker` is a Python package version of the `LANG_GRAPH` prototype from MACHI.

It stores character-path history in SQLite and returns a segment list for each new input.

## Install

```bash
pip install .
```

## Use from Python

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

You can also manage a reusable graph instance.

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
print(graph.segment_text("엄마"))
print(graph.segment_text("엄마가 아이를 안는다."))
graph.close()
```

## CLI

```bash
sentence-breaker "엄마가 아이를 안는다."
```

Or:

```bash
python -m sentence_breaker.cli "엄마가 아이를 안는다."
```

## Default DB location

By default, the package stores its DB here:

```text
~/.sentence_breaker/lang_graph.db
```

If that location is not writable, it falls back to:

```text
./.sentence_breaker/lang_graph.db
```

You can also override it by passing `db_path`.
