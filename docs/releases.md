# Управление релизами

Этот проект использует автоматизированную систему управления версиями и создания релизов.

## Быстрый старт

### Создание релиза

```bash
# Patch релиз (1.0.0 -> 1.0.1) - багфиксы
make patch

# Minor релиз (1.0.0 -> 1.1.0) - новые функции
make minor

# Major релиз (1.0.0 -> 2.0.0) - breaking changes
make major
```

### Или используя напрямую Python скрипт:

```bash
python release.py patch
python release.py minor
python release.py major
```

## Что происходит при создании релиза

1. **Проверка состояния Git** - убеждается что нет незакоммиченных изменений
2. **Инкрементирование версии** - обновляет `version.py` и `deploy_config.json`
3. **Git операции** - создает commit и tag
4. **Push в remote** - отправляет изменения и теги
5. **GitHub Release** - создает релиз с автоматическими release notes

## Требования

### Локальные зависимости

-   Python 3.7+
-   Git
-   [GitHub CLI](https://cli.github.com/) (опционально, для автоматического создания GitHub releases)

```bash
# Установка GitHub CLI на macOS
brew install gh

# Авторизация
gh auth login
```

### GitHub Secrets (для CI/CD)

Для автоматической сборки Docker images при создании тегов, настройте следующие secrets в GitHub:

-   `DOCKER_USERNAME` - ваш username на Docker Hub
-   `DOCKER_PASSWORD` - ваш пароль или access token для Docker Hub

## Структура версионирования

-   `version.py` - основной файл с версией
-   `deploy_config.json` - автоматически обновляется с новым Docker image тегом
-   Git теги в формате `v1.0.0`
-   Docker image теги в формате `v1.0.0`

## Workflow релиза

1. **Разработка** - делайте изменения в feature branches
2. **Merge в main** - объединяйте готовые изменения
3. **Создание релиза** - используйте `make patch/minor/major`
4. **Автоматическая сборка** - GitHub Actions соберет и опубликует Docker image
5. **Деплой** - используйте обновленный `deploy_config.json` для развертывания

## Полезные команды

```bash
# Показать текущую версию
make status

# Собрать Docker image локально
make build

# Отправить Docker image в registry
make push

# Развернуть на RunPod (если установлен runpod CLI)
make deploy

# Показать все доступные команды
make help
```

## Ручное управление версией

Если нужно изменить версию вручную:

1. Отредактируйте `version.py`
2. Выполните `python release.py patch` (заменит версию на правильно инкрементированную)

## Troubleshooting

### "gh command not found"

Установите GitHub CLI или создавайте релизы вручную через веб-интерфейс GitHub.

### "Not authorized with GitHub CLI"

Выполните `gh auth login` и следуйте инструкциям.

### "Uncommitted changes"

Закоммитьте все изменения перед созданием релиза:

```bash
git add .
git commit -m "feat: your changes"
```

### Docker Hub проблемы

Убедитесь что:

1. Secrets настроены правильно в GitHub
2. Docker Hub репозиторий существует
3. Username и password/token корректны
