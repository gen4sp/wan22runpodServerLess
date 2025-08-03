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
            else:
                logger.warning(f"ComfyUI API вернул статус {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Ждем ComfyUI API... попытка {i+1}/{max_attempts} - Ошибка соединения: {e}")
        except requests.exceptions.Timeout as e:
            logger.warning(f"Ждем ComfyUI API... попытка {i+1}/{max_attempts} - Таймаут: {e}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ждем ComfyUI API... попытка {i+1}/{max_attempts} - Ошибка запроса: {e}")
        
        # Дополнительная диагностика каждые 5 попыток (чаще!)
        if (i + 1) % 5 == 0:
            logger.info(f"🔍 Диагностика после {i+1} попыток:")
            try:
                # Проверяем процесс ComfyUI
                import subprocess
                result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    logger.info(f"   📊 Найдены процессы ComfyUI: {pids}")
                    
                    # Проверяем использование CPU/памяти процессом
                    for pid in pids:
                        try:
                            cpu_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,pcpu,pmem,etime,cmd'], capture_output=True, text=True)
                            if cpu_result.returncode == 0:
                                logger.info(f"   📈 Процесс {pid}: {cpu_result.stdout.strip().split(chr(10))[-1]}")
                        except:
                            pass
                else:
                    logger.warning("   ❌ Процесс ComfyUI не найден")
                
                # Проверяем порт 8188
                result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
                if ':8188' in result.stdout:
                    logger.info("   🔌 Порт 8188 слушается")
                    # Показываем кто слушает порт
                    for line in result.stdout.split('\n'):
                        if ':8188' in line:
                            logger.info(f"   🔌 Порт 8188: {line.strip()}")
                else:
                    logger.warning("   ❌ Порт 8188 не слушается")
                
                # Проверяем логи ComfyUI
                try:
                    # Ищем логи ComfyUI в разных местах
                    log_paths = ['/tmp/comfyui.log', '/comfyui/comfyui.log', '/var/log/comfyui.log']
                    for log_path in log_paths:
                        if os.path.exists(log_path):
                            with open(log_path, 'r') as f:
                                lines = f.readlines()
                                if lines:
                                    logger.info(f"   📄 Последние строки {log_path}:")
                                    for line in lines[-3:]:
                                        logger.info(f"      {line.strip()}")
                                    break
                    else:
                        logger.info("   📄 Логи ComfyUI не найдены")
                        # Попробуем получить вывод процесса через journalctl
                        try:
                            journal_result = subprocess.run(['journalctl', '--since', '5 minutes ago', '--grep', 'ComfyUI'], capture_output=True, text=True)
                            if journal_result.returncode == 0 and journal_result.stdout.strip():
                                logger.info("   📄 Из журнала системы:")
                                for line in journal_result.stdout.strip().split('\n')[-3:]:
                                    logger.info(f"      {line}")
                        except:
                            pass
                except Exception as log_e:
                    logger.warning(f"   ⚠️ Ошибка чтения логов: {log_e}")
                    
            except Exception as diag_e:
                logger.error(f"   ⚠️ Ошибка диагностики: {diag_e}")
        
        time.sleep(5)
    
    logger.error(f"❌ ComfyUI API не стал доступен за {max_attempts * 5} секунд")
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
    """Ждет завершения генерации с подробным логированием"""
    start_time = time.time()
    last_log_time = start_time
    
    logger.info(f"🕐 Начинаем ожидание завершения генерации {prompt_id} (таймаут: {timeout}s)")
    
    while time.time() - start_time < timeout:
        try:
            elapsed = time.time() - start_time
            
            # Логируем прогресс каждые 30 секунд
            if time.time() - last_log_time >= 30:
                logger.info(f"⏱️ Ожидание генерации: {elapsed:.0f}s/{timeout}s")
                last_log_time = time.time()
            
            # Проверяем статус через history
            response = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    # Задача завершена
                    result = history[prompt_id]
                    status = result.get("status", {})
                    
                    if status.get("completed", False):
                        logger.info(f"✅ Генерация завершена за {elapsed:.1f}s")
                        return result
                    elif "error" in status:
                        error_msg = status.get("error", "Неизвестная ошибка")
                        logger.error(f"❌ Ошибка генерации: {error_msg}")
                        raise Exception(f"Ошибка генерации: {error_msg}")
                    else:
                        # Проверяем очередь
                        queue_response = requests.get(f"{COMFY_URL}/queue", timeout=5)
                        if queue_response.status_code == 200:
                            queue_data = queue_response.json()
                            queue_running = queue_data.get("queue_running", [])
                            queue_pending = queue_data.get("queue_pending", [])
                            
                            # Ищем наш prompt_id в очереди
                            in_running = any(item[1] == prompt_id for item in queue_running)
                            in_pending = any(item[1] == prompt_id for item in queue_pending)
                            
                            if in_running:
                                logger.debug(f"🔄 Задача {prompt_id} выполняется...")
                            elif in_pending:
                                position = next((i for i, item in enumerate(queue_pending) if item[1] == prompt_id), -1)
                                logger.info(f"⏳ Задача {prompt_id} в очереди на позиции {position + 1}")
                            else:
                                logger.warning(f"⚠️ Задача {prompt_id} не найдена в очереди")
                        
            elif response.status_code == 404:
                logger.debug(f"🔍 История для {prompt_id} еще не создана")
            else:
                logger.warning(f"⚠️ Неожиданный статус от /history: {response.status_code}")
                        
            time.sleep(5)
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"⏰ Таймаут при проверке статуса: {e}")
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            logger.warning(f"🌐 Ошибка сети при проверке статуса: {e}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"💥 Неожиданная ошибка при проверке статуса: {e}")
            time.sleep(5)
    
    elapsed = time.time() - start_time
    logger.error(f"⏰ Генерация не завершилась за {timeout}s (прошло {elapsed:.1f}s)")
    raise TimeoutError(f"Генерация не завершилась за {timeout} секунд")



def encode_file_to_base64(file_path):
    """Кодирует файл в base64 для возврата"""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Ошибка кодирования файла {file_path}: {e}")
        return None

def get_system_debug_info():
    """Получает детальную информацию о состоянии системы для отладки"""
    debug_info = {}
    try:
        import subprocess
        import psutil
        
        # Информация о процессах
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            comfy_processes = [line for line in result.stdout.split('\n') if 'main.py' in line or 'comfy' in line.lower()]
            debug_info['comfy_processes'] = comfy_processes
            
            # Дополнительная информация о процессах ComfyUI
            pgrep_result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
            if pgrep_result.returncode == 0:
                pids = pgrep_result.stdout.strip().split('\n')
                debug_info['comfy_pids'] = pids
                
                # Детальная информация о каждом процессе
                process_details = []
                for pid in pids:
                    try:
                        ps_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,ppid,pcpu,pmem,etime,stat,cmd'], capture_output=True, text=True)
                        if ps_result.returncode == 0:
                            process_details.append(ps_result.stdout.strip())
                    except:
                        pass
                debug_info['process_details'] = process_details
            else:
                debug_info['comfy_pids'] = []
                debug_info['process_details'] = []
        except Exception as e:
            debug_info['comfy_processes'] = f"Ошибка получения процессов: {e}"
        
        # Информация о портах
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            port_8188 = [line for line in result.stdout.split('\n') if ':8188' in line]
            debug_info['port_8188'] = port_8188
            
            # Также проверим через ss (более современная утилита)
            try:
                ss_result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
                ss_8188 = [line for line in ss_result.stdout.split('\n') if ':8188' in line]
                debug_info['ss_port_8188'] = ss_8188
            except:
                debug_info['ss_port_8188'] = "ss недоступен"
                
        except Exception as e:
            debug_info['port_8188'] = f"Ошибка получения портов: {e}"
        
        # Информация о памяти
        try:
            memory = psutil.virtual_memory()
            debug_info['memory'] = {
                'total': f"{memory.total / 1024**3:.1f}GB",
                'available': f"{memory.available / 1024**3:.1f}GB",
                'used': f"{memory.used / 1024**3:.1f}GB",
                'percent': f"{memory.percent}%"
            }
        except Exception as e:
            debug_info['memory'] = f"Ошибка получения памяти: {e}"
        
        # Информация о GPU
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True)
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(',')
                debug_info['gpu_memory'] = {
                    'total': f"{int(gpu_data[0])/1024:.1f}GB",
                    'used': f"{int(gpu_data[1])/1024:.1f}GB",
                    'free': f"{int(gpu_data[2])/1024:.1f}GB",
                    'utilization': f"{gpu_data[3]}%",
                    'temperature': f"{gpu_data[4]}°C"
                }
        except Exception as e:
            debug_info['gpu_memory'] = f"Ошибка получения GPU памяти: {e}"
        
        # Проверка логов ComfyUI в разных местах
        try:
            log_paths = ['/tmp/comfyui.log', '/comfyui/comfyui.log', '/var/log/comfyui.log']
            found_logs = {}
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r') as f:
                            lines = f.readlines()
                            found_logs[log_path] = {
                                'exists': True,
                                'lines_count': len(lines),
                                'last_lines': lines[-10:] if len(lines) > 10 else lines
                            }
                    except Exception as e:
                        found_logs[log_path] = {'exists': True, 'error': str(e)}
                else:
                    found_logs[log_path] = {'exists': False}
            
            debug_info['comfyui_logs'] = found_logs
            
            # Попробуем найти вывод процесса ComfyUI через /proc
            try:
                pgrep_result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
                if pgrep_result.returncode == 0:
                    pids = pgrep_result.stdout.strip().split('\n')
                    proc_info = []
                    for pid in pids:
                        try:
                            with open(f'/proc/{pid}/cmdline', 'r') as f:
                                cmdline = f.read().replace('\x00', ' ')
                            with open(f'/proc/{pid}/status', 'r') as f:
                                status = f.read()
                            proc_info.append({
                                'pid': pid,
                                'cmdline': cmdline,
                                'status_excerpt': status[:500] + '...' if len(status) > 500 else status
                            })
                        except:
                            pass
                    debug_info['proc_info'] = proc_info
            except:
                debug_info['proc_info'] = "Ошибка чтения /proc"
                
        except Exception as e:
            debug_info['comfyui_logs'] = f"Ошибка чтения логов: {e}"
        
        # Проверка доступности ComfyUI файлов
        try:
            comfy_paths = ['/comfyui', '/comfyui/main.py', '/comfyui/server.py']
            path_info = {}
            for path in comfy_paths:
                path_info[path] = {
                    'exists': os.path.exists(path),
                    'is_file': os.path.isfile(path) if os.path.exists(path) else False,
                    'is_dir': os.path.isdir(path) if os.path.exists(path) else False
                }
            debug_info['comfy_paths'] = path_info
        except Exception as e:
            debug_info['comfy_paths'] = f"Ошибка проверки путей: {e}"
            
    except Exception as e:
        debug_info['error'] = str(e)
    
    return debug_info

def check_comfy_health():
    """Быстрая проверка здоровья ComfyUI API"""
    try:
        # Проверяем базовые эндпоинты
        endpoints_to_check = [
            ("/system_stats", "Системная статистика"),
            ("/queue", "Очередь заданий"),
            ("/history", "История заданий")
        ]
        
        health_status = {"healthy": True, "checks": {}}
        
        for endpoint, description in endpoints_to_check:
            try:
                response = requests.get(f"{COMFY_URL}{endpoint}", timeout=3)
                health_status["checks"][endpoint] = {
                    "status": response.status_code,
                    "description": description,
                    "healthy": response.status_code == 200
                }
                if response.status_code != 200:
                    health_status["healthy"] = False
            except Exception as e:
                health_status["checks"][endpoint] = {
                    "status": "error",
                    "description": description,
                    "error": str(e),
                    "healthy": False
                }
                health_status["healthy"] = False
        
        return health_status
        
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def restart_comfyui():
    """Принудительно перезапускает ComfyUI"""
    try:
        import subprocess
        
        logger.info("🔄 Принудительный перезапуск ComfyUI...")
        
        # Убиваем все процессы ComfyUI
        try:
            result = subprocess.run(['pkill', '-f', 'main.py'], capture_output=True, text=True)
            logger.info(f"   🔪 pkill main.py: код возврата {result.returncode}")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"   ⚠️ Ошибка pkill: {e}")
        
        # Убиваем процессы на порту 8188
        try:
            result = subprocess.run(['fuser', '-k', '8188/tcp'], capture_output=True, text=True)
            logger.info(f"   🔪 fuser -k 8188/tcp: код возврата {result.returncode}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"   ⚠️ Ошибка fuser: {e}")
        
        # Запускаем ComfyUI заново
        try:
            logger.info("   🚀 Запуск нового процесса ComfyUI...")
            process = subprocess.Popen([
                'python3', '/comfyui/main.py', 
                '--listen', '0.0.0.0', 
                '--port', '8188',
                '--disable-auto-launch'
            ], 
            cwd='/comfyui',
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Создаем новую группу процессов
            )
            
            logger.info(f"   ✅ ComfyUI перезапущен с PID: {process.pid}")
            time.sleep(5)  # Даем время на запуск
            
            return {"success": True, "new_pid": process.pid}
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка запуска ComfyUI: {e}")
            return {"success": False, "error": str(e)}
            
    except Exception as e:
        logger.error(f"❌ Ошибка перезапуска ComfyUI: {e}")
        return {"success": False, "error": str(e)}

def handler(event):
    """Основной обработчик RunPod с поддержкой произвольных JSON воркфлоу"""
    try:
        input_data = event.get("input", {})
        action = input_data.get("action")
        
        # Специальные команды для отладки
        if action == "debug_system":
            return {"debug_info": get_system_debug_info()}
        elif action == "health_check":
            return {"health": check_comfy_health()}
        elif action == "ping":
            return {"status": "pong", "timestamp": time.time()}
        elif action == "restart_comfyui":
            return {"restart_result": restart_comfyui()}
        
        # Проверяем доступность ComfyUI
        if not wait_for_comfy():
            # Добавляем отладочную информацию в случае неудачи
            debug_info = get_system_debug_info()
            health_info = check_comfy_health()
            return {
                "error": "ComfyUI API недоступен", 
                "debug_info": debug_info,
                "health_info": health_info
            }
        
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