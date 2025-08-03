# 🧪 Инструкции по тестированию исправленного образа

## 🐋 Пересборка Docker образа

```bash
# Пересобираем образ с исправлениями
docker build -t wan22-serverless:fixed .

# Или с отладочным выводом
docker build --progress=plain -t wan22-serverless:fixed .
```

## 🔍 Ожидаемые результаты в логах сборки

Должны увидеть:

```
✅ torchaudio mock работает: 2.5.0
```

## 🚀 Тестирование локально

```bash
# Запуск контейнера для тестирования
docker run --rm -it \
  --gpus all \
  -p 8188:8188 \
  wan22-serverless:fixed \
  /bin/bash

# Внутри контейнера проверяем torchaudio
python3 -c "
import torchaudio
print(f'torchaudio версия: {torchaudio.__version__}')
print(f'lib._torchaudio.cuda_version(): {torchaudio.lib._torchaudio.cuda_version()}')
"

# Запускаем startup.sh для проверки диагностики
/startup.sh
```

## 🔍 Ожидаемые результаты диагностики

В startup.sh должны увидеть:

```
🔍 Проверка состояния torchaudio патчей...
✅ Настоящий torchaudio полностью удален
✅ Mock torchaudio найден
✅ sitecustomize.py найден
🧪 Тестируем импорт torchaudio...
✅ torchaudio импорт успешен: версия 2.5.0
   torchaudio.lib: True
   torchaudio.lib._torchaudio: True
   cuda_version(): 12.8
```

## 🎯 Тестирование ComfyUI

Если диагностика прошла успешно, ComfyUI должен запуститься без ошибок:

```
🎨 Запуск ComfyUI...
Starting server
To see the GUI go to: http://0.0.0.0:8188
```

## ❌ Если проблема остается

1. Проверьте логи сборки на наличие ошибок
2. Убедитесь что в логах есть `✅ torchaudio mock работает: 2.5.0`
3. Проверьте что в диагностике все пункты показывают ✅
4. Если ComfyUI всё ещё падает, сохраните полные логи для дальнейшего анализа

## 🔧 Дополнительная диагностика

```bash
# Проверка файловой системы
find /usr/local/lib/python3.11 -name "*torchaudio*" -type f

# Проверка sys.modules
python3 -c "import sys; print([k for k in sys.modules.keys() if 'torchaudio' in k])"
```
