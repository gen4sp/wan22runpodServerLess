#!/bin/bash

# Скрипт диагностики Volume для WAN 2.2 RunPod Worker
# Помогает понять где находятся модели и как их правильно подключить

echo "🔍 Диагностика Volume для WAN 2.2"
echo "================================="

# Проверяем основные mount points
echo "📁 Проверка mount points:"
mount | grep runpod || echo "   RunPod volume не найден в mount points"

# Проверяем директории
echo ""
echo "📂 Проверка директорий:"
for dir in "/runpod-volume" "/runpod-volume/ComfyUI" "/runpod-volume/models" "/comfyui"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir существует"
        echo "   Размер: $(du -sh "$dir" 2>/dev/null | cut -f1)"
        echo "   Файлов: $(find "$dir" -type f 2>/dev/null | wc -l)"
    else
        echo "❌ $dir не существует"
    fi
done

# Ищем модели .safetensors
echo ""
echo "🔍 Поиск моделей .safetensors:"
echo "В /runpod-volume:"
find /runpod-volume -name "*.safetensors" -type f 2>/dev/null | while read file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    echo "✅ $file ($size)"
done

echo ""
echo "В /comfyui:"
find /comfyui -name "*.safetensors" -type f 2>/dev/null | while read file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    echo "✅ $file ($size)"
done

# Проверяем custom nodes
echo ""
echo "🔌 Проверка custom nodes:"
if [ -d "/comfyui/custom_nodes" ]; then
    echo "✅ Папка custom_nodes существует"
    custom_nodes=(
        "ComfyUI_essentials"
        "ComfyUI-VideoHelperSuite" 
        "ComfyUI-WAN"
        "ComfyUI-WanStartEndFramesNative"
        "ComfyUI_IPAdapter_plus"
    )
    
    for node in "${custom_nodes[@]}"; do
        if [ -d "/comfyui/custom_nodes/$node" ]; then
            echo "  ✅ $node установлен"
        else
            echo "  ❌ $node отсутствует"
        fi
    done
else
    echo "❌ Папка custom_nodes не найдена!"
    echo "   Это означает что volume полностью перезаписал ComfyUI"
fi

# Проверяем конкретные требуемые файлы
echo ""
echo "🎯 Проверка требуемых моделей:"
required_files=(
    "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    "wan_2.1_vae.safetensors"
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"
)

for filename in "${required_files[@]}"; do
    echo "Поиск: $filename"
    found_paths=$(find /runpod-volume /comfyui -name "$filename" -type f 2>/dev/null)
    if [ -n "$found_paths" ]; then
        echo "$found_paths" | while read path; do
            size=$(ls -lh "$path" | awk '{print $5}')
            echo "  ✅ $path ($size)"
        done
    else
        echo "  ❌ Не найден"
    fi
done

# Рекомендации
echo ""
echo "💡 Рекомендации по исправлению:"
echo "================================="

# Проверяем если модели в volume есть, но не там где ожидается
models_in_volume=$(find /runpod-volume -name "*.safetensors" -type f 2>/dev/null | wc -l)
models_in_comfyui=$(find /comfyui -name "*.safetensors" -type f 2>/dev/null | wc -l)

if [ "$models_in_volume" -gt 0 ] && [ "$models_in_comfyui" -eq 0 ]; then
    echo "🔧 Модели найдены в volume, но не подключены к /comfyui"
    echo "   Возможные решения:"
    echo "   1. Переместите модели в /runpod-volume/ComfyUI/models/"
    echo "   2. Или создайте правильную структуру папок:"
    echo "      /runpod-volume/ComfyUI/models/unet/"
    echo "      /runpod-volume/ComfyUI/models/vae/"
    echo "      /runpod-volume/ComfyUI/models/clip/"
    echo "      /runpod-volume/ComfyUI/models/loras/wan/"
    echo "   3. Перезапустите контейнер после исправления структуры"
elif [ "$models_in_volume" -eq 0 ]; then
    echo "❌ Модели не найдены в volume"
    echo "   Загрузите модели в Volume через RunPod интерфейс"
elif [ "$models_in_comfyui" -gt 0 ]; then
    echo "✅ Модели успешно подключены!"
fi

# Проверка custom nodes
if [ ! -d "/comfyui/custom_nodes" ] || [ -z "$(ls -A /comfyui/custom_nodes 2>/dev/null)" ]; then
    echo ""
    echo "❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Custom nodes отсутствуют!"
    echo "   Это означает что volume неправильно подключен и перезаписал ComfyUI"
    echo "   Решение: исправьте логику подключения volume в startup.sh"
    echo "   Volume должен линковаться ТОЛЬКО на /comfyui/models, а не на всю папку /comfyui"
fi

# Показываем права доступа
echo ""
echo "🔒 Проверка прав доступа:"
ls -la /runpod-volume/ 2>/dev/null | head -5 || echo "   Не удается проверить права на /runpod-volume"

echo ""
echo "🏁 Диагностика завершена!"