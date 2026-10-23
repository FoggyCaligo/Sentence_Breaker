from pathlib import Path

from sentence_breaker import get_default_db_path


def test_default_db_filename() -> None:
    assert get_default_db_path().name == "sentence_breaker.sqlite3"


def test_default_db_is_in_package_directory() -> None:
    assert get_default_db_path().parent == Path(__import__("sentence_breaker").__file__).resolve().parent
