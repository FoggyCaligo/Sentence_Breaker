# Sentence_Breaker

## 한국어

### 기능소개


사람의 업데이트 없이 바로 신조어를 분해할 수 있는 문장 분해 패키지.


### 상세설명

`Sentence_Breaker`는 문장을 나눌 때, 미리 만들어 둔 사전만 믿고 자르지 않습니다. 대신 사람들이 실제로 입력한 글자 흐름을 기억해 두었다가, 다음 문장을 볼 때 "전에 본 적 있는 묶음"을 다시 찾아냅니다. 그래서 새로 생긴 말이나 처음 보는 표현도, 한 번 단어처럼 들어오면 다음부터는 하나의 묶음으로 다루기 쉬워집니다.

### 원리

- 문장을 먼저 글자 단위로 봅니다. 공백과 마침표도 함께 봅니다.
- 예를 들어 `"엄마"`가 한 번 들어오면, `"엄"` 다음에 `"마"`가 이어졌다는 흐름을 기억합니다.
- 나중에 `"엄마가"`가 들어오면, 이미 알고 있는 `"엄마"` 부분을 먼저 눈에 띄는 묶음으로 봅니다.
- 이렇게 입력이 쌓일수록 자주 같이 나온 글자 묶음은 더 또렷한 단어 후보가 됩니다.
- 그래서 결과는 `["엄마", "가", " ", "아이", ...]`처럼 나뉜 리스트로 나옵니다.

### 사용법

설치:

```bash
pip install .
```

파이썬에서 사용:

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

재사용 가능한 그래프 인스턴스로 사용:

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
print(graph.segment_text("엄마"))
print(graph.segment_text("엄마가 아이를 안는다."))
graph.close()
```

터미널에서 사용:

```bash
sentence-breaker "엄마가 아이를 안는다."
```

또는:

```bash
python -m sentence_breaker.cli "엄마가 아이를 안는다."
```

기본 DB 경로:

```text
./src/sentence_breaker/lang_graph.db
```

원하면 `db_path` 인자로 직접 경로를 지정할 수도 있습니다.

---

---

## English

### One-line Feature Title

A sentence segmentation package that can split neologisms immediately without human updates.

### Description

`Sentence_Breaker` does not split sentences by trusting only a prebuilt dictionary. Instead, it remembers the character flow of what people actually typed before, and then looks for familiar bundles in later text. Because of that, even a new word can start being treated as one bundle after it has appeared once as a word.

### Principle

- The package first looks at a sentence as a stream of characters. Spaces and punctuation are included too.
- For example, if `"엄마"` appears once, the system remembers that `"엄"` was followed by `"마"`.
- Later, when it sees `"엄마가"`, it can notice that `"엄마"` is already a familiar bundle.
- As more text is collected, character bundles that often appear together become clearer word candidates.
- So the final result comes out as a split list such as `["엄마", "가", " ", "아이", ...]`.

### Usage

Install:

```bash
pip install .
```

Use from Python:

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

Use with a reusable graph instance:

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
print(graph.segment_text("엄마"))
print(graph.segment_text("엄마가 아이를 안는다."))
graph.close()
```

Use from the terminal:

```bash
sentence-breaker "엄마가 아이를 안는다."
```

Or:

```bash
python -m sentence_breaker.cli "엄마가 아이를 안는다."
```

Default DB path:

```text
./src/sentence_breaker/lang_graph.db
```

You can also override the location with the `db_path` argument.

---

## 한국어

### 기능 소개

`Sentence_Breaker`는 문장을 일반적인 토큰 규칙이 아니라 문자 경로 누적 이력으로 잘라서 `segment list`로 반환하는 파이썬 패키지입니다.

### 기능 사용법

설치:

```bash
pip install .
```

파이썬에서 사용:

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

재사용 가능한 그래프 인스턴스로 사용:

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
print(graph.segment_text("엄마"))
print(graph.segment_text("엄마가 아이를 안는다."))
graph.close()
```

터미널에서 사용:

```bash
sentence-breaker "엄마가 아이를 안는다."
```

또는:

```bash
python -m sentence_breaker.cli "엄마가 아이를 안는다."
```

기본 DB 경로:

```text
~/.sentence_breaker/lang_graph.db
```

해당 경로에 쓸 수 없으면 아래로 자동 fallback 됩니다.

```text
./.sentence_breaker/lang_graph.db
```

원하면 `db_path` 인자로 직접 경로를 지정할 수도 있습니다.

### 원리

- 입력 문장을 공백과 문장부호를 포함한 글자 흐름으로 본다.
- 각 입력은 SQLite 안에 하나의 `input_id`를 가진 문자 경로로 누적 저장된다.
- 다음 입력이 들어오면, 과거에 반복된 부분 문자열이 더 강한 segment 후보가 된다.
- 그 결과로 `["엄마", "가", " ", "아이", ...]` 같은 리스트를 반환한다.

---

## English

### One-line Description

`Sentence_Breaker` is a Python package that segments text by using accumulated character-path history instead of a conventional tokenization rule set.

### Usage

Install:

```bash
pip install .
```

Use from Python:

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

Use with a reusable graph instance:

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
print(graph.segment_text("엄마"))
print(graph.segment_text("엄마가 아이를 안는다."))
graph.close()
```

Use from the terminal:

```bash
sentence-breaker "엄마가 아이를 안는다."
```

Or:

```bash
python -m sentence_breaker.cli "엄마가 아이를 안는다."
```

Default DB path:

```text
~/.sentence_breaker/lang_graph.db
```

If that location is not writable, it automatically falls back to:

```text
./.sentence_breaker/lang_graph.db
```

You can also override the location with the `db_path` argument.

### Principle

- The package treats input as a character stream, including spaces and punctuation.
- Each input is stored in SQLite as its own character path with a unique `input_id`.
- When a new input arrives, repeated substrings from earlier history become stronger segment candidates.
- The result is returned as a list such as `["엄마", "가", " ", "아이", ...]`.

---

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
