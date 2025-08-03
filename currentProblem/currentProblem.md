# Проблема с torchaudio в WAN 2.2 ServerLess Worker

## 🔴 Описание проблемы

### Симптомы из логов

```
AttributeError: partially initialized module 'torchaudio' has no attribute 'lib' (most likely due to a circular import)
```

### Root Cause Analysis

1. **Циклический импорт torchaudio** в `/comfyui/comfy_api/latest/_ui.py:12`
2. **Неправильная последовательность патчинга** - патчи применялись ПОСЛЕ запуска ComfyUI
3. **Множественные конфликтующие патчи**:
    - `sitecustomize.py`
    - `torchaudio_patch.py`
    - Subprocess обертки

## 🔧 Решение

### Изменения в Dockerfile

```dockerfile
# РАННИЙ ПАТЧ torchaudio - ДО клонирования ComfyUI
COPY torchaudio_patch.py /tmp/torchaudio_patch.py
RUN python3 /tmp/torchaudio_patch.py

# Клонируем и устанавливаем ComfyUI
WORKDIR /
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
```

### Упрощение startup.sh

**Было** (80+ строк сложного кода):

-   sitecustomize.py с множественными патчами
-   subprocess обертки для ComfyUI
-   Дополнительное применение патчей

**Стало** (простой запуск):

```bash
# torchaudio патч уже применен в Dockerfile
echo "✅ torchaudio патч применен на этапе сборки"

# Запускаем ComfyUI
echo "🎨 Запуск ComfyUI..."
cd /comfyui
python main.py --listen 0.0.0.0 --port 8188 &
COMFY_PID=$!
```

## ✅ Результат

### Преимущества нового подхода:

-   **Простота**: Убрали 80+ строк сложного кода
-   **Надежность**: Патч применяется рано, до циклических импортов
-   **Прозрачность**: Простой запуск без многослойных оберток
-   **Правильная последовательность**: torchaudio mock создается ПЕРЕД клонированием ComfyUI

### Ожидаемый результат:

-   Исчезновение циклического импорта torchaudio
-   Успешный запуск ComfyUI без падений
-   Корректная работа GitPython и ComfyUI-Manager

## 🚀 Следующие шаги

1. Пересобрать Docker образ
2. Протестировать запуск
3. Проверить работу всех workflow типов (T2I, T2V, I2I, Video Upscale)

## 📝 Техническая деталь

Основная идея исправления - применить mock torchaudio модули на системном уровне ДО того, как Python встретит любые реальные импорты torchaudio в коде ComfyUI. Это предотвращает циклические импорты и обеспечивает стабильную работу.
