"""Разбор YAML-конфигурации приложения."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_FIELDS = (
    "package_name",
    "repository_url",
    "test_mode",
    "package_version",
    "output_image",
    "ascii_tree",
)
DEFAULT_MAX_DEPTH = -1
INFINITE_DEPTH = -1
MIN_ALLOWED_DEPTH = -1


class ConfigError(Exception):
    """Ошибка конфигурации."""


@dataclass(frozen=True)
class Config:
    """Параметры работы приложения.

    Attributes:
        package_name: имя анализируемого пакета.
        repository_url: URL репозитория или путь к тестовому файлу.
        test_mode: использовать тестовый репозиторий вместо URL.
        package_version: версия пакета.
        output_image: путь к сгенерированному изображению.
        ascii_tree: выводить ли ASCII-дерево.
        max_depth: максимальная глубина анализа (-1 = без ограничений).
    """

    package_name: str
    repository_url: str
    test_mode: bool
    package_version: str
    output_image: str
    ascii_tree: bool
    max_depth: int


def _read_yaml(path: str) -> dict:
    """Читает YAML-файл и возвращает словарь.

    Args:
        path: путь к YAML-файлу.

    Returns:
        Содержимое файла в виде словаря.

    Raises:
        ConfigError: если файл не найден, повреждён или не является словарём.
    """
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise ConfigError(f"Файл конфигурации не найден: {path}")
    if not yaml_path.is_file():
        raise ConfigError(f"Не файл: {path}")

    try:
        with yaml_path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except yaml.YAMLError as error:
        raise ConfigError(f"Ошибка разбора YAML: {error}") from error

    if not isinstance(data, dict):
        raise ConfigError("Корень YAML-файла должен быть словарём")
    return data


def _check_required(data: dict) -> None:
    """Проверяет наличие обязательных полей.

    Args:
        data: словарь из YAML.

    Raises:
        ConfigError: если какого-то поля не хватает.
    """
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ConfigError(f"Отсутствуют поля: {missing}")


def _check_str(value: object, name: str) -> str:
    """Проверяет, что значение — непустая строка.

    Args:
        value: значение из конфига.
        name: имя поля для сообщения об ошибке.

    Returns:
        Строка.

    Raises:
        ConfigError: если значение не строка или пустая.
    """
    if not isinstance(value, str):
        raise ConfigError(f"Поле '{name}' должно быть строкой")
    if not value.strip():
        raise ConfigError(f"Поле '{name}' не может быть пустым")
    return value.strip()


def _check_bool(value: object, name: str) -> bool:
    """Проверяет, что значение — булево.

    Args:
        value: значение из конфига.
        name: имя поля.

    Returns:
        Булево значение.

    Raises:
        ConfigError: если тип не bool.
    """
    if not isinstance(value, bool):
        raise ConfigError(f"Поле '{name}' должно быть true или false")
    return value


def _check_depth(value: object) -> int:
    """Проверяет максимальную глубину.

    Args:
        value: значение из конфига или None.

    Returns:
        Целое число ≥ -1. -1 означает бесконечность.

    Raises:
        ConfigError: если значение некорректно.
    """
    if value is None:
        return DEFAULT_MAX_DEPTH
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError("Поле 'max_depth' должно быть целым числом")
    if value < MIN_ALLOWED_DEPTH:
        raise ConfigError(
            f"Поле 'max_depth' должно быть ≥ {MIN_ALLOWED_DEPTH} "
            "(-1 = без ограничений)"
        )
    return value


def load_config(path: str) -> Config:
    """Загружает и валидирует конфигурацию.

    Args:
        path: путь к YAML-файлу.

    Returns:
        Заполненная структура Config.

    Raises:
        ConfigError: при любой ошибке конфигурации.
    """
    data = _read_yaml(path)
    _check_required(data)

    return Config(
        package_name=_check_str(data["package_name"], "package_name"),
        repository_url=_check_str(data["repository_url"], "repository_url"),
        test_mode=_check_bool(data["test_mode"], "test_mode"),
        package_version=_check_str(data["package_version"], "package_version"),
        output_image=_check_str(data["output_image"], "output_image"),
        ascii_tree=_check_bool(data["ascii_tree"], "ascii_tree"),
        max_depth=_check_depth(data.get("max_depth")),
    )


def format_config(config: Config) -> str:
    """Формирует отладочный вывод параметров.

    Args:
        config: разобранные параметры.

    Returns:
        Многострочная строка вида 'ключ = значение'.
    """
    lines = [
        "Параметры запуска:",
        f"  package_name     = {config.package_name!r}",
        f"  repository_url   = {config.repository_url!r}",
        f"  test_mode        = {config.test_mode!r}",
        f"  package_version  = {config.package_version!r}",
        f"  output_image     = {config.output_image!r}",
        f"  ascii_tree       = {config.ascii_tree!r}",
        f"  max_depth        = {config.max_depth!r}",
    ]
    return "\n".join(lines)