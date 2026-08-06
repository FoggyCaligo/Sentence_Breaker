from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lang_graph import get_default_db_path, segment_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Segment text with Sentence_Breaker's language graph."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to segment. If omitted, interactive input is used.",
    )
    parser.add_argument(
        "--db",
        default=str(get_default_db_path()),
        help="SQLite DB path to use.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    text = args.text if args.text is not None else input("text> ")
    segments = segment_text(text, db_path=Path(args.db))
    print(json.dumps(segments, ensure_ascii=False))


if __name__ == "__main__":
    main()
