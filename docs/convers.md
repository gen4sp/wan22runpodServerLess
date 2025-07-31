## Что ломается в треде — краткий чек-лист проблем

| Категория                   | Типовая ошибка                                                         | Причина                                             | Быстрый фикс                                                                                                                                                             |
| --------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Лоры**                    | `Value not in list … wan\Wan21_T2V_*`                                  | Неправильный путь или версия LightX2V-LoRA          | Положить `Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors` (или свежую rank-64) в `/comfyui/models/loras` и **подключить к обоим UNet'ам** ([Reddit][1]) |
| **Шаги (KSampler)**         | «High/Low steps» путаются → кривая денойза                             | Оба Sampler'а ждут _общий_ счётчик                  | Для 6 шагов ставим `0-3` и `3-6` (пределы), а `steps` в каждом Sampler’е = 6 ([Reddit][2])                                                                               |
| **CUDA**                    | `CUDA error: no kernel image is available for execution on the device` | Бинарные колёса Torch/xFormers собраны без sm_90/91 | Использовать Torch ≥ 2.8.0 + cu128 и готовый `xformers 0.0.31.post1` с того же репо WHL (уже содержит sm90)                                                              |
| **OOM на 5090**             | Падает при 1280×720×121 кадр                                           | 14B-fp8 сразу грузит 2 UNet’а                       | Снизить до ≤ 1072×608 **или** вставить `torch.compile` узел – минус \~50 % VRAM ([Reddit][3])                                                                            |
| **Бесполезная LoRA-Reward** | Hunyuan Reward не применяется                                          | Архитектура WAN ≠ MPS                               | Удаляем или ставим 0 strength — пользы нет ([Reddit][1])                                                                                                                 |

---

## Мини-инструкция: как поднять WAN 2.2 (T2V/I2V) на Runpod + ComfyUI + RTX 5090

1. **Выбираем образ**

    ```bash
    FROM runpod/worker-comfyui:5.3.0-base
    ```

    > Он уже содержит Comfy 0.3.46, Python 3.11 и CUDA 12.8.

2. **Старт-скрипт (mount + deps)**

    ```bash
    bash -c '
    ln -sfn /runpod-volume/ComfyUI /workspace/ComfyUI
    pip install --force-reinstall \
      --index-url https://download.pytorch.org/whl/cu128 \
      torch==2.8.0 torchvision==0.19.0 torchaudio==2.3.0
    pip install -U xformers --index-url https://download.pytorch.org/whl/cu128
    # flash-attn по желанию
    exec /start.sh
    '
    ```

3. **Модели и директории**

    | Тип       | Файл                                                              | Папка                   |
    | --------- | ----------------------------------------------------------------- | ----------------------- |
    | UNet-High | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`                | `/comfyui/models/unet`  |
    | UNet-Low  | `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`                 | `/comfyui/models/unet`  |
    | VAE       | `wan_2.1_vae.safetensors`                                         | `/comfyui/models/vae`   |
    | CLIP      | `umt5_xxl_fp8_e4m3fn_scaled.safetensors`                          | `/comfyui/models/clip`  |
    | LoRA      | `Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors` | `/comfyui/models/loras` |

4. **Импортируем готовый workflow**
   JSON-файл из gist’а автора («fast_image_to_video_wan22_14B.json») загружаем через _Load_ в ComfyUI ([Gist][4]).

5. **Правим самплеры под «6 шагов за 60 с»**

    - `KSampler-High` – `steps=6`, `start=0`, `end=3`
    - `KSampler-Low` – `steps=6`, `start=3`, `end=6`
    - Scheduler: `UniPC/Simple`, `cfg=1.5`
    - Базовое разрешение — `832×480`, `fps=15`. Длиннее/выше — после апскейла.

6. **Опции экономии VRAM**

    ```bash
    export TORCH_COMPILE=1           # Узел torch.compile
    export TORCH_CUDA_ARCH_LIST="9.0"
    ```

    torch.compile в узле Comfy сокращает VRAM на \~40–50 % на 14B-fp8 ([Reddit][3]).

7. **Типовые команды RunPod при создании Endpoint**

    ```json
    {
        "dockerCommand": "bash -c 'ln -sf /runpod-volume/ComfyUI /workspace/ComfyUI && exec /start.sh'",
        "gpuTypeId": "NVIDIA_GEFORCE_RTX_5090",
        "volumeMounts": [{ "name": "comfyvol", "mountPath": "/runpod-volume" }]
    }
    ```

---

### Если всё же ловите ошибки

| Сообщение                                       | Решение                                                                                                                  |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `xformers…sm90 missing`                         | wheel не попал; запустите `pip install -U xformers --index-url https://download.pytorch.org/whl/cu128 --force-reinstall` |
| `ModuleNotFoundError: 'comfy'` при кастом-нодах | Добавьте `pip install comfyui` **до** установки custom-nodes; убедитесь, что PYTHONPATH не ломается                      |
| Черный видео-вывод                              | Проверьте, что оба UNet’а и VAE связаны, steps ≠ 0, LoRA отключена либо strength ≤ 1.5                                   |
| Зависает компиляция xformers > 15 мин           | `pip install ninja` и добавьте `MAX_JOBS=$(nproc)`; на 16 vCPU уходит \~8 мин                                            |

---

### TL;DR

1. **Torch 2.8 + cu128** + готовый **xformers 0.0.31.post1** → поддержка sm_90.
2. **Два UNet’а** (high/low) + **двойная LoRA** LightX2V.
3. **6 сампл-шагов**, 480p, `torch.compile` узел — 60 с на одном RTX 5090.
4. Большие разрешения требуют либо BlockSwap/Kijai-wrapper, либо меньше кадров.

Следуя этим пунктам, воспроизвести результаты из треда можно с первой попытки и без «CUDA kernel»-адов. Удачной генерации!

[1]: https://www.reddit.com/r/StableDiffusion/comments/1mbyna7/wan_22_generated_in_60_seconds_on_rtx_5090_and/ "Wan 2.2 - Generated in ~60 seconds on RTX 5090 and the quality is absolutely outstanding. : r/StableDiffusion"
[2]: https://www.reddit.com/r/StableDiffusion/comments/1mbyna7/comment/n5px0cj/?utm_content=share_button&utm_medium=web3x&utm_name=web3xcss&utm_source=share&utm_term=1 "Wan 2.2 - Generated in ~60 seconds on RTX 5090 and the quality is absolutely outstanding. : r/StableDiffusion"
[3]: https://www.reddit.com/r/StableDiffusion/comments/1mbhdt5/first_test_i2v_wan_22/ "First test I2V Wan 2.2 : r/StableDiffusion"
[4]: https://gist.github.com/Art9681/91394be3df4f809ca5d008d219fbc5f2 "Fast image to video generation in WAN 2.2 · GitHub"
