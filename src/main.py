"""Точка входа приложения.

Этап 4: вывод порядка загрузки (топологическая сортировка).
"""

from __future__ import annotations

import argparse
import sys

from src.config import Config, ConfigError, format_config, load_config
from src.graph import DependencyGraph, GraphError
from src.nuget import NuGetError, fetch_dependencies
from src.test_repo import RepoParseError, load_test_repo
from src.toposort import CycleDetectedError, topological_sort

DEFAULT_CONFIG_PATH = "configs/config.yaml"


def build_parser() -> argparse.ArgumentParser:
    """Создаёт argparse-парсер."""
    parser = argparse.ArgumentParser(
        prog="nuget-graph",
        description="Визуализатор графа зависимостей NuGet",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default=DEFAULT_CONFIG_PATH,
        help="Путь к YAML-файлу конфигурации",
    )
    return parser


def _get_children_nuget(package: str, config: Config) -> list[str]:
    """Возвращает имена прямых зависимостей из NuGet."""
    try:
        version = (
            config.package_version
            if package.lower() == config.package_name.lower()
            else "latest"
        )
        if version == "latest":
            return []
        deps = fetch_dependencies(package, version, config.repository_url)
        return [d.name for d in deps]
    except NuGetError:
        return []


def _build_graph(config: Config) -> DependencyGraph:
    """Строит и заполняет граф зависимостей."""
    graph = DependencyGraph()
    graph.add_node(config.package_name, config.package_version)

    if config.test_mode:
        try:
            repo = load_test_repo(config.repository_url)
        except RepoParseError as error:
            print(f"Ошибка тестового репозитория: {error}", file=sys.stderr)
            raise SystemExit(1)

        def fetch_test(pkg_name: str) -> list[str]:
            return repo.get(pkg_name, [])

        for node, children in repo.items():
            graph.add_node(node, "test")
            for child in children:
                graph.add_node(child, "test")

        fetch_func = fetch_test
    else:
        def fetch_nuget(pkg_name: str) -> list[str]:
            return _get_children_nuget(pkg_name, config)

        fetch_func = fetch_nuget

    try:
        graph.dfs_traversal(config.package_name, config.max_depth, fetch_func)
    except GraphError as error:
        print(f"Ошибка графа: {error}", file=sys.stderr)
        raise SystemExit(1)

    return graph


def main(argv: list[str] | None = None) -> int:
    """Точка входа."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config_path)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return 1

    print(format_config(config))
    graph = _build_graph(config)

    if config.test_mode:
        print("\n[Тестовый режим]")
    else:
        print("\n[Реальный режим NuGet]")

    try:
        order = topological_sort(graph)
    except CycleDetectedError as error:
        print(f"Предупреждение: {error}", file=sys.stderr)
        print("Выводим порядок обхода DFS:")
        dfs_order = graph.dfs_traversal(
            config.package_name, config.max_depth, lambda x: []
        )
        order = [n.name for n in dfs_order]
    else:
        print("\nПорядок загрузки зависимостей (сначала листья):")
        for i, name in enumerate(order):
            print(f"  {i + 1}. {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
