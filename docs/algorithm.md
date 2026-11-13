# Sentence_Breaker 알고리즘·재현 조건

Sentence_Breaker는 [FoggyCaligo/Sentence_Breaker](https://github.com/FoggyCaligo/Sentence_Breaker)에서 개발한 독립 Python 패키지다. 프로젝트 작성자 표기는 `pyproject.toml`의 `bigla`이며, MAI나 MCP_memorizer에 포함된 부속 알고리즘이 아니다.

이 문서는 **현재 구현을 설명하는 재현 가이드**다. 루트의 [LANG_GRAPH_LAYER_DESIGN.md](../LANG_GRAPH_LAYER_DESIGN.md)는 발전 방향과 선택적 기능까지 다루는 설계 기록이며, 그 안의 `bundle_memory`·경계 일관성 점수 등을 현재 기능으로 간주하지 않는다.

## 목적과 구성

과거 입력 문장의 **문자 간 연속 경로**를 SQLite에 누적하고, 새 문장과 경로가 일치하는 구간들을 이용해 문장을 분해한다. 공백과 문장부호도 문자 단위로 취급한다. 자연어 형태소 분석기나 모델 토크나이저와는 다른 구조다.

기존 이력으로 **먼저 분해한 후**, 현재 문장의 문자 경로를 누적한다. 따라서 실행 이력과 DB 내용이 같지 않으면 같은 입력도 다른 결과를 낼 수 있다.

## SQLite 테이블

| 테이블 | 주된 필드 | 역할 |
|---|---|---|
| `alph_nodes` | `alph`, 생성 시각 | 문자 셀 |
| `sentence_layers` | `sentence_id`, `char_length`, 생성 시각 | 입력 문장마다 한 개의 경로 층 |
| `alph_links` | `source_alph`, `target_alph`, `sentence_id`, `position`, 생성 시각 | 해당 문장 층·위치의 인접 문자 연결 |

쌍별 검색과 층·위치 검색을 위한 색인을 둔다. 기존 문자 셀은 재사용할 수 있지만 **새 입력의 문자 연결은 새 층의 기록**으로 저장한다. 입력 층 식별자는 `sentence-<UUID>` 형식일 수 있으며, 연속된 정수일 필요는 없다.

## 문자 경로 비교

새 입력을 `c[0], c[1], …, c[n-1]`로 분해한다.

1. 각 위치 `i`에서 `c[i] → c[i+1]`에 해당하는 저장 연결을 조회한다.
2. 해당 연결의 `(sentence_id, position)`을 `step_matches[i]`에 모은다.
3. 어떤 `[start,end)` 구간이 과거 문장에서 이어졌는지 확인할 때는 단순 문자 쌍 일치만 보지 않는다.
4. 이전 단계의 `(sentence_id, position)`과 다음 단계의 `(sentence_id, position+1)`이 이어지는 상태만 남긴다.
5. 마지막까지 살아남은 경로 상태 수를 해당 구간의 지원 수로 계산한다.

서로 다른 과거 문장의 문자 쌍을 임의로 이어 붙이는 것은 허용하지 않는다. 하나의 문장에 같은 부분 문자열이 여러 위치에 있다면 지원 상태도 여러 개일 수 있다.

## 최종 분해 선택

입력의 끝에서 시작 방향으로 동적 계획법을 적용한다. 한 글자 조각은 기본 후보이며, 지원되는 길이 2 이상의 구간을 추가 후보로 비교한다.

구간 길이를 `L`, 살아남은 경로 지원 수를 `K`라 할 때 추가 점수는 `K × L`이다. 각 후보의 뒤쪽 분해 결과 점수를 더해 최종 분해를 선택한다. 기존 MAI에서 분리해 보존한 구현 설명의 비교 순서는 다음과 같다.

1. 전체 지원 점수가 더 큰 분해
2. 지원을 받은 문자 수가 더 많은 분해
3. 현재 후보 조각의 길이가 더 긴 분해
4. 전체 조각 수가 더 적은 분해

완전히 같으면 현재 선택을 유지한다. 후보 탐색 순서도 동점의 재현성에 영향을 줄 수 있다. 변경 시에는 반드시 현재 `src/sentence_breaker/lang_graph.py` 구현과 비교해야 한다.

## 학습 순서와 예시

첫 `엄마` 입력에서는 과거 연결이 없는 DB라면 문자별로 분해될 수 있다. 그 입력의 경로가 저장되고 나서 `엄마가`가 들어오면 과거의 `엄마`가 두 글자 후보로 지원될 수 있다. 최종 결과는 다른 누적 경로의 지원 수에 따라 달라진다.

분해 **이후** 현재 입력의 층을 저장하지 않으면 최초 입력이 스스로를 지원하는 문제가 생길 수 있다. 누적 DB의 차이와 입력 순서는 재현 실험에 반드시 기록한다.

## API와 DB 경로

```python
from sentence_breaker import LanguageGraph, segment_text

segments = segment_text("엄마가 아이를 안는다.", db_path="./sentence_breaker.sqlite3")
graph = LanguageGraph(db_path="./sentence_breaker.sqlite3")
try:
    print(graph.segment_text("엄마"))
finally:
    graph.close()
```

별도 `db_path`를 지정하지 않으면 설치된 패키지의 기본 DB를 사용할 수 있다. 다른 프로그램과 기존 분해 이력을 공유하려면 **같은 DB 경로**를 명시해야 한다. 별도 앱이 누적 DB를 자동 복제하는 기능으로 오해하면 안 된다.

## MCP_memorizer와 MAI의 책임 경계

- Sentence_Breaker: 문자 경로 알고리즘·DB·분해 API의 원본 구현 및 문서
- [MCP_memorizer](https://github.com/FoggyCaligo/MCP_memorizer): 분해 조각을 Concept 그래프·검색 색인에 연결하는 어댑터
- [MAI](https://github.com/FoggyCaligo/MAI_MyAI_sllm): 해당 메모리 패키지 호출, 사용자별 DB 경로·작업 생명주기

## 성능 및 구현 유의사항

현재 동적 계획법과 과거 경로 지원 수 계산은 긴 입력에서 비용이 늘 수 있다. 색인·캐시·경로 확장 최적화를 고려하더라도 **지원 수, 동점, 입력 후 학습**의 의미를 바꾸지 않고 회귀 검증해야 한다. 루트 설계 기록에 제안된 선택적 경계 점수나 `bundle_memory` 테이블이 이미 구현됐다고 가정하지 않는다.
