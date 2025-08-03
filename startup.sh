#!/bin/bash

# Скрипт запуска для RunPod ServerLess Worker
# Решает проблемы с torchvision и настраивает окружение

echo "🚀 Запуск WAN 2.2 ServerLess Worker..."

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
echo "🔧 Проверка torchvision..."
python -c "import torchvision; print(f'✅ torchvision: {torchvision.__version__}')" 2>/dev/null || {
    echo "⚠️  Проблема с torchvision, переустанавливаем..."
    pip uninstall -y torchvision
    pip install --no-cache-dir torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu128
    echo "✅ torchvision переустановлен"
}

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

# Проверяем torchaudio mock
echo "🔧 Проверка torchaudio mock..."
if [ -f "/test_torchaudio_fix.py" ]; then
    python /test_torchaudio_fix.py
else
    python -c "
try:
    import torchaudio
    print(f'✅ torchaudio импортирован: {torchaudio.__version__}')
    
    # Проверяем наличие всех необходимых атрибутов
    if hasattr(torchaudio, 'lib'):
        print('✅ torchaudio.lib найден')
    else:
        print('❌ torchaudio.lib отсутствует')
        
    if hasattr(torchaudio, 'transforms'):
        print('✅ torchaudio.transforms найден')
    else:
        print('❌ torchaudio.transforms отсутствует')
        
    if hasattr(torchaudio, 'functional'):
        print('✅ torchaudio.functional найден')
    else:
        print('❌ torchaudio.functional отсутствует')
        
except Exception as e:
    print(f'❌ Ошибка импорта torchaudio: {e}')
    import traceback
    traceback.print_exc()
"
fi

# Запускаем ComfyUI в фоне
echo "🎨 Запуск ComfyUI..."
cd /comfyui
python main.py --listen 0.0.0.0 --port 8188 &
COMFY_PID=$!

# Ждем запуска ComfyUI
echo "⏳ Ожидание готовности ComfyUI..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
        echo "✅ ComfyUI готов к работе!"
        break
    fi
    echo "   Попытка $i/60..."
    sleep 5
done

# Проверяем что ComfyUI запустился
if ! curl -s http://127.0.0.1:8188/system_stats >/dev/null 2>&1; then
    echo "❌ ComfyUI не смог запуститься!"
    echo "📋 Логи ComfyUI:"
    tail -50 /comfyui/comfyui.log 2>/dev/null || echo "Логи недоступны"
    exit 1
fi

# Запускаем RunPod handler
echo "🏃 Запуск RunPod handler..."
cd /
exec python -u rp_handler.py