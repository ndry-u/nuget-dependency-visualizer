"""Точка входа приложения.

Этап 2: сбор прямых зависимостей пакета NuGet.
"""

from __future__ import annotations

import argparse
import sys

from src.config import ConfigError, format_config, load_config
from src.nuget import NuGetError, fetch_dependencies

DEFAULT_CONFIG_PATH = "configs/config.yaml"


def build_parser() -> argparse.ArgumentParser:
    """Создаёт argparse-парсер.

    Returns:
        Настроенный парсер.
    """
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


def print_dependencies(package: str, dependencies: list) -> None:
    """Выводит прямые зависимости пакета.

    Args:
        package: имя пакета.
        dependencies: список объектов Dependency.
    """
    if not dependencies:
        print(f"{package}: нет прямых зависимостей")
        return

    print(f"Прямые зависимости {package}:")
    for dep in dependencies:
        print(f"  - {dep.name} ({dep.version})")


def main(argv: list[str] | None = None) -> int:
    """Точка входа.

    Args:
        argv: аргументы командной строки.

    Returns:
        Код возврата: 0 при успехе, 1 при ошибке.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config_path)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return 1

    print(format_config(config))

    if config.test_mode:
        print("Тестовый режим: получение зависимостей из NuGet не выполняется")
        return 0

    try:
        dependencies = fetch_dependencies(
            config.package_name,
            config.package_version,
            config.repository_url,
        )
    except NuGetError as error:
        print(f"Ошибка NuGet: {error}", file=sys.stderr)
        return 1

    print_dependencies(config.package_name, dependencies)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
