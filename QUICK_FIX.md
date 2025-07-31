# Быстрое исправление проблемы с моделями и Custom Nodes

## Проблема 1: Отсутствие моделей

```
❌ Отсутствуют критически важные файлы:
   - /comfyui/models/unet/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
   - /comfyui/models/unet/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
   - ...
```

## Проблема 2: Потеря Custom Nodes (КРИТИЧЕСКАЯ)

```
❌ Custom nodes не найдены! Проблема с volume linking
```

**Причина:** Volume полностью заменял папку `/comfyui`, что приводило к потере всех установленных custom nodes.

## Решение

### 1. Проверьте структуру Volume

Модели должны лежать в одной из структур:

**✅ Правильно:**

```
/runpod-volume/ComfyUI/models/unet/
/runpod-volume/ComfyUI/models/vae/
/runpod-volume/ComfyUI/models/clip/
/runpod-volume/ComfyUI/models/loras/wan/
```

**❌ Неправильно:**

```
/runpod-volume/unet/
/runpod-volume/vae/
```

### 2. Перестройте и перезапустите контейнер

```bash
# Пересобрать образ
docker build -t wan22-worker .

# Пушнуть в Docker Hub
docker push your-username/wan22-worker:latest
```

### 3. Диагностика в контейнере

После запуска контейнера в RunPod:

```bash
# Запустить диагностику
bash diagnose_volume.sh
```

### 4. Исправление Volume Mount

В настройках RunPod Endpoint:

-   **Volume Mount Point**: `/runpod-volume` (обязательно!)
-   **Container Path**: должен быть пустым или `/runpod-volume`

### 5. Проверка логов

```bash
# Смотрим что происходит при запуске
docker logs <container_id>
```

## Обновленные файлы

-   ✅ `startup.sh` - **ИСПРАВЛЕНА КРИТИЧЕСКАЯ ОШИБКА**: теперь линкуется только папка models, custom nodes сохраняются
-   ✅ `diagnose_volume.sh` - добавлена диагностика custom nodes
-   ✅ `Dockerfile` - включен диагностический скрипт
-   ✅ `README.md` - обновлены инструкции и добавлено предупреждение о volume linking

## ⚠️ ВАЖНОЕ ИЗМЕНЕНИЕ в startup.sh

**Старая логика (НЕПРАВИЛЬНО):**

```bash
ln -sfn /runpod-volume/ComfyUI /comfyui  # Заменяет ВСЮ папку!
```

**Новая логика (ПРАВИЛЬНО):**

```bash
rm -rf /comfyui/models
ln -sfn /runpod-volume/ComfyUI/models /comfyui/models  # Только модели!
```

## Результат

После исправления вы должны увидеть:

```
🔌 Проверка custom nodes:
✅ Custom nodes найдены:
   ComfyUI_essentials
   ComfyUI-VideoHelperSuite

✅ Модели подключены: /runpod-volume/ComfyUI/models -> /comfyui/models
✅ Найден: /comfyui/models/unet/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
✅ Найден: /comfyui/models/unet/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
...
🎉 Все необходимые модели найдены!
```
