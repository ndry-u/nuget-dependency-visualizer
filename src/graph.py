"""Построение графа зависимостей и обход в глубину (DFS)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

INFINITE_DEPTH = -1


class GraphError(Exception):
    """Ошибка работы с графом."""


@dataclass
class GraphNode:
    """Узел графа зависимостей.

    Attributes:
        name: имя пакета.
        version: версия пакета.
        children: список имён пакетов, от которых зависит данный.
    """

    name: str
    version: str
    children: list[str] = field(default_factory=list)


class DependencyGraph:
    """Граф зависимостей с поддержкой DFS без рекурсии."""

    def __init__(self) -> None:
        """Создаёт пустой граф."""
        self.nodes: dict[str, GraphNode] = {}

    def add_node(self, name: str, version: str) -> None:
        """Добавляет узел, если его ещё нет.

        Args:
            name: имя пакета.
            version: версия.
        """
        key = name.lower()
        if key not in self.nodes:
            self.nodes[key] = GraphNode(name=name, version=version)

    def add_edge(self, parent: str, child: str) -> None:
        """Добавляет связь parent -> child.

        Args:
            parent: имя родительского пакета.
            child: имя дочернего пакета.
        """
        parent_key = parent.lower()
        child_key = child.lower()
        if parent_key not in self.nodes:
            raise GraphError(f"Родительский узел не найден: {parent}")
        if child_key not in self.nodes:
            raise GraphError(f"Дочерний узел не найден: {child}")

        parent_children = [
            c.lower() for c in self.nodes[parent_key].children
        ]
        if child_key not in parent_children:
            self.nodes[parent_key].children.append(child)

    def dfs_traversal(
        self,
        root_name: str,
        max_depth: int,
        fetch_children: Callable[[str], list[str]],
    ) -> list[GraphNode]:
        """Обходит граф в глубину без рекурсии.

        Args:
            root_name: имя корневого пакета.
            max_depth: максимальная глубина (-1 = бесконечно).
            fetch_children: функция, возвращающая список дочерних имён
                для пакета (для ленивой загрузки).

        Returns:
            Список узлов в порядке обхода (без дубликатов).

        Raises:
            GraphError: если корневой пакет не найден.
        """
        root_key = root_name.lower()
        if root_key not in self.nodes:
            raise GraphError(f"Корневой пакет не найден: {root_name}")

        visited: set[str] = set()
        order: list[GraphNode] = []
        stack: list[tuple[str, int]] = [(root_key, 0)]

        while stack:
            current_key, current_depth = stack.pop()

            if current_key in visited:
                continue

            visited.add(current_key)
            node = self.nodes[current_key]
            order.append(node)

            if max_depth != INFINITE_DEPTH and current_depth >= max_depth:
                continue

            children_names = fetch_children(node.name)

            for child_name in children_names:
                child_key = child_name.lower()
                if child_key not in self.nodes:
                    self.add_node(child_name, version="unknown")
                self.add_edge(node.name, child_name)

            for child_name in reversed(children_names):
                child_key = child_name.lower()
                if child_key not in visited:
                    stack.append((child_key, current_depth + 1))

        return order
