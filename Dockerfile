FROM runpod/worker-comfyui:5.3.0-base

# Обновляем PyTorch и xformers для поддержки RTX 5090 (sm_90)
RUN pip install --force-reinstall \
    --index-url https://download.pytorch.org/whl/cu128 \
    torch==2.8.0 torchvision==0.19.0 torchaudio==2.3.0

RUN pip install -U xformers==0.0.31.post1 --index-url https://download.pytorch.org/whl/cu128

# Устанавливаем flash-attention для дополнительной оптимизации
RUN pip install flash-attn --no-build-isolation

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