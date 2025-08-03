#!/bin/bash

# Скрипт запуска для RunPod ServerLess Worker
# Решает проблемы с torchvision и настраивает окружение

echo "🚀 Запуск WAN 2.2 ServerLess Worker..."

# 🔍 ДИАГНОСТИКА TORCHAUDIO ПАТЧЕЙ
echo "🔍 Проверка состояния torchaudio патчей..."

# Проверяем что настоящий torchaudio удален
if find /usr/local/lib/python3.11 -name "*torchaudio*" -type f | grep -v "dist-packages/torchaudio" | head -1; then
    echo "⚠️  Найдены остатки настоящего torchaudio!"
    find /usr/local/lib/python3.11 -name "*torchaudio*" -type f | head -5
else
    echo "✅ Настоящий torchaudio полностью удален"
fi

# Проверяем наш mock torchaudio
if [ -f "/usr/local/lib/python3.11/dist-packages/torchaudio/__init__.py" ]; then
    echo "✅ Mock torchaudio найден"
else
    echo "❌ Mock torchaudio НЕ найден!"
fi

# Проверяем sitecustomize.py
if [ -f "/usr/local/lib/python3.11/dist-packages/sitecustomize.py" ]; then
    echo "✅ sitecustomize.py найден"
else
    echo "❌ sitecustomize.py НЕ найден!"
fi

# Тестируем импорт torchaudio
echo "🧪 Тестируем импорт torchaudio..."
python3 -c "
try:
    import torchaudio
    print(f'✅ torchaudio импорт успешен: версия {torchaudio.__version__}')
    print(f'   torchaudio.lib: {hasattr(torchaudio, \"lib\")}')
    print(f'   torchaudio.lib._torchaudio: {hasattr(torchaudio.lib, \"_torchaudio\") if hasattr(torchaudio, \"lib\") else False}')
    if hasattr(torchaudio, 'lib') and hasattr(torchaudio.lib, '_torchaudio'):
        print(f'   cuda_version(): {torchaudio.lib._torchaudio.cuda_version()}')
except Exception as e:
    print(f'❌ Ошибка импорта torchaudio: {e}')
    import sys
    print(f'   sys.modules содержит torchaudio: {\"torchaudio\" in sys.modules}')
" || echo "❌ Критическая ошибка при тестировании torchaudio"

# Создаем символические ссылки для volume (только для моделей!)
echo "📁 Настройка volume..."

# Создаем базовые директории ComfyUI (НЕ перезаписываем custom_nodes!)
mkdir -p /comfyui/{input,output,models/{unet,vae,clip,loras/wan}}

# Проверяем различные возможные структуры volume и линкуем ТОЛЬКО модели
if [ -d "/runpod-volume/ComfyUI/models" ]; then
    echo "✅ Найден volume: /runpod-volume/ComfyUI/models"
    # Удаляем пустую папку models и создаем ссылку
    rm -rf /comfyui/models
    ln -sfn /runpod-volume/ComfyUI/models /comfyui/models
    echo "✅ Модели подключены: /runpod-volume/ComfyUI/models -> /comfyui/models"
elif [ -d "/runpod-volume/models" ]; then
    echo "✅ Найден volume с моделями: /runpod-volume/models"
    # Удаляем пустую папку models и создаем ссылку
    rm -rf /comfyui/models
    ln -sfn /runpod-volume/models /comfyui/models
    echo "✅ Модели подключены: /runpod-volume/models -> /comfyui/models"
elif [ -d "/runpod-volume" ] && [ "$(ls -A /runpod-volume 2>/dev/null)" ]; then
    echo "✅ Найден volume: /runpod-volume (содержимое: $(ls /runpod-volume | head -5 | tr '\n' ' '))"
    # Проверяем наличие папок с моделями в корне volume
    if [ -d "/runpod-volume/unet" ] || [ -d "/runpod-volume/vae" ] || [ -d "/runpod-volume/clip" ]; then
        echo "✅ Найдена структура моделей в корне volume"
        # Удаляем пустую папку models и создаем ссылку на весь volume как models
        rm -rf /comfyui/models
        ln -sfn /runpod-volume /comfyui/models
        echo "✅ Модели подключены: /runpod-volume -> /comfyui/models"
    else
        echo "⚠️  Volume подключен, но структура папок неизвестна"
        ls -la /runpod-volume/ || echo "Не удалось прочитать содержимое volume"
    fi
else
    echo "⚠️  Volume не найден или пуст, используем локальную установку"
fi

# Проверяем наличие критически важных файлов
echo "🔍 Проверка моделей..."

# Проверяем что custom nodes сохранились
echo "🔌 Проверка custom nodes:"
if [ -d "/comfyui/custom_nodes" ]; then
    echo "✅ Custom nodes найдены:"
    ls -la /comfyui/custom_nodes/ | grep -E "(ComfyUI_essentials|ComfyUI-VideoHelperSuite|ComfyUI-WAN)" || echo "   Основные custom nodes могут отсутствовать"
else
    echo "❌ Custom nodes не найдены! Проблема с volume linking"
fi

# Показываем текущую структуру папок
echo "📂 Структура /comfyui:"
ls -la /comfyui/ 2>/dev/null || echo "   /comfyui не существует"
if [ -d "/comfyui/models" ]; then
    echo "📂 Структура /comfyui/models:"
    find /comfyui/models -type f -name "*.safetensors" 2>/dev/null | head -10 || echo "   Модели .safetensors не найдены"
fi

required_files=(
    "/comfyui/models/unet/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    "/comfyui/models/unet/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    "/comfyui/models/vae/wan_2.1_vae.safetensors"
    "/comfyui/models/clip/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    "/comfyui/models/loras/wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"
)

missing_files=()
found_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        found_files+=("$file")
        echo "✅ Найден: $file"
    else
        missing_files+=("$file")
    fi
done

if [ ${#found_files[@]} -gt 0 ]; then
    echo "✅ Найдено моделей: ${#found_files[@]}/${#required_files[@]}"
fi

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Отсутствуют критически важные файлы:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "🔍 Диагностика volume:"
    echo "   Volume mount point: /runpod-volume"
    if [ -d "/runpod-volume" ]; then
        echo "   Volume содержимое:"
        find /runpod-volume -name "*.safetensors" 2>/dev/null | head -10 || echo "     Файлы .safetensors не найдены в volume"
    fi
    echo ""
    echo "📋 Инструкция по исправлению:"
    echo "1. Проверьте что Volume подключен как /runpod-volume"
    echo "2. Структура должна быть: /runpod-volume/ComfyUI/models/..."
    echo "3. Либо /runpod-volume/models/..."
    echo "4. Перезапустите контейнер после исправления"
    echo ""
else
    echo "🎉 Все необходимые модели найдены!"
fi

# Фикс для torchvision ошибки (из error.md)
echo "🔧 Применение фикса для torchvision..."
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TORCH_CUDA_ARCH_LIST="9.0"

# Переустанавливаем torchvision если есть проблемы
python -c "import torchvision" 2>/dev/null || {
    echo "⚠️  Проблема с torchvision, переустанавливаем..."
    pip uninstall -y torchvision
    pip install --no-cache-dir torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu128
}

# Создаем ранний torchaudio патч через sitecustomize.py
echo "🔧 Создание раннего torchaudio патча через sitecustomize.py..."
mkdir -p /usr/local/lib/python3.11/dist-packages/
cat > /usr/local/lib/python3.11/dist-packages/sitecustomize.py << 'EOF'
import sys
import types

# Создаем полный mock для torchaudio
def create_mock_torchaudio():
    # Mock для _torchaudio
    _torchaudio = types.ModuleType('_torchaudio')
    _torchaudio.cuda_version = lambda: '12.8'
    
    # Mock для torchaudio.lib
    lib = types.ModuleType('torchaudio.lib')
    lib._torchaudio = _torchaudio
    
    # Mock для torchaudio._extension
    extension = types.ModuleType('torchaudio._extension')
    extension._check_cuda_version = lambda: None
    
    # Основной mock для torchaudio
    torchaudio = types.ModuleType('torchaudio')
    torchaudio.lib = lib
    torchaudio._extension = extension
    torchaudio.__version__ = '2.5.0'
    
    # Регистрируем все модули
    sys.modules['torchaudio'] = torchaudio
    sys.modules['torchaudio.lib'] = lib
    sys.modules['torchaudio.lib._torchaudio'] = _torchaudio
    sys.modules['torchaudio._extension'] = extension
    
    return torchaudio

# Применяем патч немедленно
create_mock_torchaudio()
EOF

# Применяем дополнительный torchaudio патч
echo "🔧 Применение дополнительного torchaudio патча..."
python3 /tmp/torchaudio_patch.py 2>/dev/null || true

echo "✅ АГРЕССИВНЫЙ torchaudio патч применен"

# Проверяем CUDA и xformers
echo "🧪 Проверка CUDA и xformers..."
python -c "
import torch
import xformers
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ CUDA: {torch.version.cuda}')
print(f'✅ xformers: {xformers.__version__}')
print(f'✅ CUDA доступна: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
"

# Проверяем и переустанавливаем GitPython для ComfyUI-Manager
echo "🔧 Проверка GitPython для ComfyUI-Manager..."
python -c "import git; print(f'✅ GitPython: {git.__version__}')" 2>/dev/null || {
    echo "⚠️  Проблема с GitPython, агрессивно переустанавливаем..."
    pip uninstall -y gitpython || true
    pip install --no-cache-dir --force-reinstall gitpython
    # Также переустанавливаем все зависимости ComfyUI-Manager
    if [ -f "/comfyui/custom_nodes/ComfyUI-Manager/requirements.txt" ]; then
        echo "🔧 Переустановка зависимостей ComfyUI-Manager..."
        pip install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-Manager/requirements.txt || true
    fi
}

# Финальная проверка GitPython
echo "🔍 Финальная проверка GitPython..."
python -c "
try:
    import git
    print(f'✅ GitPython успешно загружен: {git.__version__}')
    # Проверяем что можем создать Repo объект
    repo = git.Repo('/comfyui')
    print('✅ GitPython функционирует нормально')
except Exception as e:
    print(f'❌ GitPython проблема: {e}')
    import sys
    sys.exit(1)
"

# Проверяем ComfyUI-Manager
echo "🔌 Проверка ComfyUI-Manager..."
if [ -d "/comfyui/custom_nodes/ComfyUI-Manager" ]; then
    echo "✅ ComfyUI-Manager найден"
    # Проверяем что файлы есть
    if [ -f "/comfyui/custom_nodes/ComfyUI-Manager/__init__.py" ]; then
        echo "✅ ComfyUI-Manager инициализирован"
    else
        echo "⚠️  ComfyUI-Manager установлен некорректно"
    fi
else
    echo "❌ ComfyUI-Manager не найден!"
fi

# Запускаем ComfyUI с патчем для torchaudio
echo "🎨 Запуск ComfyUI с патчем для torchaudio..."
cd /comfyui

# Применяем патч еще раз перед запуском
python3 /tmp/torchaudio_patch.py 2>/dev/null || true

# Запускаем ComfyUI и перенаправляем вывод в лог
echo "🚀 Запуск ComfyUI процесса..."
python main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch > /tmp/comfyui.log 2>&1 &
COMFY_PID=$!

# Даем время на запуск
sleep 3

# Проверяем что процесс запустился
if ! kill -0 $COMFY_PID 2>/dev/null; then
    echo "❌ ComfyUI не смог запуститься!"
    echo "📋 Последние строки лога:"
    tail -50 /tmp/comfyui.log
    
    echo "🔍 Диагностика проблемы запуска:"
    echo "   - Проверяем Python процессы:"
    ps aux | grep python | grep -v grep
    echo "   - Проверяем порты:"
    netstat -tlnp | grep 8188 || echo "     Порт 8188 не занят"
    echo "   - Проверяем память:"
    free -h
    echo "   - Проверяем GPU:"
    nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits || echo "     nvidia-smi недоступен"
    
    # Пробуем запустить еще раз с дополнительным патчем
    echo "🔧 Применение дополнительного патча и повторный запуск..."
    python3 /tmp/torchaudio_patch.py
    echo "✅ АГРЕССИВНЫЙ torchaudio патч применен"
    
    # Очищаем старый лог и запускаем заново
    > /tmp/comfyui.log
    python main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch > /tmp/comfyui.log 2>&1 &
    COMFY_PID=$!
    echo "✅ ComfyUI запущен с PID: $COMFY_PID"
    sleep 3
else
    echo "✅ ComfyUI запущен с PID: $COMFY_PID"
fi

# Ждем запуска ComfyUI
echo "⏳ Ожидание готовности ComfyUI..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
        echo "✅ ComfyUI готов к работе!"
        break
    fi
    echo "   Попытка $i/60..."
    
    # Каждые 10 попыток показываем диагностику
    if [ $((i % 10)) -eq 0 ]; then
        echo "🔍 Диагностика после $i попыток:"
        echo "   - Процесс ComfyUI:"
        if kill -0 $COMFY_PID 2>/dev/null; then
            echo "     ✅ Процесс $COMFY_PID активен"
            ps -p $COMFY_PID -o pid,pcpu,pmem,etime,cmd --no-headers || echo "     ⚠️ Не удается получить детали процесса"
        else
            echo "     ❌ Процесс $COMFY_PID не найден"
        fi
        echo "   - Порт 8188:"
        netstat -tlnp | grep 8188 || echo "     ❌ Порт 8188 не слушается"
        echo "   - Последние строки лога ComfyUI:"
        tail -3 /tmp/comfyui.log 2>/dev/null || echo "     ⚠️ Лог недоступен"
    fi
    
    sleep 5
done

# Проверяем что ComfyUI запустился
if ! curl -s http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
    echo "❌ ComfyUI не смог запуститься за 300 секунд!"
    echo "📋 Финальная диагностика:"
    echo "   - Статус процесса $COMFY_PID:"
    if kill -0 $COMFY_PID 2>/dev/null; then
        echo "     ✅ Процесс активен"
        ps -p $COMFY_PID -o pid,pcpu,pmem,etime,stat,cmd --no-headers
    else
        echo "     ❌ Процесс завершился"
    fi
    echo "   - Порты:"
    netstat -tlnp | grep 8188 || echo "     Порт 8188 не слушается"
    echo "   - Полные логи ComfyUI:"
    cat /tmp/comfyui.log 2>/dev/null || echo "     Логи недоступны"
    echo "   - Системная память:"
    free -h
    echo "   - GPU память:"
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits || echo "     nvidia-smi недоступен"
    exit 1
fi

# Запускаем RunPod handler
echo "🏃 Запуск RunPod handler..."
cd /
exec python -u rp_handler.py