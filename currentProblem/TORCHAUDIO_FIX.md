# Решение проблемы с torchaudio в ComfyUI

## Проблема

ComfyUI падает при запуске с ошибкой:

```
AttributeError: partially initialized module 'torchaudio' has no attribute 'lib' (most likely due to a circular import)
```

Это происходит потому что ComfyUI импортирует torchaudio в файле `/comfyui/comfy_api/latest/_ui.py`, но torchaudio имеет циклическую зависимость при проверке версии CUDA.

## Решение

Мы применяем многоуровневый подход:

### 1. Ранний патч через sitecustomize.py

Создаем файл `/usr/local/lib/python3.11/site-packages/sitecustomize.py`, который автоматически загружается при каждом запуске Python и создает mock для torchaudio.

### 2. Полное удаление и замена torchaudio

Скрипт `remove_torchaudio.py`:

-   Удаляет torchaudio через pip
-   Удаляет все файлы torchaudio из системы
-   Создает фейковый пакет torchaudio с минимальным функционалом

### 3. Дополнительный патч при запуске

В `startup.sh` применяем патч еще раз перед запуском ComfyUI для гарантии.

### 4. Обработка ошибок запуска

Если ComfyUI не запускается, автоматически применяем патч еще раз и перезапускаем.

## GitPython

GitPython работает корректно (видно в логах). Мы дополнительно:

-   Удаляем старые версии перед установкой
-   Используем --force-reinstall для чистой установки
-   Проверяем работоспособность после установки

## Переменные окружения

Устанавливаем переменные для отключения проверок torchaudio:

-   `TORCH_AUDIO_BACKEND=soundfile`
-   `DISABLE_TORCHAUDIO_CUDA_CHECK=1`
-   `CM_DISABLE_TORCHAUDIO=1`

## Результат

ComfyUI должен запуститься без ошибок, игнорируя отсутствие torchaudio (он не нужен для работы с видео моделями WAN).
