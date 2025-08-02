# Фикс для проблемы с torchaudio циклическим импортом

## Проблема

При запуске ComfyUI возникает ошибка циклического импорта в torchaudio:

```
AttributeError: partially initialized module 'torchaudio' has no attribute 'lib' (most likely due to a circular import)
```

## Решение

Создан комплексный фикс состоящий из нескольких компонентов:

### 1. Переменные окружения в Dockerfile

```dockerfile
ENV TORCH_AUDIO_BACKEND=soundfile \
    TORCHAUDIO_BACKEND=soundfile \
    DISABLE_TORCHAUDIO_CUDA_CHECK=1
```

### 2. Патч файл torchaudio_patch.py

-   Создает mock модули для всех проблемных компонентов torchaudio
-   Устанавливает защитные переменные окружения
-   Использует import hook для перехвата импортов torchaudio
-   Предотвращает циклический импорт путем предварительной загрузки mock'ов

### 3. Интеграция в startup.sh

-   Применяет патч перед запуском ComfyUI
-   Имеет fallback на стандартный запуск если патч не сработал
-   Создает wrapper скрипт с патчем для запуска ComfyUI

## Как это работает

1. При запуске контейнера патч применяется в startup.sh
2. Создается wrapper скрипт который:
    - Загружает torchaudio патч
    - Запускает main.py ComfyUI с правильными аргументами
3. Если что-то идет не так, есть fallback на стандартный запуск

## Файлы изменены

-   `Dockerfile` - добавлены переменные окружения и копирование патча
-   `startup.sh` - добавлена логика применения патча
-   `torchaudio_patch.py` - новый файл с патчем (создан)
-   `docs/torchaudio_fix.md` - данная документация (создана)

## Проверка работы

После применения фикса вместо ошибки циклического импорта должно появиться:

```
✅ torchaudio mock создан успешно
✅ torchaudio import hook установлен
✅ torchaudio патч применен успешно
```
