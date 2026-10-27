# Визуализатор графа зависимостей NuGet

Практическая работа №2 по дисциплине «Конфигурационное управление».
Вариант №20.

## Общее описание

Инструмент для построения и визуализации графа зависимостей пакетов
менеджера .NET (NuGet). Готовые менеджеры пакетов и библиотеки для
получения зависимостей не используются — только HTTP и разбор .nuspec.

## Этапы разработки

- [x] Этап 1. Минимальный прототип с конфигурацией (YAML)
- [x] Этап 2. Сбор данных (NuGet)
- [ ] Этап 3. Основные операции — граф (DFS без рекурсии)
- [ ] Этап 4. Дополнительные операции (порядок загрузки)
- [ ] Этап 5. Визуализация (D2 → PNG, ASCII-дерево)

## Функции и настройки

### Этап 1 (реализовано)

- Конфигурация загружается из YAML-файла.
- Параметры:
  - `package_name` — имя анализируемого пакета;
  - `repository_url` — URL репозитория или путь к тестовому файлу;
  - `test_mode` — использовать тестовый репозиторий;
  - `package_version` — версия пакета;
  - `output_image` — путь к PNG с графом;
  - `ascii_tree` — выводить ли ASCII-дерево;
  - `max_depth` — максимальная глубина анализа
    (`-1` = без ограничений, `0` = только корень, `> 0` = ограничение).
- При запуске выводится отладочный дамп параметров в формате
  ключ-значение.
- Обработка ошибок: файл не найден, неверный YAML, отсутствие
  обязательных полей, пустые строки, неверные типы, глубина < -1.

### Этап 2 (реализовано)

- Получение прямых зависимостей пакета NuGet по URL репозитория.
- Формирование URL `.nupkg`-файла по шаблону:
  `{repository_url}/{id}/{version}/{id}.{version}.nupkg`.
- Скачивание `.nupkg` в память (без сохранения на диск).
- Извлечение `.nuspec` из ZIP-архива.
- Парсинг XML:
  - поиск `<dependency>` на любой глубине внутри `<dependencies>`
    (в том числе внутри `<group targetFramework="...">`);
  - дедупликация зависимостей по имени.
- Обработка ошибок:
  - неверный URL репозитория;
  - пустые имя или версия пакета;
  - HTTP-ошибки (404, 500 и т.д.);
  - ошибки сети и таймауты;
  - повреждённый ZIP-архив;
  - отсутствие `.nuspec` в архиве;
  - некорректный XML.
- Готовые менеджеры пакетов и клиентские библиотеки NuGet
  не используются — только `urllib`, `zipfile`, `xml.etree`.

## Сборка и запуск

Требуется Python 3.10+.

Зависимости:
```bash
python -m pip install -r requirements.txt
```

Или вручную:
```bash
python -m pip install pyyaml requests pytest
```

Запуск:
```bash
python -m src.main --config configs/config.yaml
```

На Windows:
```
run.bat --config configs/config.yaml
```

На Linux/macOS:
```bash
./run.sh --config configs/config.yaml
```

## Запуск тестов

```bash
python -m pytest tests/ -v
```

## Проверка стиля

```bash
python -m flake8 --max-line-length=80 src/ tests/
```

## Примеры использования

### Запуск с конфигурацией

```bash
python -m src.main --config configs/config.yaml
```

Вывод при запуске:
```
Параметры запуска:
  package_name     = 'Newtonsoft.Json'
  repository_url   = 'https://api.nuget.org/v3-flatcontainer'
  test_mode        = False
  package_version  = '13.0.3'
  output_image     = 'output/graph.png'
  ascii_tree       = True
  max_depth        = -1
Newtonsoft.Json: нет прямых зависимостей
```

### Пакет с зависимостями

`configs/serilog.yaml`:
```yaml
package_name: "Serilog.Sinks.Console"
repository_url: "https://api.nuget.org/v3-flatcontainer"
test_mode: false
package_version: "5.0.0"
output_image: "output/serilog.png"
ascii_tree: true
max_depth: -1
```

```bash
python -m src.main --config configs/serilog.yaml
```

Вывод:
```
Прямые зависимости Serilog.Sinks.Console:
  - Serilog (3.1.0)
```

### Обработка ошибок

**Файл конфигурации не найден:**
```
Ошибка конфигурации: Файл конфигурации не найден: configs/missing.yaml
```

**Неверный формат YAML:**
```
Ошибка конфигурации: Ошибка разбора YAML: ...
```

**Отсутствуют обязательные поля:**
```
Ошибка конфигурации: Отсутствуют поля: ['repository_url', 'test_mode', ...]
```

**Пакет не найден в NuGet:**
```
Ошибка NuGet: HTTP 404 при скачивании ...: Not Found
```

**Ошибка сети:**
```
Ошибка NuGet: Ошибка сети при скачивании ...: <urlopen error ...>
```