from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS alph_nodes (
    alph TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sentence_layers (
    sentence_id TEXT PRIMARY KEY,
    char_length INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alph_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_alph TEXT NOT NULL,
    target_alph TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_alph) REFERENCES alph_nodes(alph),
    FOREIGN KEY (target_alph) REFERENCES alph_nodes(alph),
    FOREIGN KEY (sentence_id) REFERENCES sentence_layers(sentence_id)
);

CREATE INDEX IF NOT EXISTS idx_alph_links_pair
ON alph_links (source_alph, target_alph);

CREATE INDEX IF NOT EXISTS idx_alph_links_sentence_position
ON alph_links (sentence_id, position);

CREATE INDEX IF NOT EXISTS idx_alph_links_source_sentence
ON alph_links (source_alph, sentence_id);
"""


PathState = tuple[str, int]


def get_default_db_path() -> Path:
    package_file = Path(__file__).resolve()
    return package_file.parent / "sentence_breaker.sqlite3"


@dataclass(slots=True)
class SegmentChoice:
    segment: str
    next_index: int
    support_score: int
    supported_chars: int
    piece_count: int


class LanguageGraph:
    """Character-path language graph with sentence-layer filtering."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def segment_text(self, text: str) -> list[str]:
        normalized = str(text)
        if not normalized:
            return []

        chars = list(normalized)
        step_matches = self._build_step_matches(chars)
        segments = self._segment_from_layer_matches(chars, step_matches)
        self._ingest(chars)
        return segments

    def _build_step_matches(self, chars: list[str]) -> list[set[PathState]]:
        step_matches: list[set[PathState]] = []
        for index in range(len(chars) - 1):
            rows = self.conn.execute(
                """
                SELECT sentence_id, position
                FROM alph_links
                WHERE source_alph = ? AND target_alph = ?
                """,
                (chars[index], chars[index + 1]),
            ).fetchall()
            step_matches.append({
                (str(row["sentence_id"]), int(row["position"]))
                for row in rows
            })
        return step_matches

    def _segment_from_layer_matches(
        self,
        chars: list[str],
        step_matches: list[set[PathState]],
    ) -> list[str]:
        text_length = len(chars)
        best: list[SegmentChoice | None] = [None] * (text_length + 1)
        best[text_length] = SegmentChoice("", text_length, 0, 0, 0)

        for start in range(text_length - 1, -1, -1):
            fallback = best[start + 1]
            assert fallback is not None

            best_choice = SegmentChoice(
                segment=chars[start],
                next_index=start + 1,
                support_score=fallback.support_score,
                supported_chars=fallback.supported_chars,
                piece_count=fallback.piece_count + 1,
            )

            for end in range(start + 2, text_length + 1):
                support_count = self._support_count(step_matches, start, end)
                if support_count == 0:
                    continue

                remainder = best[end]
                assert remainder is not None
                span_length = end - start
                candidate = SegmentChoice(
                    segment="".join(chars[start:end]),
                    next_index=end,
                    support_score=remainder.support_score + (support_count * span_length),
                    supported_chars=remainder.supported_chars + span_length,
                    piece_count=remainder.piece_count + 1,
                )

                if self._is_better(candidate, best_choice):
                    best_choice = candidate

            best[start] = best_choice

        segments: list[str] = []
        index = 0
        while index < text_length:
            choice = best[index]
            assert choice is not None
            segments.append(choice.segment)
            index = choice.next_index
        return segments

    def _support_count(
        self,
        step_matches: list[set[PathState]],
        start: int,
        end: int,
    ) -> int:
        if end - start < 2:
            return 0

        survivors = set(step_matches[start])
        if not survivors:
            return 0

        for step_index in range(start + 1, end - 1):
            next_matches = step_matches[step_index]
            if not next_matches:
                return 0

            advanced: set[PathState] = set()
            for sentence_id, position in survivors:
                candidate_state = (sentence_id, position + 1)
                if candidate_state in next_matches:
                    advanced.add(candidate_state)

            survivors = advanced
            if not survivors:
                return 0

        return len(survivors)

    def _is_better(self, candidate: SegmentChoice, current: SegmentChoice) -> bool:
        candidate_key = (
            candidate.support_score,
            candidate.supported_chars,
            len(candidate.segment),
            -candidate.piece_count,
        )
        current_key = (
            current.support_score,
            current.supported_chars,
            len(current.segment),
            -current.piece_count,
        )
        return candidate_key > current_key

    def _ingest(self, chars: list[str]) -> None:
        sentence_id = f"sentence-{uuid.uuid4()}"

        self.conn.executemany(
            "INSERT OR IGNORE INTO alph_nodes(alph) VALUES (?)",
            ((alph,) for alph in chars),
        )
        self.conn.execute(
            """
            INSERT INTO sentence_layers(sentence_id, char_length)
            VALUES (?, ?)
            """,
            (sentence_id, len(chars)),
        )

        if len(chars) >= 2:
            self.conn.executemany(
                """
                INSERT INTO alph_links(source_alph, target_alph, sentence_id, position)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (chars[position], chars[position + 1], sentence_id, position)
                    for position in range(len(chars) - 1)
                ),
            )

        self.conn.commit()


def segment_text(text: str, db_path: str | Path | None = None) -> list[str]:
    graph = LanguageGraph(db_path=db_path)
    try:
        return graph.segment_text(text)
    finally:
        graph.close()
