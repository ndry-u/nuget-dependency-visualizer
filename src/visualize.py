"""Визуализация графа зависимостей (D2 и ASCII-дерево)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.graph import DependencyGraph

D2_COMMAND = "d2"


class VisualizeError(Exception):
    """Ошибка визуализации графа."""


def generate_d2_code(graph: DependencyGraph) -> str:
    """Формирует текстовое представление графа на языке D2.

    Args:
        graph: граф зависимостей.

    Returns:
        Строка с кодом D2.
    """
    lines = ["direction: right"]
    for node in graph.nodes.values():
        if not node.children:
            lines.append(f'"{node.name}"')
        else:
            for child in node.children:
                lines.append(f'"{node.name}" -> "{child}"')
    return "\n".join(lines)


def render_png(d2_code: str, output_path: str) -> None:
    """Генерирует PNG-изображение из кода D2.

    Args:
        d2_code: исходный код D2.
        output_path: путь для сохранения PNG.

    Raises:
        VisualizeError: если d2 не установлен или произошла ошибка.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    d2_file = output.with_suffix(".d2")
    d2_file.write_text(d2_code, encoding="utf-8")

    try:
        subprocess.run(
            [D2_COMMAND, str(d2_file), str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise VisualizeError(
            "Утилита 'd2' не найдена. Установите её с https://d2lang.com"
        ) from error
    except subprocess.CalledProcessError as error:
        raise VisualizeError(
            f"Ошибка рендеринга D2: {error.stderr}"
        ) from error


def _build_tree_lines(
    graph: DependencyGraph,
    node_name: str,
    prefix: str,
    visited: set[str],
) -> list[str]:
    """Рекурсивно формирует строки ASCII-дерева."""
    key = node_name.lower()
    if key not in graph.nodes:
        return [f"{prefix}└── {node_name} (not found)"]

    if key in visited:
        return [f"{prefix}└── {node_name} (cycle)"]

    visited.add(key)
    node = graph.nodes[key]
    lines = [f"{prefix}{node.name}"]

    if not node.children:
        return lines

    for i, child in enumerate(node.children):
        is_last = i == len(node.children) - 1
        branch = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        child_lines = _build_tree_lines(
            graph, child, extension, visited
        )

        # Безопасное добавление отступа для первой строки
        first_child_line = child_lines[0].lstrip()
        lines.append(f"{prefix}{branch}{first_child_line}")

        # Добавляем остальные строки потомка как есть
        lines.extend(child_lines[1:])

    return lines


def generate_ascii_tree(graph: DependencyGraph, root_name: str) -> str:
    """Формирует ASCII-дерево зависимостей.

    Args:
        graph: граф зависимостей.
        root_name: имя корневого пакета.

    Returns:
        Строка с деревом.
    """
    root_key = root_name.lower()
    if root_key not in graph.nodes:
        raise VisualizeError(f"Пакет не найден: {root_name}")

    visited: set[str] = set()
    lines = [root_name]

    root_node = graph.nodes[root_key]
    for i, child in enumerate(root_node.children):
        is_last = i == len(root_node.children) - 1
        branch = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        child_lines = _build_tree_lines(
            graph, child, extension, visited
        )

        first_child_line = child_lines[0].lstrip()
        lines.append(f"{branch}{first_child_line}")
        lines.extend(child_lines[1:])

    return "\n".join(lines)
