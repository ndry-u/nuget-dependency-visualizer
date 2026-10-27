"""Получение зависимостей пакетов NuGet.

Пакет NuGet — это ZIP-архив (.nupkg), внутри которого находится
файл .nuspec с метаданными, включая зависимости.
Готовые менеджеры пакетов и клиентские библиотеки NuGet не используются.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

NUSPEC_NS = "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"
DEFAULT_TIMEOUT = 30


class NuGetError(Exception):
    """Ошибка получения данных о пакете."""


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость пакета.

    Attributes:
        name: имя пакета.
        version: версия пакета.
    """

    name: str
    version: str


def build_package_url(repository_url: str, package: str, version: str) -> str:
    """Формирует URL для скачивания пакета.

    Args:
        repository_url: базовый URL репозитория (без завершающего слеша).
        package: имя пакета.
        version: версия пакета.

    Returns:
        Полный URL к .nupkg.

    Raises:
        NuGetError: если параметры некорректны.
    """
    if not repository_url.startswith(("http://", "https://")):
        raise NuGetError(
            f"URL репозитория должен начинаться с http:// или https://: "
            f"{repository_url}"
        )
    if not package.strip():
        raise NuGetError("Имя пакета не может быть пустым")
    if not version.strip():
        raise NuGetError("Версия пакета не может быть пустой")

    base = repository_url.rstrip("/")
    lower_name = package.lower()
    lower_version = version.lower()
    return (
        f"{base}/{lower_name}/{lower_version}/"
        f"{lower_name}.{lower_version}.nupkg"
    )


def _download(url: str) -> bytes:
    """Скачивает содержимое по URL.

    Args:
        url: URL для скачивания.

    Returns:
        Байты содержимого.

    Raises:
        NuGetError: при ошибках сети или HTTP.
    """
    try:
        with urlopen(url, timeout=DEFAULT_TIMEOUT) as response:
            return response.read()
    except HTTPError as error:
        raise NuGetError(
            f"HTTP {error.code} при скачивании {url}: {error.reason}"
        ) from error
    except URLError as error:
        raise NuGetError(
            f"Ошибка сети при скачивании {url}: {error.reason}"
        ) from error
    except TimeoutError as error:
        raise NuGetError(
            f"Таймаут при скачивании {url}"
        ) from error


def _extract_nuspec(data: bytes) -> bytes:
    """Извлекает содержимое .nuspec из .nupkg (zip).

    Args:
        data: байты архива .nupkg.

    Returns:
        Содержимое .nuspec.

    Raises:
        NuGetError: если архив повреждён или .nuspec не найден.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            nuspec_files = [
                name for name in archive.namelist()
                if name.lower().endswith(".nuspec")
            ]
            if not nuspec_files:
                raise NuGetError("В архиве .nupkg не найден .nuspec")
            return archive.read(nuspec_files[0])
    except zipfile.BadZipFile as error:
        raise NuGetError(f"Повреждённый .nupkg: {error}") from error


def _parse_nuspec(xml_bytes: bytes) -> list[Dependency]:
    """Парсит .nuspec и извлекает зависимости.

    Зависимости могут быть как напрямую в <dependencies>,
    так и внутри <group targetFramework="...">. Повторяющиеся
    зависимости (из разных групп) объединяются по имени —
    берётся первая встреченная версия.

    Args:
        xml_bytes: содержимое .nuspec (XML).

    Returns:
        Список прямых зависимостей без дубликатов.

    Raises:
        NuGetError: если XML некорректен или корневой тег неожиданный.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as error:
        raise NuGetError(f"Ошибка парсинга .nuspec: {error}") from error

    ns = {"n": NUSPEC_NS}
    dependencies_node = root.find(".//n:dependencies", ns)
    if dependencies_node is None:
        return []

    seen: set[str] = set()
    result: list[Dependency] = []
    for dep in dependencies_node.findall(".//n:dependency", ns):
        name = dep.get("id", "").strip()
        version = dep.get("version", "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(Dependency(name=name, version=version))
    return result


def fetch_dependencies(
    package: str,
    version: str,
    repository_url: str,
) -> list[Dependency]:
    """Получает прямые зависимости пакета из NuGet.

    Args:
        package: имя пакета.
        version: версия пакета.
        repository_url: URL репозитория.

    Returns:
        Список прямых зависимостей.

    Raises:
        NuGetError: при любой ошибке получения данных.
    """
    url = build_package_url(repository_url, package, version)
    data = _download(url)
    nuspec = _extract_nuspec(data)
    return _parse_nuspec(nuspec)
