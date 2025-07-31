FROM runpod/worker-comfyui:5.3.0-base

# Обновляем PyTorch и xformers для поддержки RTX 5090 (sm_90)
RUN pip install --force-reinstall \
    --index-url https://download.pytorch.org/whl/test/cu128 \
    torch==2.8.0 torchvision torchaudio

RUN pip install -U xformers==0.0.31.post1 --index-url https://download.pytorch.org/whl/test/cu128

# Устанавливаем flash-attention для дополнительной оптимизации
RUN pip install flash-attn --no-build-isolation

# ---------------- Comfy custom nodes ------------
WORKDIR /comfyui
RUN comfy-node-install \
        ComfyUI-WAN \
        ComfyUI_essentials \
        ComfyUI-VideoHelperSuite \
        ComfyUI_IPAdapter_plus \
        ComfyUI-WanStartEndFramesNative \
    && ls -la /comfyui/custom_nodes/ \
    && echo "Проверяем установленные custom nodes:" \
    && ls -la /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/ || echo "VideoHelperSuite не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI-WAN/ || echo "ComfyUI-WAN не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI_essentials/ || echo "ComfyUI_essentials не найден!"

# Копируем handler и зависимости
COPY rp_handler.py /
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Переменные окружения для оптимизации
ENV TORCH_COMPILE=1
ENV TORCH_CUDA_ARCH_LIST="9.0"

# Устанавливаем рабочую директорию
WORKDIR /

# Копируем startup скрипт
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Команда запуска через startup скрипт
CMD ["/startup.sh"]