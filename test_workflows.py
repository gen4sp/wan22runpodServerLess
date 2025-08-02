#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки системы воркфлоу
"""

import json
import sys
import os

# Добавляем текущую директорию в путь для импорта workflows
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows import get_workflow, list_available_workflows


def test_workflow_loading():
    """Тестирует загрузку воркфлоу"""
    print("=== Тест загрузки воркфлоу ===")
    
    # Получаем список доступных воркфлоу
    workflows = list_available_workflows()
    print(f"Доступно воркфлоу: {len(workflows)}")
    
    for name, info in workflows.items():
        print(f"  - {name}: {info.get('name', 'Unknown')} v{info.get('version', '?')}")
        print(f"    T2V: {info.get('supports_t2v', False)}, I2V: {info.get('supports_i2v', False)}")
    
    print()


def test_workflow_creation():
    """Тестирует создание воркфлоу"""
    print("=== Тест создания воркфлоу ===")
    
    # Тестируем WAN 2.2
    wan22 = get_workflow("wan22")
    if wan22:
        print("✓ WAN 2.2 загружен успешно")
        workflow = wan22.create_workflow("Test prompt", "test.png", {"width": 512, "height": 512})
        print(f"  Создан воркфлоу с {len(workflow)} узлами")
    else:
        print("✗ Ошибка загрузки WAN 2.2")
    
    # Тестируем простой воркфлоу
    simple = get_workflow("test")
    if simple:
        print("✓ Simple Test загружен успешно")
        workflow = simple.create_workflow("Test prompt", "test.png")
        print(f"  Создан воркфлоу с {len(workflow)} узлами")
    else:
        print("✗ Ошибка загрузки Simple Test")
    
    print()


def test_workflow_validation():
    """Тестирует валидацию опций"""
    print("=== Тест валидации опций ===")
    
    wan22 = get_workflow("wan22")
    if wan22:
        # Тест с частичными опциями
        options = {"width": 1024}
        validated = wan22.validate_options(options)
        print(f"Опции до валидации: {options}")
        print(f"Опции после валидации: {validated}")
        
        # Проверяем, что значения по умолчанию добавлены
        default_options = wan22.get_default_options()
        for key, default_value in default_options.items():
            if key not in options:
                assert validated[key] == default_value, f"Значение {key} не установлено по умолчанию"
        
        print("✓ Валидация опций работает корректно")
    
    print()


def load_test_cases():
    """Загружает тестовые случаи из JSON файла"""
    try:
        with open("test_workflows.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл test_workflows.json не найден")
        return {}


def test_workflow_compatibility():
    """Тестирует совместимость воркфлоу с тестовыми случаями"""
    print("=== Тест совместимости воркфлоу ===")
    
    test_cases = load_test_cases()
    
    for test_name, test_data in test_cases.items():
        if test_name == "list_workflows":
            continue
            
        input_data = test_data.get("input", {})
        workflow_name = input_data.get("workflow", "default")
        has_image = "image" in input_data
        
        print(f"Тест: {test_name} (воркфлоу: {workflow_name})")
        
        workflow = get_workflow(workflow_name)
        if not workflow:
            print(f"  ✗ Воркфлоу {workflow_name} не найден")
            continue
            
        # Проверяем совместимость режимов
        if has_image and not workflow.supports_i2v():
            print(f"  ⚠ Воркфлоу не поддерживает I2V режим")
        elif not has_image and not workflow.supports_t2v():
            print(f"  ⚠ Воркфлоу не поддерживает T2V режим")
        else:
            print(f"  ✓ Режим совместим")
        
        # Проверяем опции
        options = input_data.get("options", {})
        default_options = workflow.get_default_options()
        
        unknown_options = set(options.keys()) - set(default_options.keys())
        if unknown_options:
            print(f"  ⚠ Неизвестные опции: {unknown_options}")
        else:
            print(f"  ✓ Все опции поддерживаются")
    
    print()


def main():
    """Основная функция тестирования"""
    print("Тестирование системы воркфлоу RunPod Handler\n")
    
    try:
        test_workflow_loading()
        test_workflow_creation()
        test_workflow_validation()
        test_workflow_compatibility()
        
        print("=== Все тесты завершены ===")
        
    except Exception as e:
        print(f"Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()