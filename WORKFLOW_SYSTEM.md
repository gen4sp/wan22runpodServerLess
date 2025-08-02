# Система Воркфлоу для RunPod Handler

## Обзор

Система воркфлоу позволяет использовать разные типы обработки в зависимости от потребностей. Хендлер теперь поддерживает динамическую загрузку различных воркфлоу вместо жестко запрограммированного WAN 2.2.

## Структура

```
workflows/
├── __init__.py          # Экспорты модуля
├── base.py             # Базовый класс WorkflowBase
├── loader.py           # Система загрузки и реестр воркфлоу
├── wan22.py            # Воркфлоу WAN 2.2
└── simple_test.py      # Простой тестовый воркфлоу
```

## Использование

### Основные параметры

```json
{
    "input": {
        "prompt": "Текстовое описание",
        "workflow": "имя_воркфлоу",
        "image": "base64_изображение (опционально)",
        "options": {
            "width": 832,
            "height": 832,
            "steps": 6,
            "cfg": 1.0
        }
    }
}
```

### Доступные воркфлоу

1. **wan22** / **wan2.2** / **default** - WAN 2.2 для генерации видео

    - Поддерживает T2V (Text-to-Video)
    - Поддерживает I2V (Image-to-Video)
    - Опции: width, height, length, cfg, steps, frame_rate, shift

2. **test** / **simple** - Простой тестовый воркфлоу
    - Поддерживает только I2I (Image-to-Image)
    - Опции: width, height, steps, cfg, sampler_name, scheduler

### Получение списка воркфлоу

```json
{
    "input": {
        "action": "list_workflows"
    }
}
```

## Создание нового воркфлоу

### 1. Создайте класс воркфлоу

```python
from workflows.base import WorkflowBase
from typing import Dict, Any, Optional

class MyWorkflow(WorkflowBase):
    def __init__(self):
        super().__init__()
        self.name = "My Custom Workflow"
        self.version = "1.0"

    def get_default_options(self) -> Dict[str, Any]:
        return {
            'width': 512,
            'height': 512,
            'steps': 20
        }

    def supports_t2v(self) -> bool:
        return False

    def supports_i2v(self) -> bool:
        return True

    def create_workflow(self, prompt: str, image_filename: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        validated_options = self.validate_options(options or {})

        # Создайте структуру воркфлоу для ComfyUI
        workflow = {
            # Ваша логика воркфлоу здесь
        }

        return workflow
```

### 2. Зарегистрируйте воркфлоу

В `workflows/loader.py`:

```python
from .my_workflow import MyWorkflow

def _register_default_workflows(self):
    # ... существующие регистрации
    self.register("my_workflow", MyWorkflow)
```

## Примеры использования

### WAN 2.2 Text-to-Video

```json
{
    "input": {
        "prompt": "A beautiful mountain landscape with flowing rivers",
        "workflow": "wan22",
        "options": {
            "width": 832,
            "height": 832,
            "length": 81,
            "steps": 6,
            "cfg": 1.0
        }
    }
}
```

### WAN 2.2 Image-to-Video

```json
{
    "input": {
        "prompt": "Transform this into a flowing animation",
        "workflow": "wan2.2",
        "image": "data:image/png;base64,...",
        "options": {
            "length": 49,
            "steps": 8
        }
    }
}
```

### Простой тест

```json
{
    "input": {
        "prompt": "A beautiful sunset",
        "workflow": "test",
        "options": {
            "width": 512,
            "height": 512,
            "steps": 4
        }
    }
}
```

## Ответ API

```json
{
  "video": "base64_encoded_video",  // или "image" для статичных воркфлоу
  "filename": "generated_file.mp4",
  "prompt_id": "12345",
  "files_count": 1,
  "workflow_used": "wan22",
  "workflow_info": {
    "name": "WAN 2.2",
    "version": "2.2",
    "supports_t2v": true,
    "supports_i2v": true,
    "default_options": {...}
  }
}
```

## Обратная совместимость

Если параметр `workflow` не указан, используется воркфлоу по умолчанию (WAN 2.2). Это обеспечивает совместимость с существующими интеграциями.

## Файлы тестирования

-   `test_input.json` - Основной тест с WAN 2.2
-   `test_workflows.json` - Набор тестов для разных воркфлоу

## Логирование

Система записывает подробные логи о:

-   Выбранном воркфлоу
-   Режиме работы (T2V/I2V)
-   Параметрах генерации
-   Результатах обработки
