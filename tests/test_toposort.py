"""Тесты для топологической сортировки."""

import pytest

from src.graph import DependencyGraph
from src.toposort import CycleDetectedError, topological_sort

EXPECTED_LEN = 4


def _make_graph(edges: dict[str, list[str]]) -> DependencyGraph:
    """Создаёт граф из словаря зависимостей."""
    graph = DependencyGraph()
    for node, children in edges.items():
        graph.add_node(node, "1.0")
        for child in children:
            graph.add_node(child, "1.0")
    for node, children in edges.items():
        for child in children:
            graph.add_edge(node, child)
    return graph


class TestTopologicalSort:
    """Тесты алгоритма Кана."""

    def test_linear_order(self) -> None:
        """A зависит от B, B от C. Порядок загрузки: C, B, A."""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        order = topological_sort(graph)
        assert order == ["C", "B", "A"]

    def test_tree_order(self) -> None:
        """Древовидный граф. D загружается первым, A — последним."""
        graph = _make_graph({
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        })
        order = topological_sort(graph)
        assert order[0] == "D"
        assert order[-1] == "A"
        assert len(order) == EXPECTED_LEN

    def test_cycle_raises(self) -> None:
        """Цикл A -> B -> A вызывает ошибку."""
        graph = _make_graph({"A": ["B"], "B": ["A"]})
        with pytest.raises(CycleDetectedError):
            topological_sort(graph)
