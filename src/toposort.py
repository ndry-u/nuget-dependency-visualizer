"""Топологическая сортировка для получения порядка загрузки."""

from __future__ import annotations

from src.graph import DependencyGraph, GraphError


class CycleDetectedError(GraphError):
    """Ошибка: в графе обнаружен цикл."""


def topological_sort(graph: DependencyGraph) -> list[str]:
    """Возвращает порядок загрузки пакетов (от листьев к корню).

    В нашем графе ребро A -> B означает, что A зависит от B.
    Для загрузки это значит, что B должен быть загружен раньше A.

    Args:
        graph: граф зависимостей.

    Returns:
        Список имён пакетов в порядке загрузки.

    Raises:
        CycleDetectedError: если в графе есть цикл.
    """
    # Степень входа: сколько зависимостей нужно загрузить перед этим пакетом.
    in_degree = {key: 0 for key in graph.nodes}

    for node in graph.nodes.values():
        in_degree[node.name.lower()] = len(node.children)

    # В очередь попадают пакеты, у которых нет зависимостей (листья).
    queue: list[str] = [k for k, v in in_degree.items() if v == 0]
    result: list[str] = []

    while queue:
        current = queue.pop(0)
        result.append(graph.nodes[current].name)

        # Убираем текущий узел. Для всех, кто от него зависел,
        # уменьшаем счётчик.
        for node in graph.nodes.values():
            for child_name in node.children:
                if child_name.lower() == current:
                    parent_key = node.name.lower()
                    if parent_key in in_degree:
                        in_degree[parent_key] -= 1
                        if in_degree[parent_key] == 0:
                            queue.append(parent_key)

    if len(result) != len(graph.nodes):
        raise CycleDetectedError(
            "В графе обнаружен цикл, топологическая сортировка невозможна"
        )

    return result
