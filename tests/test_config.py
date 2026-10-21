"""Юнит-тесты для модуля конфигурации."""

import pytest

from src.config import (
    DEFAULT_MAX_DEPTH,
    INFINITE_DEPTH,
    Config,
    ConfigError,
    format_config,
    load_config,
)

DEFAULT_DEPTH = 5
INVALID_DEPTH = -2


def _write_yaml(tmp_path, content: str) -> str:
    """Записывает YAML во временный файл и возвращает путь."""
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


VALID_YAML = f"""
package_name: "Newtonsoft.Json"
repository_url: "https://api.nuget.org/v3-flatcontainer"
test_mode: false
package_version: "13.0.3"
output_image: "output/graph.png"
ascii_tree: true
max_depth: {DEFAULT_DEPTH}
"""


class TestLoadConfig:
    """Тесты загрузки конфигурации."""

    def test_valid_config(self, tmp_path) -> None:
        """Корректный конфиг загружается без ошибок."""
        path = _write_yaml(tmp_path, VALID_YAML)
        config = load_config(path)
        assert config.package_name == "Newtonsoft.Json"
        assert config.test_mode is False
        assert config.max_depth == DEFAULT_DEPTH

    def test_missing_file(self) -> None:
        """Отсутствующий файл даёт ошибку."""
        with pytest.raises(ConfigError):
            load_config("nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path) -> None:
        """Повреждённый YAML даёт ошибку."""
        path = _write_yaml(tmp_path, "foo: [unclosed")
        with pytest.raises(ConfigError):
            load_config(path)

    def test_missing_field(self, tmp_path) -> None:
        """Отсутствие обязательного поля даёт ошибку."""
        path = _write_yaml(
            tmp_path,
            "package_name: a\nrepository_url: b\n",
        )
        with pytest.raises(ConfigError):
            load_config(path)

    def test_empty_string_field(self, tmp_path) -> None:
        """Пустая строка в поле даёт ошибку."""
        yaml_text = VALID_YAML.replace(
            'package_name: "Newtonsoft.Json"',
            'package_name: "   "',
        )
        path = _write_yaml(tmp_path, yaml_text)
        with pytest.raises(ConfigError):
            load_config(path)

    def test_invalid_test_mode_type(self, tmp_path) -> None:
        """test_mode не булев — ошибка."""
        yaml_text = VALID_YAML.replace(
            "test_mode: false", 'test_mode: "false"'
        )
        path = _write_yaml(tmp_path, yaml_text)
        with pytest.raises(ConfigError):
            load_config(path)

    def test_invalid_max_depth(self, tmp_path) -> None:
        """max_depth < -1 — ошибка."""
        yaml_text = VALID_YAML.replace(
            f"max_depth: {DEFAULT_DEPTH}",
            f"max_depth: {INVALID_DEPTH}",
        )
        path = _write_yaml(tmp_path, yaml_text)
        with pytest.raises(ConfigError):
            load_config(path)

    def test_default_max_depth(self, tmp_path) -> None:
        """max_depth отсутствует — берётся -1 (без ограничений)."""
        yaml_text = VALID_YAML.replace(f"max_depth: {DEFAULT_DEPTH}\n", "")
        path = _write_yaml(tmp_path, yaml_text)
        config = load_config(path)
        assert config.max_depth == INFINITE_DEPTH
        assert config.max_depth == DEFAULT_MAX_DEPTH

    def test_infinite_depth_explicit(self, tmp_path) -> None:
        """max_depth: -1 — допустимо (без ограничений)."""
        yaml_text = VALID_YAML.replace(
            f"max_depth: {DEFAULT_DEPTH}",
            f"max_depth: {INFINITE_DEPTH}",
        )
        path = _write_yaml(tmp_path, yaml_text)
        config = load_config(path)
        assert config.max_depth == INFINITE_DEPTH

    def test_zero_depth_allowed(self, tmp_path) -> None:
        """max_depth: 0 — допустимо (только корень)."""
        yaml_text = VALID_YAML.replace(
            f"max_depth: {DEFAULT_DEPTH}",
            "max_depth: 0",
        )
        path = _write_yaml(tmp_path, yaml_text)
        config = load_config(path)
        assert config.max_depth == 0


class TestFormatConfig:
    """Тесты функции format_config."""

    def test_contains_all_keys(self) -> None:
        """Все ключи присутствуют в выводе."""
        config = Config(
            package_name="A",
            repository_url="B",
            test_mode=True,
            package_version="1.0",
            output_image="out.png",
            ascii_tree=False,
            max_depth=DEFAULT_DEPTH,
        )
        text = format_config(config)
        for key in (
            "package_name",
            "repository_url",
            "test_mode",
            "package_version",
            "output_image",
            "ascii_tree",
            "max_depth",
        ):
            assert key in text