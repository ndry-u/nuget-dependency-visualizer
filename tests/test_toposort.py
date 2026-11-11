"""Тесты для топологической сортировки."""

import pytest

from src.graph import DependencyGraph
from src.toposort import CycleDetectedError, topological_sort


def _make_graph(edges: dict[str, list[str]]) -> DependencyGraph:
    """Создаёт граф. edges: {'A': ['B']} = A зависит от B."""
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
        """A зависит от B, B от C.

        Порядок загрузки: C, B, A.
        """
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        order = topological_sort(graph)
        assert order == ["C", "B", "A"]

    def test_tree_order(self) -> None:
        """Древовидный граф."""
        graph = _make_graph({
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        })
        order = topological_sort(graph)
        # D — самый глубокий, загружается первым.
        # A — корень, загружается последним.
        assert order[0] == "D"
        assert order[-1] == "A"
        assert len(order) == 4

    def test_cycle_raises(self) -> None:
        """Цикл A -> B -> A вызывает ошибку."""
        graph = _make_graph({"A": ["B"], "B": ["A"]})
        with pytest.raises(CycleDetectedError):
            topological_sort(graph)
