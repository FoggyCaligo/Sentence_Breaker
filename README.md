# Sentence_Breaker

입력된 문자의 연속 경로를 SQLite에 누적하고, 과거 문장 경로와 일치하는 구간을 이용해 텍스트를 분할하는 Python 패키지임. 공백과 문장부호도 문자 경로에 포함됨.

## 설치

```bash
pip install .
```

## 사용법

```python
from sentence_breaker import segment_text

segments = segment_text("엄마가 아이를 안는다.")
print(segments)
```

반복 처리에는 그래프 인스턴스를 재사용할 수 있음.

```python
from sentence_breaker import LanguageGraph

graph = LanguageGraph()
try:
    print(graph.segment_text("엄마"))
    print(graph.segment_text("엄마가 아이를 안는다."))
finally:
    graph.close()
```

CLI 실행:

```bash
sentence-breaker "엄마가 아이를 안는다."
```

## 데이터베이스

기본 DB 경로는 설치된 패키지의 `src/sentence_breaker/sentence_breaker.sqlite3`에 해당하는 `sentence_breaker.sqlite3` 파일임. 설치 방식에 따라 실제 패키지 디렉터리는 달라질 수 있음.

기존 `lang_graph.db`의 데이터를 그대로 이전한 DB를 사용하며, 매번 입력을 처리한 후 새 문장 경로가 DB에 누적됨.

별도 경로를 사용하려면 `segment_text(text, db_path=...)` 또는 `LanguageGraph(db_path=...)`를 지정하거나, CLI에서 `--db` 옵션을 사용할 수 있음.

DB 스키마는 `alph_nodes`, `sentence_layers`, `alph_links`를 사용함. 최초 생성 및 연결 시 필요한 테이블/인덱스를 확인함.

**주의:** 기본 DB가 패키지 내부에 있으므로 설치 경로에 쓰기 권한이 필요함. MAI와 동일한 누적 데이터를 공유하려면 MAI도 동일한 DB 파일 경로를 명시하도록 구성해야 함.

## English

Sentence_Breaker segments character sequences using previously observed sentence paths stored in SQLite. Each input is added to the graph after segmentation.

Install with `pip install .`. Import `segment_text` or `LanguageGraph` from `sentence_breaker`, or invoke `sentence-breaker "some text"` in a terminal.

The default database is `sentence_breaker.sqlite3` in the installed package directory, migrated without changing the data from the previous `lang_graph.db`. Override it with `db_path` or the CLI `--db` option. The installation location must be writable.
