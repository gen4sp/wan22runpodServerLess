#!/usr/bin/env python3
"""
Пример использования WAN 2.2 ServerLess Worker
"""

import requests
import base64
import json
import time
from pathlib import Path

# Конфигурация
RUNPOD_API_KEY = "your_api_key_here"
ENDPOINT_ID = "your_endpoint_id_here"
RUNPOD_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

def encode_image(image_path):
    """Кодирует изображение в base64"""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Определяем MIME тип
    suffix = Path(image_path).suffix.lower()
    mime_type = {
        '.jpg': 'jpeg',
        '.jpeg': 'jpeg', 
        '.png': 'png',
        '.webp': 'webp'
    }.get(suffix, 'jpeg')
    
    return f"data:image/{mime_type};base64,{image_data}"

def save_video(video_base64, output_path):
    """Сохраняет видео из base64"""
    video_data = base64.b64decode(video_base64)
    with open(output_path, "wb") as f:
        f.write(video_data)
    print(f"✅ Видео сохранено: {output_path}")

def generate_video(image_path, prompt, options=None):
    """Генерирует видео через RunPod API"""
    
    # Кодируем изображение
    print(f"📸 Кодируем изображение: {image_path}")
    image_b64 = encode_image(image_path)
    
    # Подготавливаем запрос
    payload = {
        "input": {
            "prompt": prompt,
            "image": image_b64,
            "options": options or {}
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Отправляем запрос: {prompt[:50]}...")
    
    # Используем runsync для синхронного выполнения
    response = requests.post(
        f"{RUNPOD_URL}/runsync", 
        json=payload, 
        headers=headers,
        timeout=300  # 5 минут
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка API: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    
    if "error" in result:
        print(f"❌ Ошибка обработки: {result['error']}")
        return None
    
    if "output" not in result:
        print(f"❌ Нет выходных данных: {result}")
        return None
        
    return result["output"]

def generate_text_to_video(prompt, options=None):
    """Генерирует видео только из текстового промпта (T2V режим)"""
    
    # Подготавливаем запрос без изображения
    payload = {
        "input": {
            "prompt": prompt,
            "options": options or {}
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Отправляем T2V запрос...")
    print(f"📝 Промпт: {prompt}")
    if options:
        print(f"⚙️  Параметры: {options}")
    
    try:
        # Отправляем запрос
        response = requests.post(
            f"{RUNPOD_URL}/runsync", 
            json=payload, 
            headers=headers,
            timeout=600  # 10 минут
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            print(f"❌ Ошибка обработки: {result['error']}")
            return None
        
        if "output" not in result:
            print(f"❌ Нет выходных данных: {result}")
            return None
            
        return result["output"]
        
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None

def main():
    """Основная функция с примерами использования"""
    
    # Пример 1: Базовая генерация
    print("🎬 Пример 1: Базовая генерация")
    
    result = generate_video(
        image_path="input_image.jpg",  # Замените на путь к вашему изображению
        prompt="A majestic eagle soaring through clouds, cinematic, high quality",
        options={
            "width": 832,
            "height": 832,
            "length": 81,
            "steps": 6,
            "cfg": 1.0,
            "frame_rate": 24
        }
    )
    
    if result:
        save_video(result["video"], "output_eagle.mp4")
        print(f"📁 Файл: {result['filename']}")
        print(f"🆔 Prompt ID: {result['prompt_id']}")
    
    # Пример 2: Короткое видео в высоком разрешении
    print("\n🎬 Пример 2: HD качество, короткое видео")
    
    result = generate_video(
        image_path="input_image.jpg",
        prompt="A cat walking gracefully, professional lighting, 4k quality",
        options={
            "width": 1280,
            "height": 720,
            "length": 49,  # Меньше кадров для экономии VRAM
            "steps": 6,
            "cfg": 1.2,
            "frame_rate": 24,
            "seed": 42
        }
    )
    
    if result:
        save_video(result["video"], "output_cat_hd.mp4")
    
    # Пример 3: Длинное видео в стандартном разрешении
    print("\n🎬 Пример 3: Длинное видео")
    
    result = generate_video(
        image_path="input_image.jpg", 
        prompt="Ocean waves gently lapping on the shore, peaceful, relaxing",
        options={
            "width": 640,
            "height": 640,
            "length": 121,  # ~5 секунд
            "steps": 6,
            "cfg": 1.0,
            "frame_rate": 24
        }
    )
    
    if result:
        save_video(result["video"], "output_ocean_long.mp4")
    
    # Пример 4: Text-to-Video (без изображения)
    print("\n🎬 Пример 4: T2V - генерация только по промпту")
    
    result = generate_text_to_video(
        prompt="A majestic dragon flying through stormy clouds, lightning, epic fantasy, cinematic",
        options={
            "width": 832,
            "height": 832,
            "length": 81,
            "steps": 6,
            "cfg": 1.0,
            "frame_rate": 24,
            "seed": 123
        }
    )
    
    if result:
        save_video(result["video"], "output_dragon_t2v.mp4")
        print(f"📁 Файл: {result['filename']}")
        print(f"🆔 Prompt ID: {result['prompt_id']}")

def async_example():
    """Пример асинхронного использования с run"""
    
    payload = {
        "input": {
            "prompt": "A butterfly landing on a flower",
            "image": encode_image("input_image.jpg"),
            "options": {"width": 832, "height": 832, "length": 81}
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Запускаем задачу
    response = requests.post(f"{RUNPOD_URL}/run", json=payload, headers=headers)
    job_id = response.json()["id"]
    
    print(f"🆔 Задача запущена: {job_id}")
    
    # Проверяем статус
    while True:
        status_response = requests.get(f"{RUNPOD_URL}/status/{job_id}", headers=headers)
        status = status_response.json()
        
        if status["status"] == "COMPLETED":
            result = status["output"]
            save_video(result["video"], "output_async.mp4")
            break
        elif status["status"] == "FAILED":
            print(f"❌ Задача провалилась: {status.get('error', 'Unknown error')}")
            break
        else:
            print(f"⏳ Статус: {status['status']}")
            time.sleep(5)

if __name__ == "__main__":
    # Проверяем наличие входного изображения
    if not Path("input_image.jpg").exists():
        print("❌ Создайте файл input_image.jpg перед запуском примера")
        print("📋 Или измените путь к изображению в коде")
        exit(1)
    
    # Проверяем конфигурацию
    if RUNPOD_API_KEY == "your_api_key_here":
        print("❌ Укажите ваш RunPod API ключ в переменной RUNPOD_API_KEY")
        exit(1)
        
    if ENDPOINT_ID == "your_endpoint_id_here":
        print("❌ Укажите ID вашего Endpoint в переменной ENDPOINT_ID")
        exit(1)
    
    main()
    
    print("\n🔄 Хотите попробовать асинхронный режим? (y/N): ", end="")
    if input().lower() == 'y':
        async_example()