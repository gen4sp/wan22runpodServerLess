t-==

# WAN 2.2 Image-to-Video RunPod ServerLess Worker

Серверлесс воркер для генерации видео из изображений с помощью WAN 2.2 на RunPod с RTX 5090.

> **\* Примечание про PyTorch 2.8.0:** Официально PyTorch 2.8.0 пока не выпущен, и нужно использовать RC-сборку из тестового репозитория:
>
> Для CUDA 12.8:
>
> ```bash
> pip3 install torch==2.8.0 torchvision torchaudio \
>        --index-url https://download.pytorch.org/whl/test/cu128
> ```
>
> Для CPU:
>
> ```bash
> pip3 install torch==2.8.0 --index-url https://download.pytorch.org/whl/test/cpu
> ```
>
> или использовать образ RunPod nightly/RC 2.8.0.

## Особенности

-   ⚡ Быстрая генерация (~60 секунд на RTX 5090)
-   🎯 Оптимизирован для RTX 5090 (Torch 2.8.0 + xformers)
-   🔧 Автоматическая настройка dual-sampling (high/low noise)
-   📹 Поддержка различных разрешений и длительности видео
-   🚀 torch.compile для экономии VRAM

## Версионирование и релизы

Проект использует автоматизированную систему управления версиями:

```bash
# Создать patch релиз (багфиксы)
make patch

# Создать minor релиз (новые функции)
make minor

# Создать major релиз (breaking changes)
make major
```

Подробнее: [docs/releases.md](docs/releases.md)

## Требования

### Модели (нужно загрузить в RunPod Volume):

```
/comfyui/models/unet/
├─ wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
└─ wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors

/comfyui/models/vae/
└─ wan_2.1_vae.safetensors

/comfyui/models/clip/
└─ umt5_xxl_fp8_e4m3fn_scaled.safetensors

/comfyui/models/loras/wan/
└─ Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors
```

### Custom Nodes для ComfyUI:

-   ComfyUI-WAN (для WanImageToVideo ноды)
-   ComfyUI-VideoHelperSuite (для VHS_VideoCombine)
-   ComfyUI-Essentials (для ImageResize+)

## Сборка и деплой

### 1. Локальная сборка

```bash
docker build -t wan22-worker .
```

### 2. Пуш в Docker Hub

```bash
docker tag wan22-worker your-dockerhub-username/wan22-worker:latest
docker push your-dockerhub-username/wan22-worker:latest
```

### 3. Создание Endpoint в RunPod

-   Image: `your-dockerhub-username/wan22-worker:latest`
-   GPU: `RTX 5090` (обязательно)
-   Container Disk: `50GB+`
-   Volume Mount: `/runpod-volume` → `/comfyui`

## Использование API

### Входные параметры

```json
{
    "input": {
        "prompt": "описание желаемого видео",
        "image": "base64_encoded_image_data",
        "options": {
            "width": 832,
            "height": 832,
            "length": 81,
            "steps": 6,
            "cfg": 1.0,
            "frame_rate": 24,
            "seed": 123456
        }
    }
}
```

#### Описание параметров:

-   `prompt` (обязательно): Текстовое описание желаемого видео
-   `image` (обязательно): Входное изображение в формате base64
-   `options.width/height`: Разрешение видео (рекомендуется 832×832)
-   `options.length`: Количество кадров (81 = ~3.4 сек при 24fps)
-   `options.steps`: Количество шагов семплинга (6 оптимально)
-   `options.cfg`: CFG scale (1.0 рекомендуется)
-   `options.frame_rate`: FPS выходного видео
-   `options.seed`: Seed для воспроизводимости

### Выходные данные

```json
{
    "video": "base64_encoded_video_data",
    "filename": "wan2_2_00001.mp4",
    "prompt_id": "abc123",
    "files_count": 1
}
```

## Оптимизация производительности

### Рекомендуемые настройки:

-   **Разрешение**: 832×832 (оптимально для RTX 5090)
-   **Длительность**: 81 кадр (~3.4 сек)
-   **Steps**: 6 (dual-sampling: 0-3 high, 3-6 low)
-   **CFG**: 1.0

### Экономия VRAM:

-   torch.compile включен автоматически (`TORCH_COMPILE=1`)
-   Для больших разрешений используйте меньше кадров
-   1280×720×121 кадр = ~24GB VRAM
-   832×832×81 кадр = ~16GB VRAM

## Устранение неполадок

### Частые ошибки:

1. **"Could not find a version that satisfies the requirement xformers"**

    - Исправлено в последней версии Dockerfile
    - Используется fallback установка из PyPI если PyTorch индекс недоступен

2. **"ComfyUI API недоступен"**

    - Проверьте, что ComfyUI запущен
    - Увеличьте timeout в wait_for_comfy()

3. **"Value not in list ... wan\\Wan21*T2V*\*"**

    - Проверьте пути к LoRA файлам
    - Убедитесь что LoRA подключена к обоим UNet'ам

4. **"CUDA error: no kernel image"**

    - Используйте только RTX 5090
    - Проверьте установку torch 2.8.0 + cu128

5. **OOM ошибки**
    - Уменьшите разрешение или количество кадров
    - Проверьте включение torch.compile

### Логи:

```bash
# Логи контейнера
docker logs <container_id>

# Логи ComfyUI
tail -f /comfyui/comfyui.log
```

## Поддерживаемые форматы

-   **Входные изображения**: JPG, PNG, WebP
-   **Выходное видео**: MP4 (H.264, yuv420p)
-   **Максимальное разрешение**: 1280×720 (на RTX 5090)
-   **Максимальная длительность**: 121 кадр (~5 сек)

## Версии

-   **ComfyUI**: 0.3.46
-   **PyTorch**: 2.8.0\*
-   **xformers**: 0.0.31.post1+ (auto-selected)
-   **CUDA**: 12.8
-   **WAN**: 2.2 (14B fp8)

> **Примечание**: xformers устанавливается автоматически из доступного источника (PyTorch CUDA индекс или PyPI)

## Лицензия

Этот проект использует модели WAN 2.2, которые могут иметь собственные лицензионные ограничения.
