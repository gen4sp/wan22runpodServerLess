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
from workflows import process_workflow, analyze_workflow, get_workflow_info, WorkflowType

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

# еу
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

def create_empty_image(width=832, height=832, filename="empty_image.png"):
    """Создает черное изображение для T2V режима"""
    try:
        # Создаем черное изображение через PIL
        image = Image.new('RGB', (width, height), color='black')
        
        # Сохраняем в input директорию ComfyUI
        input_dir = "/comfyui/input"
        os.makedirs(input_dir, exist_ok=True)
        
        image_path = os.path.join(input_dir, filename)
        image.save(image_path)
        
        logger.info(f"Создано пустое изображение {width}x{height} как {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Ошибка создания пустого изображения: {e}")
        raise

def get_output_files_by_type(result, workflow_type):
    """Получает выходные файлы в зависимости от типа воркфлоု"""
    output_files = []
    
    try:
        # Для видео воркфлоу ищем видеофайлы
        if workflow_type in [WorkflowType.T2V, WorkflowType.VIDEO_UPSCALE]:
            for node_id, node_result in result.get("outputs", {}).items():
                # Ищем видеофайлы
                if "gifs" in node_result:
                    for gif_info in node_result["gifs"]:
                        filename = gif_info["filename"]
                        output_files.append({
                            "type": "video",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
                # Альтернативный формат для видео
                elif "videos" in node_result:
                    for video_info in node_result["videos"]:
                        filename = video_info["filename"]
                        output_files.append({
                            "type": "video",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
        
        # Для изображений воркфлоу ищем изображения
        elif workflow_type in [WorkflowType.T2I, WorkflowType.IMG2IMG]:
            for node_id, node_result in result.get("outputs", {}).items():
                if "images" in node_result:
                    for img_info in node_result["images"]:
                        filename = img_info["filename"]
                        output_files.append({
                            "type": "image",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
        
        # Для неизвестных типов пробуем найти любые выходные файлы
        else:
            for node_id, node_result in result.get("outputs", {}).items():
                # Сначала видео
                if "gifs" in node_result:
                    for gif_info in node_result["gifs"]:
                        filename = gif_info["filename"]
                        output_files.append({
                            "type": "video",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
                elif "videos" in node_result:
                    for video_info in node_result["videos"]:
                        filename = video_info["filename"]
                        output_files.append({
                            "type": "video",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
                # Затем изображения
                elif "images" in node_result:
                    for img_info in node_result["images"]:
                        filename = img_info["filename"]
                        output_files.append({
                            "type": "image",
                            "filename": filename,
                            "path": f"/comfyui/output/{filename}"
                        })
                        
    except Exception as e:
        logger.error(f"Ошибка получения выходных файлов: {e}")
        
    return output_files

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



def encode_file_to_base64(file_path):
    """Кодирует файл в base64 для возврата"""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Ошибка кодирования файла {file_path}: {e}")
        return None

def handler(event):
    """Основной обработчик RunPod с поддержкой произвольных JSON воркфлоу"""
    try:
        # Проверяем доступность ComfyUI
        if not wait_for_comfy():
            return {"error": "ComfyUI API недоступен"}
        
        # Получаем входные данные
        input_data = event["input"]
        
        # Специальная команда для анализа воркфлоу
        if input_data.get("action") == "analyze_workflow":
            workflow = input_data.get("workflow")
            if not workflow:
                return {"error": "Для анализа требуется воркфлоу в параметре 'workflow'"}
            return {"workflow_info": get_workflow_info(workflow)}
        
        # Получаем обязательный параметр workflow (полный JSON)
        workflow = input_data.get("workflow")
        if not workflow:
            return {"error": "Параметр 'workflow' обязателен и должен содержать полный JSON воркфлоу ComfyUI"}
        
        # Получаем остальные параметры
        prompt = input_data.get("prompt")
        image_data = input_data.get("image")
        video_data = input_data.get("video") 
        options = input_data.get("options", {})
        
        logger.info(f"Начинаем обработку воркфлоу с {len(workflow)} узлами")
        if prompt:
            logger.info(f"Промпт: {prompt}")
        
        # Обрабатываем воркфлоу
        try:
            prepared_workflow, workflow_type, metadata = process_workflow(
                workflow=workflow,
                prompt=prompt,
                image_data=image_data,
                video_data=video_data,
                options=options
            )
        except ValueError as e:
            return {"error": f"Ошибка валидации воркфлоу: {str(e)}"}
        
        logger.info(f"Воркфлоу обработан: тип={workflow_type.value}, узлов={metadata['node_count']}")
        
        # Отправляем в очередь ComfyUI
        prompt_id = queue_workflow(prepared_workflow)
        logger.info(f"Воркфлоу поставлен в очередь: {prompt_id}")
        
        # Ждем завершения
        result = wait_for_completion(prompt_id)
        logger.info("Генерация завершена")
        
        # Получаем выходные файлы
        output_files = get_output_files_by_type(result, workflow_type)
        
        if not output_files:
            return {"error": "Выходные файлы не найдены"}
        
        # Кодируем основной файл
        main_file = output_files[0]
        file_base64 = encode_file_to_base64(main_file["path"])
        
        if not file_base64:
            return {"error": f"Не удалось закодировать {main_file['type']}"}
        
        # Формируем ответ
        response = {
            main_file["type"]: file_base64,
            "filename": main_file["filename"],
            "prompt_id": prompt_id,
            "files_count": len(output_files),
            "workflow_type": workflow_type.value,
            "metadata": metadata
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})