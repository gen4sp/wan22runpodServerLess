# Инструкции по сборке Docker образа

## Что было исправлено

### ✅ Исправленные проблемы в Dockerfile:

1. **Добавлены переменные окружения для torchaudio**:

    - `CM_NETWORK_MODE=offline`
    - `COMFYUI_DISABLE_VERSION_CHECK=1`
    - `TORCH_AUDIO_BACKEND=soundfile`
    - `TORCHAUDIO_BACKEND=soundfile`
    - `DISABLE_TORCHAUDIO_CUDA_CHECK=1`
    - `CM_DISABLE_TORCHAUDIO=1`
    - `PYTHONDONTWRITEBYTECODE=1`

2. **Полная система обработки torchaudio**:

    - Скрипт `remove_torchaudio.py` для полного удаления
    - Скрипт `torchaudio_patch.py` для создания mock-версии
    - Файл `sitecustomize.py` для раннего патчинга при запуске Python
    - Проверка работоспособности mock-версии

3. **Исправлены custom nodes**:

    - Убраны несуществующие репозитории
    - Добавлены правильные зависимости:
        - `ComfyUI_essentials`
        - `ComfyUI-VideoHelperSuite`
        - `ComfyUI_IPAdapter_plus`
        - `ComfyUI-WanStartEndFramesNative`
        - `ComfyUI-post-processing-nodes`
        - `ComfyUI-EmptyHunyuanLatent`

4. **Улучшена установка зависимостей**:

    - Принудительная переустановка критических пакетов
    - Обработка ошибок при установке зависимостей custom nodes
    - Fallback механизмы для ComfyUI-Manager

5. **Расширен requirements.txt**:
    - Добавлены все необходимые зависимости для обработки изображений и видео
    - Версии пакетов зафиксированы для стабильности

## Команды для сборки

```bash
# Убедитесь что Docker запущен
docker --version

# Соберите образ
docker build -t wan22-serverless:latest .

# Проверьте что образ создался
docker images | grep wan22-serverless

# Запустите контейнер для тестирования
docker run --rm -it wan22-serverless:latest /bin/bash
```

## Проверка установленных зависимостей

После запуска контейнера выполните:

```bash
# Проверка Python зависимостей
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torchaudio; print(f'TorchAudio (mock): {torchaudio.__version__}')"
python3 -c "import xformers; print(f'xformers: {xformers.__version__}')"

# Проверка ComfyUI
cd /comfyui && python3 main.py --help

# Проверка custom nodes
ls -la /comfyui/custom_nodes/

# Проверка зависимостей
pip list | grep -E "(torch|numpy|pillow|opencv|requests|aiohttp|gitpython)"
```

## Структура установленных компонентов

### Системные зависимости:

-   ffmpeg
-   git, wget, curl
-   OpenGL библиотеки
-   Системные библиотеки для обработки изображений

### Python зависимости:

-   PyTorch 2.8.0 с CUDA 12.8
-   xformers (оптимизированный для RTX 5090)
-   flash-attention
-   Все зависимости из requirements.txt

### ComfyUI компоненты:

-   ComfyUI (основная система)
-   ComfyUI-Manager (управление custom nodes)
-   6 критически важных custom nodes
-   Mock torchaudio (предотвращает конфликты)

## Устранение неисправностей

Если при сборке возникают ошибки:

1. **Ошибки torchaudio**: Система автоматически создаст mock-версию
2. **Ошибки custom nodes**: Некритичные ошибки будут пропущены
3. **Ошибки зависимостей**: Есть fallback механизмы

Логи сборки покажут все проблемы с префиксами:

-   ✅ - успешно
-   ⚠️ - предупреждение
-   ❌ - ошибка (но обработана)

## Следующие шаги

После успешной сборки образ готов для:

1. Загрузки на RunPod
2. Обработки T2I/T2V/I2I/V2V workflow
3. Использования с системой JSON workflow [[memory:5023539]]
