"""Точка входа приложения.

Этап 1: загрузка и вывод параметров YAML-конфигурации.
"""

from __future__ import annotations

import argparse
import sys

from src.config import ConfigError, format_config, load_config

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
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
