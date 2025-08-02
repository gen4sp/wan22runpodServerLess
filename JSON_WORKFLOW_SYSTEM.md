# Система произвольных JSON воркфлоу

## Обзор

Новая система принимает **полные JSON воркфлоу ComfyUI** вместо предустановленных шаблонов. Система автоматически анализирует тип воркфлоу и обрабатывает входные данные соответственно.

## Поддерживаемые типы воркфлоу

1. **T2V (Text-to-Video)** - генерация видео из текста
2. **T2I (Text-to-Image)** - генерация изображения из текста
3. **Img2Img (Image-to-Image)** - преобразование изображения
4. **Video Upscale** - апскейл видео

## Формат запроса

```json
{
    "input": {
        "workflow": {
            /* ПОЛНЫЙ JSON ВОРКФЛОУ ComfyUI */
        },
        "prompt": "Текстовый промпт (опционально)",
        "image": "data:image/png;base64,... (опционально)",
        "video": "data:video/mp4;base64,... (опционально)",
        "options": {
            "seed": 12345,
            "steps": 20,
            "cfg": 7.0
        }
    }
}
```

## Обязательные параметры

-   **workflow** - полный JSON воркфлоу ComfyUI (обязательно)

## Входные данные по типам

### T2V (Text-to-Video)

-   **Обязательно**: `prompt`
-   **Опционально**: `image` (для I2V режима)
-   **Пример узлов**: `CLIPTextEncode`, `WanImageToVideo`, `VHS_VideoCombine`

### T2I (Text-to-Image)

-   **Обязательно**: `prompt`
-   **Пример узлов**: `CLIPTextEncode`, `KSampler`, `EmptyLatentImage`, `SaveImage`

### Img2Img (Image-to-Image)

-   **Обязательно**: `image`
-   **Опционально**: `prompt`
-   **Пример узлов**: `LoadImage`, `KSampler`, `SaveImage`

### Video Upscale

-   **Обязательно**: `video`
-   **Пример узлов**: `VHS_LoadVideo`, `ImageUpscaleWithModel`, `VHS_VideoCombine`

## Автоматическая обработка

Система автоматически:

1. **Анализирует тип воркфлоу** по узлам ComfyUI
2. **Валидирует входные данные** для соответствия типу
3. **Сохраняет медиафайлы** (изображения/видео) в ComfyUI input
4. **Обновляет промпты** в узлах `CLIPTextEncode`
5. **Применяет опции** (seed, steps, cfg и др.)
6. **Обновляет пути файлов** в узлах `LoadImage`/`LoadVideo`

## Примеры использования

### T2V с WAN 2.2

```json
{
    "input": {
        "prompt": "A beautiful mountain landscape with flowing rivers",
        "options": { "seed": 12345, "steps": 6, "cfg": 1.0 },
        "workflow": {
            "6": {
                "inputs": { "text": "placeholder", "clip": ["38", 0] },
                "class_type": "CLIPTextEncode",
                "_meta": { "title": "CLIP Text Encode (Positive)" }
            },
            "50": {
                "inputs": {
                    "width": 832,
                    "height": 832,
                    "length": 81,
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "vae": ["39", 0],
                    "start_image": ["68", 0]
                },
                "class_type": "WanImageToVideo"
            },
            "64": {
                "inputs": {
                    "frame_rate": 24,
                    "format": "video/h264-mp4",
                    "images": ["8", 0]
                },
                "class_type": "VHS_VideoCombine"
            }
        }
    }
}
```

### T2I с Stable Diffusion

```json
{
    "input": {
        "prompt": "A beautiful sunset over the ocean",
        "options": { "seed": 98765, "steps": 20, "cfg": 7.0 },
        "workflow": {
            "1": {
                "inputs": { "text": "placeholder", "clip": ["4", 1] },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "seed": 0,
                    "steps": 20,
                    "cfg": 7.0,
                    "model": ["4", 0],
                    "positive": ["1", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "5": {
                "inputs": { "width": 1024, "height": 1024 },
                "class_type": "EmptyLatentImage"
            },
            "7": {
                "inputs": { "images": ["6", 0] },
                "class_type": "SaveImage"
            }
        }
    }
}
```

### Img2Img

```json
{
    "input": {
        "prompt": "Transform into painting style",
        "image": "data:image/png;base64,iVBORw0KGgo...",
        "options": { "denoise": 0.75, "steps": 15 },
        "workflow": {
            "5": {
                "inputs": { "image": "placeholder.png" },
                "class_type": "LoadImage"
            },
            "3": {
                "inputs": {
                    "denoise": 0.75,
                    "steps": 15,
                    "positive": ["1", 0],
                    "latent_image": ["7", 0]
                },
                "class_type": "KSampler"
            },
            "9": {
                "inputs": { "images": ["6", 0] },
                "class_type": "SaveImage"
            }
        }
    }
}
```

### Video Upscale

```json
{
    "input": {
        "video": "data:video/mp4;base64,AAAAHGZ0eXBpc2...",
        "options": { "scale_factor": 2.0 },
        "workflow": {
            "1": {
                "inputs": { "video": "placeholder.mp4" },
                "class_type": "VHS_LoadVideo"
            },
            "2": {
                "inputs": {
                    "upscale_model_name": "RealESRGAN_x2plus.pth",
                    "image": ["1", 0]
                },
                "class_type": "ImageUpscaleWithModel"
            },
            "3": {
                "inputs": {
                    "frame_rate": 24,
                    "format": "video/h264-mp4",
                    "images": ["2", 0]
                },
                "class_type": "VHS_VideoCombine"
            }
        }
    }
}
```

## Анализ воркфлоу

Для получения информации о воркфлоу:

```json
{
    "input": {
        "action": "analyze_workflow",
        "workflow": {
            /* ваш воркфлоу */
        }
    }
}
```

Ответ:

```json
{
    "workflow_info": {
        "workflow_type": "text_to_video",
        "node_count": 10,
        "node_types": ["CLIPTextEncode", "WanImageToVideo", "VHS_VideoCombine"],
        "expected_output": "video",
        "supports_prompt": true,
        "requires_image": false,
        "requires_video": false
    }
}
```

## Ответ API

```json
{
    "video": "base64_encoded_video", // или "image" для статичных воркфлоу
    "filename": "generated_file.mp4",
    "prompt_id": "12345",
    "files_count": 1,
    "workflow_type": "text_to_video",
    "metadata": {
        "workflow_type": "text_to_video",
        "has_prompt": true,
        "has_image": false,
        "has_video": false,
        "node_count": 10,
        "options_applied": true
    }
}
```

## Детекция типов воркфлоу

Система анализирует узлы ComfyUI для определения типа:

### T2V (Text-to-Video)

-   Есть `CLIPTextEncode` И `VHS_VideoCombine`/`WanImageToVideo`
-   НЕТ `VHS_LoadVideo`

### T2I (Text-to-Image)

-   Есть `CLIPTextEncode` И `SaveImage`/`PreviewImage`
-   НЕТ `LoadImage` И НЕТ `VHS_VideoCombine`

### Img2Img (Image-to-Image)

-   Есть `LoadImage` И `SaveImage`
-   НЕТ `VHS_VideoCombine`

### Video Upscale

-   Есть `VHS_LoadVideo` И `ImageUpscaleWithModel`/`VideoUpscaler` И `VHS_VideoCombine`

## Обработка файлов

### Входные файлы

-   Изображения сохраняются как `input_image_{timestamp}.png`
-   Видео сохраняются как `input_video_{timestamp}.mp4`
-   Файлы помещаются в `/comfyui/input/`

### Выходные файлы

-   Видео: ищет в `outputs.*.gifs` и `outputs.*.videos`
-   Изображения: ищет в `outputs.*.images`

## Ошибки и валидация

### Типичные ошибки:

-   `"Параметр 'workflow' обязателен"` - не передан JSON воркфлоу
-   `"T2V воркфлоу требует текстовый промпт"` - нет промпта для T2V
-   `"Img2Img воркфлоу требует входное изображение"` - нет изображения для Img2Img
-   `"Video Upscale воркфлоу требует входное видео"` - нет видео для апскейла

## Тестирование

Запуск тестов:

```bash
python3 test_workflows.py
```

Тестовые файлы:

-   `test_input.json` - основной тест с WAN 2.2
-   `test_json_workflows.json` - примеры всех типов воркфлоу

## Ключевые преимущества

-   🎯 **Гибкость** - любые воркфлоу ComfyUI
-   🔍 **Автоанализ** - определение типа по узлам
-   ✅ **Валидация** - проверка соответствия входных данных
-   🔧 **Автообработка** - обновление промптов, файлов, опций
-   📊 **Метаданные** - подробная информация о процессе
-   🚀 **Производительность** - прямая передача в ComfyUI без преобразований
