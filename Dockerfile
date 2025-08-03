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

# 🚨 КРИТИЧЕСКИ ВАЖНО: ПОЛНОСТЬЮ УДАЛЯЕМ TORCHAUDIO ДО УСТАНОВКИ COMFYUI 🚨
# Копируем скрипты для патчей
COPY torchaudio_patch.py /tmp/torchaudio_patch.py
COPY remove_torchaudio.py /tmp/remove_torchaudio.py

# 1. Удаляем torchaudio через pip
RUN pip uninstall -y torchaudio 2>/dev/null || true

# 2. Полностью удаляем все файлы torchaudio из системы
RUN find /usr/local/lib/python3.11 -name "*torchaudio*" -type d -exec rm -rf {} + 2>/dev/null || true
RUN find /usr/local/lib/python3.11 -name "*torchaudio*" -type f -delete 2>/dev/null || true

# 3. Применяем наш remove_torchaudio.py для создания mock
RUN python3 /tmp/remove_torchaudio.py

# 4. РАННИЙ ПАТЧ через sitecustomize.py - копируем ПОСЛЕ удаления настоящего torchaudio
RUN mkdir -p /usr/local/lib/python3.11/dist-packages
COPY sitecustomize.py /usr/local/lib/python3.11/dist-packages/sitecustomize.py

# 5. Применяем дополнительный патч
RUN python3 /tmp/torchaudio_patch.py

# 6. Проверяем что torchaudio теперь mock
RUN python3 -c "
import torchaudio
print(f'✅ torchaudio mock работает: {torchaudio.__version__}')
print(f'✅ torchaudio.lib: {hasattr(torchaudio, \"lib\")}')
print(f'✅ torchaudio.transforms: {hasattr(torchaudio, \"transforms\")}')
print(f'✅ torchaudio.functional: {hasattr(torchaudio, \"functional\")}')
" || echo "❌ torchaudio mock не работает"

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

# Устанавливаем необходимые custom nodes
RUN git clone https://github.com/cubiq/ComfyUI_essentials.git /comfyui/custom_nodes/ComfyUI_essentials && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git /comfyui/custom_nodes/ComfyUI-VideoHelperSuite && \
    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    git clone https://github.com/Flow-two/ComfyUI-WanStartEndFramesNative.git /comfyui/custom_nodes/ComfyUI-WanStartEndFramesNative && \
    git clone https://github.com/EllangoK/ComfyUI-post-processing-nodes.git /comfyui/custom_nodes/ComfyUI-post-processing-nodes && \
    git clone https://github.com/ShmuelRonen/ComfyUI-EmptyHunyuanLatent.git /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent
# Устанавливаем зависимости для custom nodes с обработкой ошибок
RUN cd /comfyui/custom_nodes/ComfyUI_essentials && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости ComfyUI_essentials")

RUN cd /comfyui/custom_nodes/ComfyUI-VideoHelperSuite && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости VideoHelperSuite")

RUN cd /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости IPAdapter_plus")

RUN cd /comfyui/custom_nodes/ComfyUI-post-processing-nodes && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости post-processing-nodes")

RUN cd /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости EmptyHunyuanLatent")

RUN cd /comfyui/custom_nodes/ComfyUI-WanStartEndFramesNative && \
    (pip install -r requirements.txt || echo "Пропускаем зависимости WanStartEndFramesNative")

# Проверяем установленные custom nodes
RUN ls -la /comfyui/custom_nodes/ && \
    echo "Проверяем установленные custom nodes:" && \
    ls -la /comfyui/custom_nodes/ComfyUI-VideoHelperSuite/ || echo "VideoHelperSuite не найден!" && \
    ls -la /comfyui/custom_nodes/ComfyUI_essentials/ || echo "ComfyUI_essentials не найден!" && \
    ls -la /comfyui/custom_nodes/ComfyUI-post-processing-nodes/ || echo "ComfyUI-post-processing-nodes не найден!" && \
    ls -la /comfyui/custom_nodes/ComfyUI-EmptyHunyuanLatent/ || echo "ComfyUI-EmptyHunyuanLatent не найден!" && \
    ls -la /comfyui/custom_nodes/ComfyUI-WanStartEndFramesNative/ || echo "ComfyUI-WanStartEndFramesNative не найден!"

# Копируем handler и зависимости
COPY rp_handler.py /
COPY requirements.txt /
COPY workflows/ /workflows/
COPY test_torchaudio_fix.py /
RUN pip install -r /requirements.txt

# Финальный тест torchaudio после установки всех зависимостей
RUN python3 /test_torchaudio_fix.py

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