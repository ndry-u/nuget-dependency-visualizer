"""Парсер тестового репозитория."""

from __future__ import annotations

from pathlib import Path

SEPARATOR = ":"


class RepoParseError(Exception):
    """Ошибка чтения тестового репозитория."""


def load_test_repo(path: str) -> dict[str, list[str]]:
    """Загружает граф из текстового файла.

    Формат строки: `A: B C` — пакет A зависит от B и C.
    Пробел после двоеточия опционален (можно и `A:B C`).

    Args:
        path: путь к файлу.

    Returns:
        Словарь {имя_пакета: [список_зависимостей]}.

    Raises:
        RepoParseError: если файл не найден или формат некорректен.
    """
    repo_path = Path(path)
    if not repo_path.exists():
        raise RepoParseError(
            f"Файл тестового репозитория не найден: {path}"
        )

    graph: dict[str, list[str]] = {}
    text = repo_path.read_text(encoding="utf-8")

    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if SEPARATOR not in line:
            raise RepoParseError(
                f"Строка {line_no}: ожидается формат 'A: B C'"
            )

        name, deps_str = line.split(SEPARATOR, 1)
        name = name.strip()
        if not name:
            raise RepoParseError(
                f"Строка {line_no}: пустое имя пакета"
            )

        deps = [d.strip() for d in deps_str.split() if d.strip()]
        graph[name] = deps

    return graph
