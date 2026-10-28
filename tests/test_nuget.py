"""Юнит-тесты для модуля работы с NuGet."""

import io
import zipfile

import pytest

from src.nuget import (
    Dependency,
    NuGetError,
    _extract_nuspec,
    _parse_nuspec,
    build_package_url,
    fetch_dependencies,
)

EXPECTED_FLAT_DEPS = 2
EXPECTED_GROUPED_DEPS = 2
EXPECTED_SERILOG_COUNT = 1

SAMPLE_NUSPEC = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Test.Package</id>
    <version>1.0.0</version>
    <dependencies>
      <dependency id="Newtonsoft.Json" version="13.0.3" />
      <dependency id="System.Text.Json" version="8.0.0" />
    </dependencies>
  </metadata>
</package>
"""

EMPTY_NUSPEC = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Empty.Package</id>
    <version>1.0.0</version>
  </metadata>
</package>
"""

GROUPED_NUSPEC = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Grouped.Package</id>
    <version>1.0.0</version>
    <dependencies>
      <group targetFramework="net6.0">
        <dependency id="Serilog" version="3.1.0" />
        <dependency id="Newtonsoft.Json" version="13.0.3" />
      </group>
      <group targetFramework="net8.0">
        <dependency id="Serilog" version="3.1.0" />
      </group>
    </dependencies>
  </metadata>
</package>
"""


def _make_nupkg(nuspec_content: str) -> bytes:
    """Создаёт .nupkg в памяти с указанным .nuspec."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("Test.Package.nuspec", nuspec_content)
    return buffer.getvalue()


class TestBuildPackageUrl:
    """Тесты формирования URL."""

    def test_basic(self) -> None:
        """Обычный URL."""
        url = build_package_url(
            "https://api.nuget.org/v3-flatcontainer",
            "Newtonsoft.Json",
            "13.0.3",
        )
        assert url == (
            "https://api.nuget.org/v3-flatcontainer/"
            "newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg"
        )

    def test_trailing_slash(self) -> None:
        """Завершающий слеш убирается."""
        url = build_package_url(
            "https://api.nuget.org/v3-flatcontainer/",
            "Test",
            "1.0",
        )
        assert not url.startswith(
            "https://api.nuget.org/v3-flatcontainer//"
        )

    def test_invalid_url(self) -> None:
        """URL без http/https — ошибка."""
        with pytest.raises(NuGetError):
            build_package_url("api.nuget.org", "Test", "1.0")

    def test_empty_package(self) -> None:
        """Пустое имя пакета — ошибка."""
        with pytest.raises(NuGetError):
            build_package_url("https://api.nuget.org", "", "1.0")

    def test_empty_version(self) -> None:
        """Пустая версия — ошибка."""
        with pytest.raises(NuGetError):
            build_package_url("https://api.nuget.org", "Test", "")


class TestExtractNuspec:
    """Тесты извлечения .nuspec из архива."""

    def test_extract_ok(self) -> None:
        """Корректный архив."""
        data = _make_nupkg(SAMPLE_NUSPEC)
        result = _extract_nuspec(data)
        assert b"Test.Package" in result

    def test_missing_nuspec(self) -> None:
        """Архив без .nuspec — ошибка."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("readme.txt", "hello")
        with pytest.raises(NuGetError):
            _extract_nuspec(buffer.getvalue())

    def test_bad_zip(self) -> None:
        """Не-zip данные — ошибка."""
        with pytest.raises(NuGetError):
            _extract_nuspec(b"not a zip")


class TestParseNuspec:
    """Тесты парсинга .nuspec."""

    def test_parse_dependencies(self) -> None:
        """Извлекаются все зависимости (плоский список)."""
        result = _parse_nuspec(SAMPLE_NUSPEC.encode("utf-8"))
        assert len(result) == EXPECTED_FLAT_DEPS
        assert result[0] == Dependency("Newtonsoft.Json", "13.0.3")
        assert result[1] == Dependency("System.Text.Json", "8.0.0")

    def test_empty_dependencies(self) -> None:
        """Пакет без зависимостей."""
        result = _parse_nuspec(EMPTY_NUSPEC.encode("utf-8"))
        assert result == []

    def test_invalid_xml(self) -> None:
        """Повреждённый XML — ошибка."""
        with pytest.raises(NuGetError):
            _parse_nuspec(b"<not-xml")


class TestParseGroupedNuspec:
    """Тесты парсинга зависимостей внутри <group>."""

    def test_grouped_dependencies(self) -> None:
        """Зависимости извлекаются из групп."""
        result = _parse_nuspec(GROUPED_NUSPEC.encode("utf-8"))
        assert len(result) == EXPECTED_GROUPED_DEPS
        names = [d.name for d in result]
        assert "Serilog" in names
        assert "Newtonsoft.Json" in names

    def test_deduplication(self) -> None:
        """Повторяющиеся зависимости объединяются."""
        result = _parse_nuspec(GROUPED_NUSPEC.encode("utf-8"))
        names = [d.name for d in result]
        assert names.count("Serilog") == EXPECTED_SERILOG_COUNT


class TestFetchDependencies:
    """Тесты высокоуровневой функции (без сети)."""

    def test_invalid_url(self) -> None:
        """Невалидный URL даёт ошибку до сетевого запроса."""
        with pytest.raises(NuGetError):
            fetch_dependencies("Test", "1.0", "not-a-url")
