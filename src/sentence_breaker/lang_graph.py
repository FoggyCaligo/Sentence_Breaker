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

CREATE TABLE IF NOT EXISTS seq_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    source_alph TEXT NOT NULL,
    target_alph TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_alph) REFERENCES alph_nodes(alph),
    FOREIGN KEY (target_alph) REFERENCES alph_nodes(alph)
);

CREATE INDEX IF NOT EXISTS idx_seq_edges_input_position
ON seq_edges (input_id, position);
"""


def get_default_db_path() -> Path:
    candidates = [
        Path.home() / ".sentence_breaker",
        Path.cwd() / ".sentence_breaker",
    ]
    for base_dir in candidates:
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
            return base_dir / "lang_graph.db"
        except OSError:
            continue
    raise OSError("Could not create a writable .sentence_breaker directory.")


@dataclass(slots=True)
class SegmentChoice:
    segment: str
    next_index: int
    score: int
    piece_count: int


class LanguageGraph:
    """Character-path language graph that returns segment lists."""

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

        segments = self._segment_from_history(normalized)
        self._ingest(normalized)
        return segments

    def _segment_from_history(self, text: str) -> list[str]:
        best: list[SegmentChoice | None] = [None] * (len(text) + 1)
        best[len(text)] = SegmentChoice("", len(text), 0, 0)

        for start in range(len(text) - 1, -1, -1):
            fallback = best[start + 1]
            assert fallback is not None

            best_choice = SegmentChoice(
                segment=text[start],
                next_index=start + 1,
                score=fallback.score,
                piece_count=fallback.piece_count + 1,
            )

            for end in range(start + 2, len(text) + 1):
                piece = text[start:end]
                count = self._count_substring_occurrences(piece)
                if count == 0:
                    continue

                remainder = best[end]
                assert remainder is not None
                candidate = SegmentChoice(
                    segment=piece,
                    next_index=end,
                    score=remainder.score + (len(piece) * count),
                    piece_count=remainder.piece_count + 1,
                )

                if candidate.score > best_choice.score:
                    best_choice = candidate
                    continue
                if candidate.score < best_choice.score:
                    continue

                if len(candidate.segment) > len(best_choice.segment):
                    best_choice = candidate
                    continue
                if len(candidate.segment) < len(best_choice.segment):
                    continue

                if candidate.piece_count < best_choice.piece_count:
                    best_choice = candidate

            best[start] = best_choice

        segments: list[str] = []
        index = 0
        while index < len(text):
            choice = best[index]
            assert choice is not None
            segments.append(choice.segment)
            index = choice.next_index
        return segments

    def _count_substring_occurrences(self, piece: str) -> int:
        if len(piece) < 2:
            return 0

        input_ids = [
            row["input_id"]
            for row in self.conn.execute(
                "SELECT DISTINCT input_id FROM seq_edges ORDER BY input_id"
            ).fetchall()
        ]
        if not input_ids:
            return 0

        target_chars = list(piece)
        count = 0
        for input_id in input_ids:
            rows = self.conn.execute(
                """
                SELECT position, source_alph, target_alph
                FROM seq_edges
                WHERE input_id = ?
                ORDER BY position
                """,
                (input_id,),
            ).fetchall()
            if not rows:
                continue

            chars = [rows[0]["source_alph"]]
            chars.extend(row["target_alph"] for row in rows)
            for start in range(0, len(chars) - len(target_chars) + 1):
                if chars[start:start + len(target_chars)] == target_chars:
                    count += 1
        return count

    def _ingest(self, text: str) -> None:
        alphs = list(text)
        self.conn.executemany(
            "INSERT OR IGNORE INTO alph_nodes(alph) VALUES (?)",
            ((alph,) for alph in alphs),
        )

        input_id = f"input-{uuid.uuid4()}"
        self.conn.executemany(
            """
            INSERT INTO seq_edges(input_id, position, source_alph, target_alph)
            VALUES (?, ?, ?, ?)
            """,
            (
                (input_id, position, alphs[position], alphs[position + 1])
                for position in range(len(alphs) - 1)
            ),
        )
        self.conn.commit()


def segment_text(text: str, db_path: str | Path | None = None) -> list[str]:
    graph = LanguageGraph(db_path=db_path)
    try:
        return graph.segment_text(text)
    finally:
        graph.close()
