#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отладочных функций
"""

import json
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rp_handler import get_system_debug_info, check_comfy_health, restart_comfyui

def test_debug_functions():
    """Тестирует отладочные функции"""
    
    print("🔍 Тестирование отладочных функций...")
    
    # Тест системной диагностики
    print("\n📊 Системная диагностика:")
    try:
        debug_info = get_system_debug_info()
        print(json.dumps(debug_info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка системной диагностики: {e}")
    
    # Тест проверки здоровья
    print("\n🏥 Проверка здоровья ComfyUI:")
    try:
        health_info = check_comfy_health()
        print(json.dumps(health_info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка проверки здоровья: {e}")
    
    # Предлагаем перезапуск, если API недоступен
    try:
        health_info = check_comfy_health()
        if not health_info.get("healthy", False):
            print("\n🔄 ComfyUI API недоступен. Хотите перезапустить? (y/N)")
            response = input().strip().lower()
            if response == 'y':
                print("🔄 Перезапуск ComfyUI...")
                restart_result = restart_comfyui()
                print(json.dumps(restart_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка при попытке перезапуска: {e}")

if __name__ == "__main__":
    test_debug_functions()