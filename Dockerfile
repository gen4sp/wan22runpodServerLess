FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

ENV CM_NETWORK_MODE=offline \
    COMFYUI_DISABLE_VERSION_CHECK=1 \
    TORCH_AUDIO_BACKEND=soundfile \
    TORCHAUDIO_BACKEND=soundfile \
    DISABLE_TORCHAUDIO_CUDA_CHECK=1 \
    CM_DISABLE_TORCHAUDIO=1 \
    PYTHONDONTWRITEBYTECODE=1
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

# РАННИЙ ПАТЧ torchaudio - создаем sitecustomize.py для автоматического патча
RUN mkdir -p /usr/local/lib/python3.11/site-packages/ && \
    cat > /usr/local/lib/python3.11/site-packages/sitecustomize.py << 'EOF'
import sys
import types

# Создаем полный mock для torchaudio при каждом запуске Python
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

# Применяем патч немедленно при импорте Python
create_mock_torchaudio()
EOF

# Копируем скрипты для патчей
COPY torchaudio_patch.py /tmp/torchaudio_patch.py
COPY remove_torchaudio.py /tmp/remove_torchaudio.py

# Полностью удаляем torchaudio и заменяем на mock
RUN python3 /tmp/remove_torchaudio.py

# Применяем дополнительный патч
RUN python3 /tmp/torchaudio_patch.py

# Клонируем и устанавливаем ComfyUI
WORKDIR /
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui

# Устанавливаем зависимости ComfyUI
WORKDIR /comfyui
RUN pip install -r requirements.txt

# Предустанавливаем все критические зависимости ДО установки ComfyUI-Manager
# Удаляем старые версии и устанавливаем заново
RUN pip uninstall -y gitpython GitPython || true && \
    pip install --no-cache-dir --upgrade --force-reinstall gitpython>=3.1.40 requests aiohttp pyyaml

# Устанавливаем ComfyUI Manager для управления custom nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /comfyui/custom_nodes/ComfyUI-Manager

# Устанавливаем зависимости ComfyUI-Manager с принудительной переустановкой
RUN cd /comfyui/custom_nodes/ComfyUI-Manager && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt || \
    (echo "Fallback установка зависимостей Manager" && pip install --no-cache-dir gitpython requests aiohttp pyyaml)

# Копируем handler и зависимости
COPY rp_handler.py /
COPY requirements.txt /
COPY workflows/ /workflows/
RUN pip install -r /requirements.txt

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