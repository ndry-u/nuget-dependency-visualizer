"""Тесты для графа зависимостей и DFS."""

import pytest

from src.graph import DependencyGraph, GraphError
from src.test_repo import RepoParseError, load_test_repo

SAMPLE_REPO = """A: B C
B: D
C: D E
D: F
E: F
F:
"""


def _make_graph() -> tuple[DependencyGraph, dict[str, list[str]]]:
    """Строит граф и словарь зависимостей из SAMPLE_REPO."""
    repo: dict[str, list[str]] = {}
    for line in SAMPLE_REPO.splitlines():
        line = line.strip()
        if not line:
            continue
        name, deps_str = line.split(":", 1)
        repo[name.strip()] = deps_str.strip().split()

    graph = DependencyGraph()
    for node, children in repo.items():
        graph.add_node(node, "1.0")
        for child in children:
            graph.add_node(child, "1.0")
    for node, children in repo.items():
        for child in children:
            graph.add_edge(node, child)
    return graph, repo


def _fetch_factory(repo: dict[str, list[str]]):
    """Возвращает функцию для получения зависимостей из словаря."""
    return lambda name: repo.get(name, [])


class TestDependencyGraph:
    """Тесты DFS-обхода графа."""

    def test_dfs_order_no_limits(self) -> None:
        """Обход без ограничения глубины проходит по всем узлам."""
        graph, repo = _make_graph()
        order = graph.dfs_traversal("A", -1, _fetch_factory(repo))
        names = [n.name for n in order]
        assert names[0] == "A"
        assert "F" in names
        assert len(names) == len(repo)

    def test_dfs_depth_limit(self) -> None:
        """Обход с ограничением глубины не идёт глубже."""
        graph, repo = _make_graph()
        order = graph.dfs_traversal("A", 1, _fetch_factory(repo))
        names = [n.name for n in order]
        assert "A" in names
        assert "B" in names
        assert "C" in names
        assert "D" not in names

    def test_cycle_handling(self) -> None:
        """Циклические зависимости не вызывают зависания."""
        graph = DependencyGraph()
        graph.add_node("A", "1.0")
        graph.add_node("B", "1.0")
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")

        repo = {"A": ["B"], "B": ["A"]}
        order = graph.dfs_traversal("A", -1, _fetch_factory(repo))
        assert len(order) == 2

    def test_unknown_root(self) -> None:
        """Несуществующий корень — ошибка."""
        graph, _ = _make_graph()
        with pytest.raises(GraphError):
            graph.dfs_traversal("Nope", -1, lambda name: [])


class TestTestRepo:
    """Тесты парсера тестового репозитория."""

    def test_load_valid(self, tmp_path) -> None:
        """Корректный файл парсится."""
        path = tmp_path / "repo.txt"
        path.write_text(SAMPLE_REPO, encoding="utf-8")
        repo = load_test_repo(str(path))
        assert repo["A"] == ["B", "C"]
        assert repo["F"] == []

    def test_load_invalid(self, tmp_path) -> None:
        """Строка без ':' — ошибка."""
        path = tmp_path / "repo.txt"
        path.write_text("invalid_line_without_colon", encoding="utf-8")
        with pytest.raises(RepoParseError):
            load_test_repo(str(path))

    def test_load_missing_file(self) -> None:
        """Несуществующий файл — ошибка."""
        with pytest.raises(RepoParseError):
            load_test_repo("nonexistent.txt")
