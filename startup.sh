#!/bin/bash

# Скрипт запуска для RunPod ServerLess Worker
# Решает проблемы с torchvision и настраивает окружение

echo "🚀 Запуск WAN 2.2 ServerLess Worker..."

# Создаем символические ссылки для volume
echo "📁 Настройка volume..."
if [ -d "/runpod-volume/ComfyUI" ]; then
    ln -sfn /runpod-volume/ComfyUI /comfyui
    echo "✅ Volume подключен: /runpod-volume/ComfyUI -> /comfyui"
else
    echo "⚠️  Volume не найден, используем локальную установку"
    mkdir -p /comfyui
fi

# Создаем необходимые директории
mkdir -p /comfyui/{input,output,models/{unet,vae,clip,loras/wan},custom_nodes}

# Проверяем наличие критически важных файлов
echo "🔍 Проверка моделей..."
required_files=(
    "/comfyui/models/unet/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    "/comfyui/models/unet/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    "/comfyui/models/vae/wan_2.1_vae.safetensors"
    "/comfyui/models/clip/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    "/comfyui/models/loras/wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Отсутствуют критически важные файлы:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "📋 Инструкция по загрузке моделей:"
    echo "1. Создайте Volume в RunPod"
    echo "2. Загрузите модели в соответствующие папки"
    echo "3. Подключите Volume при создании Endpoint"
    echo ""
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