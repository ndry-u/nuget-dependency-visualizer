"""Топологическая сортировка для получения порядка загрузки."""

from __future__ import annotations

from src.graph import DependencyGraph, GraphError


class CycleDetectedError(GraphError):
    """Ошибка: в графе обнаружен цикл."""


def _count_in_degrees(graph: DependencyGraph) -> dict[str, int]:
    """Считает степень входа для каждого пакета.

    Args:
        graph: граф зависимостей.

    Returns:
        Словарь {имя_пакета: количество_зависимостей}.
    """
    in_degree: dict[str, int] = {}
    for key, node in graph.nodes.items():
        in_degree[key] = len(node.children)
    return in_degree


def _process_queue(
    graph: DependencyGraph,
    in_degree: dict[str, int],
    queue: list[str],
) -> list[str]:
    """Обрабатывает очередь и собирает порядок загрузки.

    Args:
        graph: граф зависимостей.
        in_degree: текущие степени входа пакетов.
        queue: начальная очередь (пакеты с нулевой степенью).

    Returns:
        Список имён пакетов в порядке загрузки.
    """
    result: list[str] = []

    while queue:
        current = queue.pop(0)
        result.append(graph.nodes[current].name)

        for node in graph.nodes.values():
            for child_name in node.children:
                if child_name.lower() == current:
                    parent_key = node.name.lower()
                    if parent_key in in_degree:
                        in_degree[parent_key] -= 1
                        if in_degree[parent_key] == 0:
                            queue.append(parent_key)

    return result


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
    in_degree = _count_in_degrees(graph)
    queue = [k for k, v in in_degree.items() if v == 0]

    result = _process_queue(graph, in_degree, queue)

    if len(result) != len(graph.nodes):
        raise CycleDetectedError(
            "В графе обнаружен цикл, топологическая сортировка невозможна"
        )

    return result
