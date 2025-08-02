FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

ENV CM_NETWORK_MODE=offline \
    COMFYUI_DISABLE_VERSION_CHECK=1
# Обновляем систему и устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем xformers для поддержки RTX 5090 (sm_90)
# Сначала пробуем установить из PyTorch индекса для CUDA 12.8
RUN pip install -U xformers --index-url https://download.pytorch.org/whl/cu128 || \
    # Если не получилось, устанавливаем из основного PyPI
    pip install -U xformers

# Устанавливаем flash-attention для дополнительной оптимизации
RUN pip install flash-attn --no-build-isolation

# Клонируем и устанавливаем ComfyUI
WORKDIR /
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui

# Устанавливаем зависимости ComfyUI
WORKDIR /comfyui
RUN pip install -r requirements.txt

# Устанавливаем ComfyUI Manager для управления custom nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /comfyui/custom_nodes/ComfyUI-Manager

# Предустанавливаем GitPython для ComfyUI-Manager
RUN pip install --no-cache-dir gitpython==3.1.43

# Устанавливаем необходимые custom nodes
RUN  git clone https://github.com/cubiq/ComfyUI_essentials.git /comfyui/custom_nodes/ComfyUI_essentials \
    && git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite \
    && git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git /comfyui/custom_nodes/ComfyUI_IPAdapter_plus \
    && git clone https://github.com/Flow-two/ComfyUI-WanStartEndFramesNative.git /comfyui/custom_nodes/ComfyUI-WanStartEndFramesNative \
    && git clone https://github.com/EllangoK/ComfyUI-post-processing-nodes.git /comfyui/custom_nodes/ComfyUI-post-processing-nodes \
    && git clone https://github.com/ShmuelRonen/ComfyUI-EmptyHunyuanLatent.git /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent
# Устанавливаем зависимости для custom nodes
RUN cd /comfyui/custom_nodes/ComfyUI_essentials && pip install -r requirements.txt || true
RUN cd /comfyui/custom_nodes/ComfyUI-VideoHelperSuite && pip install -r requirements.txt || true
RUN cd /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && pip install -r requirements.txt || true
RUN cd /comfyui/custom_nodes/ComfyUI-post-processing-nodes && pip install -r requirements.txt || true
RUN cd /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent && pip install -r requirements.txt || true

# Проверяем установленные custom nodes
RUN ls -la /comfyui/custom_nodes/ \
    && echo "Проверяем установленные custom nodes:" \
    && ls -la /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/ || echo "VideoHelperSuite не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI-WAN/ || echo "ComfyUI-WAN не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI_essentials/ || echo "ComfyUI_essentials не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI-post-processing-nodes/ || echo "ComfyUI_essentials не найден!" \
    && ls -la /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent/ || echo "ComfyUI_essentials не найден!"

# Копируем handler и зависимости
COPY rp_handler.py /
COPY requirements.txt /
COPY workflows/ /workflows/
RUN pip install -r /requirements.txt

# Переменные окружения для оптимизации
ENV TORCH_COMPILE=1
ENV TORCH_CUDA_ARCH_LIST="9.0"

# Устанавливаем рабочую директорию
WORKDIR /

# Копируем startup скрипт и диагностику
COPY startup.sh /startup.sh
COPY diagnose_volume.sh /diagnose_volume.sh
RUN chmod +x /startup.sh /diagnose_volume.sh

# Команда запуска через startup скрипт
CMD ["/startup.sh"]