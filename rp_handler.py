#!/usr/bin/env python3

import runpod
import requests
import json
import base64
import io
import time
from PIL import Image
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ComfyUI API endpoint
COMFY_URL = "http://127.0.0.1:8188"

def wait_for_comfy():
    """Ждем пока ComfyUI API станет доступным"""
    max_attempts = 60
    for i in range(max_attempts):
        try:
            response = requests.get(f"{COMFY_URL}/system_stats", timeout=5)
            if response.status_code == 200:
                logger.info("ComfyUI API готов")
                return True
        except requests.exceptions.RequestException:
            logger.info(f"Ждем ComfyUI API... попытка {i+1}/{max_attempts}")
            time.sleep(5)
    return False

def encode_image_to_base64(image_path):
    """Кодирует изображение в base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def upload_image_to_comfy(image_data, filename="input_image.png"):
    """Загружает изображение в ComfyUI"""
    try:
        # Декодируем base64 если нужно
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Убираем data:image/png;base64, префикс
            image_data = image_data.split(',')[1]
        
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
            
        # Сохраняем в input директорию ComfyUI
        input_dir = "/comfyui/input"
        os.makedirs(input_dir, exist_ok=True)
        
        image_path = os.path.join(input_dir, filename)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        logger.info(f"Изображение сохранено как {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        raise

def create_wan22_workflow(prompt, image_filename, options=None):
    """Создает воркфлоу WAN 2.2 на основе fast-wan22.js"""
    if options is None:
        options = {}
    
    # Параметры по умолчанию
    width = options.get('width', 832)
    height = options.get('height', 832) 
    length = options.get('length', 81)
    cfg = options.get('cfg', 1.0)
    steps = options.get('steps', 6)
    seed = options.get('seed', int(time.time()))
    
    workflow = {
        "6": {
            "inputs": {
                "text": prompt,
                "clip": ["38", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Positive Prompt)"}
        },
        "7": {
            "inputs": {
                "text": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
                "clip": ["38", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative Prompt)"}
        },
        "8": {
            "inputs": {
                "samples": ["58", 0],
                "vae": ["39", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "37": {
            "inputs": {
                "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load Diffusion Model (High)"}
        },
        "38": {
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load CLIP"}
        },
        "39": {
            "inputs": {
                "vae_name": "wan_2.1_vae.safetensors"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "50": {
            "inputs": {
                "width": width,
                "height": height,
                "length": length,
                "batch_size": 1,
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["39", 0],
                "start_image": ["68", 0]
            },
            "class_type": "WanImageToVideo",
            "_meta": {"title": "WanImageToVideo"}
        },
        "52": {
            "inputs": {
                "image": image_filename
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Image"}
        },
        "54": {
            "inputs": {
                "shift": 8.0,
                "model": ["37", 0]
            },
            "class_type": "ModelSamplingSD3",
            "_meta": {"title": "ModelSamplingSD3 (High)"}
        },
        "55": {
            "inputs": {
                "shift": 8.0,
                "model": ["56", 0]
            },
            "class_type": "ModelSamplingSD3",
            "_meta": {"title": "ModelSamplingSD3 (Low)"}
        },
        "56": {
            "inputs": {
                "unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load Diffusion Model (Low)"}
        },
        "57": {
            "inputs": {
                "add_noise": "enable",
                "noise_seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 0,
                "end_at_step": 3,
                "return_with_leftover_noise": "enable",
                "model": ["62", 0],
                "positive": ["50", 0],
                "negative": ["50", 1],
                "latent_image": ["50", 2]
            },
            "class_type": "KSamplerAdvanced",
            "_meta": {"title": "KSampler (Advanced) High"}
        },
        "58": {
            "inputs": {
                "add_noise": "disable",
                "noise_seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 3,
                "end_at_step": 10000,
                "return_with_leftover_noise": "disable",
                "model": ["63", 0],
                "positive": ["50", 0],
                "negative": ["50", 1],
                "latent_image": ["57", 0]
            },
            "class_type": "KSamplerAdvanced",
            "_meta": {"title": "KSampler (Advanced) Low"}
        },
        "62": {
            "inputs": {
                "lora_name": "wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
                "strength_model": 1.0,
                "model": ["54", 0]
            },
            "class_type": "LoraLoaderModelOnly",
            "_meta": {"title": "LoraLoaderModelOnly (High)"}
        },
        "63": {
            "inputs": {
                "lora_name": "wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
                "strength_model": 1.0,
                "model": ["55", 0]
            },
            "class_type": "LoraLoaderModelOnly",
            "_meta": {"title": "LoraLoaderModelOnly (Low)"}
        },
        "64": {
            "inputs": {
                "frame_rate": options.get('frame_rate', 24),
                "loop_count": 0,
                "filename_prefix": "wan2_2",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 19,
                "save_metadata": True,
                "trim_to_audio": False,
                "pingpong": False,
                "save_output": True,
                "images": ["8", 0]
            },
            "class_type": "VHS_VideoCombine",
            "_meta": {"title": "Video Combine 🎥🅥🅗🅢"}
        },
        "68": {
            "inputs": {
                "width": width,
                "height": height,
                "interpolation": "lanczos",
                "method": "fill / crop",
                "condition": "always",
                "multiple_of": 0,
                "image": ["52", 0]
            },
            "class_type": "ImageResize+",
            "_meta": {"title": "🔧 Image Resize"}
        }
    }
    
    return workflow

def queue_workflow(workflow):
    """Отправляет воркфлоу в очередь ComfyUI"""
    try:
        response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
        response.raise_for_status()
        return response.json()["prompt_id"]
    except Exception as e:
        logger.error(f"Ошибка постановки в очередь: {e}")
        raise

def wait_for_completion(prompt_id, timeout=600):
    """Ждет завершения генерации"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Проверяем статус через history
            response = requests.get(f"{COMFY_URL}/history/{prompt_id}")
            
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    # Задача завершена
                    result = history[prompt_id]
                    if result.get("status", {}).get("completed", False):
                        return result
                    elif "error" in result.get("status", {}):
                        raise Exception(f"Ошибка генерации: {result['status']['error']}")
                        
            time.sleep(5)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка проверки статуса: {e}")
            time.sleep(5)
    
    raise TimeoutError(f"Генерация не завершилась за {timeout} секунд")

def get_output_files(result):
    """Получает выходные файлы из результата"""
    output_files = []
    
    try:
        # Ищем видеофайлы в outputs
        for node_id, node_result in result.get("outputs", {}).items():
            if "gifs" in node_result:
                for gif_info in node_result["gifs"]:
                    filename = gif_info["filename"]
                    output_files.append({
                        "type": "video",
                        "filename": filename,
                        "path": f"/comfyui/output/{filename}"
                    })
                    
    except Exception as e:
        logger.error(f"Ошибка получения выходных файлов: {e}")
        
    return output_files

def encode_file_to_base64(file_path):
    """Кодирует файл в base64 для возврата"""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Ошибка кодирования файла {file_path}: {e}")
        return None

def handler(event):
    """Основной обработчик RunPod"""
    try:
        # Проверяем доступность ComfyUI
        if not wait_for_comfy():
            return {"error": "ComfyUI API недоступен"}
        
        # Получаем входные данные
        input_data = event["input"]
        prompt = input_data.get("prompt", "A beautiful scene")
        image_data = input_data.get("image")
        options = input_data.get("options", {})
        
        if not image_data:
            return {"error": "Требуется входное изображение"}
        
        logger.info(f"Начинаем генерацию с промптом: {prompt}")
        
        # Загружаем изображение
        image_filename = upload_image_to_comfy(image_data)
        
        # Создаем воркфлоу
        workflow = create_wan22_workflow(prompt, image_filename, options)
        
        # Отправляем в очередь
        prompt_id = queue_workflow(workflow)
        logger.info(f"Воркфлоу поставлен в очередь: {prompt_id}")
        
        # Ждем завершения
        result = wait_for_completion(prompt_id)
        logger.info("Генерация завершена")
        
        # Получаем выходные файлы
        output_files = get_output_files(result)
        
        if not output_files:
            return {"error": "Выходные файлы не найдены"}
        
        # Кодируем основной видеофайл
        main_video = output_files[0]
        video_base64 = encode_file_to_base64(main_video["path"])
        
        if not video_base64:
            return {"error": "Не удалось закодировать видеофайл"}
        
        return {
            "video": video_base64,
            "filename": main_video["filename"],
            "prompt_id": prompt_id,
            "files_count": len(output_files)
        }
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})