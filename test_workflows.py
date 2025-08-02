#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для новой системы JSON воркфлоу
"""

import json
import sys
import os

# Добавляем текущую директорию в путь для импорта workflows
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows import analyze_workflow, get_workflow_info, process_workflow, WorkflowType


def test_workflow_analysis():
    """Тестирует анализ типов воркфлоу"""
    print("=== Тест анализа воркфлоу ===")
    
    # Тестовые воркфлоу разных типов
    test_workflows = {
        "T2V (WAN 2.2)": {
            "6": {"class_type": "CLIPTextEncode"},
            "50": {"class_type": "WanImageToVideo"},
            "64": {"class_type": "VHS_VideoCombine"}
        },
        "T2I (Stable Diffusion)": {
            "1": {"class_type": "CLIPTextEncode"}, 
            "3": {"class_type": "KSampler"},
            "5": {"class_type": "EmptyLatentImage"},
            "7": {"class_type": "SaveImage"}
        },
        "Img2Img": {
            "1": {"class_type": "CLIPTextEncode"},
            "3": {"class_type": "KSampler"}, 
            "5": {"class_type": "LoadImage"},
            "9": {"class_type": "SaveImage"}
        },
        "Video Upscale": {
            "1": {"class_type": "VHS_LoadVideo"},
            "2": {"class_type": "ImageUpscaleWithModel"},
            "3": {"class_type": "VHS_VideoCombine"}
        }
    }
    
    for name, workflow in test_workflows.items():
        workflow_type = analyze_workflow(workflow)
        print(f"  {name}: {workflow_type.value}")
        
        # Получаем подробную информацию
        info = get_workflow_info(workflow)
        print(f"    Узлов: {info['node_count']}, Выход: {info['expected_output']}")
        print(f"    Промпт: {info['supports_prompt']}, Изображение: {info['requires_image']}, Видео: {info['requires_video']}")
    
    print()


def test_workflow_processing():
    """Тестирует обработку воркфлоу"""
    print("=== Тест обработки воркфлоу ===")
    
    # Простой T2I воркфлоу
    test_workflow = {
        "1": {
            "inputs": {"text": "old prompt", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {"seed": 0, "steps": 10, "cfg": 5.0},
            "class_type": "KSampler"
        },
        "5": {
            "inputs": {"width": 512, "height": 512},
            "class_type": "EmptyLatentImage"
        },
        "7": {
            "inputs": {"filename_prefix": "test"},
            "class_type": "SaveImage"
        }
    }
    
    try:
        prepared_workflow, workflow_type, metadata = process_workflow(
            workflow=test_workflow,
            prompt="New test prompt",
            options={"seed": 12345, "steps": 20}
        )
        
        print(f"✓ Воркфлоу обработан успешно")
        print(f"  Тип: {workflow_type.value}")
        print(f"  Метаданные: {metadata}")
        
        # Проверяем, что промпт обновился
        if prepared_workflow["1"]["inputs"]["text"] == "New test prompt":
            print("  ✓ Промпт обновлен корректно")
        else:
            print("  ✗ Ошибка обновления промпта")
            
        # Проверяем, что сид обновился
        if prepared_workflow["3"]["inputs"]["seed"] == 12345:
            print("  ✓ Сид обновлен корректно")
        else:
            print("  ✗ Ошибка обновления сида")
            
    except Exception as e:
        print(f"✗ Ошибка обработки воркфлоу: {e}")
    
    print()


def test_validation():
    """Тестирует валидацию входных данных"""
    print("=== Тест валидации ===")
    
    # T2V воркфлоу - требует промпт
    t2v_workflow = {
        "6": {"class_type": "CLIPTextEncode"},
        "50": {"class_type": "WanImageToVideo"},
        "64": {"class_type": "VHS_VideoCombine"}
    }
    
    # Тест без промпта (должен выдать ошибку)
    try:
        prepared_workflow, workflow_type, metadata = process_workflow(
            workflow=t2v_workflow
        )
        print("  ✗ Должна была быть ошибка валидации для T2V без промпта")
    except ValueError as e:
        print(f"  ✓ Корректная ошибка валидации: {e}")
    
    # Img2Img воркфлоу - требует изображение
    img2img_workflow = {
        "5": {"class_type": "LoadImage"},
        "9": {"class_type": "SaveImage"}
    }
    
    try:
        prepared_workflow, workflow_type, metadata = process_workflow(
            workflow=img2img_workflow,
            prompt="Test prompt"
        )
        print("  ✗ Должна была быть ошибка валидации для Img2Img без изображения")
    except ValueError as e:
        print(f"  ✓ Корректная ошибка валидации: {e}")
    
    print()


def load_test_cases():
    """Загружает тестовые случаи из JSON файлов"""
    test_files = ["test_json_workflows.json", "test_workflows.json"]
    all_tests = {}
    
    for filename in test_files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                tests = json.load(f)
                all_tests.update(tests)
                print(f"  Загружено {len(tests)} тестов из {filename}")
        except FileNotFoundError:
            print(f"  Файл {filename} не найден")
        except Exception as e:
            print(f"  Ошибка загрузки {filename}: {e}")
    
    return all_tests


def test_json_cases():
    """Тестирует случаи из JSON файлов"""
    print("=== Тест JSON случаев ===")
    
    test_cases = load_test_cases()
    
    for test_name, test_data in test_cases.items():
        print(f"\nТест: {test_name}")
        
        input_data = test_data.get("input", {})
        
        # Проверяем, есть ли воркфлоу
        workflow = input_data.get("workflow")
        if not workflow:
            print(f"  ⚠ Воркфлоу не найден в тесте")
            continue
        
        # Анализируем воркфлоу
        try:
            workflow_type = analyze_workflow(workflow)
            info = get_workflow_info(workflow)
            
            print(f"  Тип: {workflow_type.value}")
            print(f"  Узлов: {info['node_count']}")
            print(f"  Ожидаемый выход: {info['expected_output']}")
            
            # Проверяем соответствие входных данных требованиям
            has_prompt = bool(input_data.get("prompt"))
            has_image = bool(input_data.get("image"))
            has_video = bool(input_data.get("video"))
            
            validation_ok = True
            
            if info['supports_prompt'] and workflow_type in [WorkflowType.T2V, WorkflowType.T2I] and not has_prompt:
                print(f"  ⚠ Воркфлоу поддерживает промпт, но промпт не предоставлен")
                validation_ok = False
            
            if info['requires_image'] and not has_image:
                print(f"  ⚠ Воркфлоу требует изображение, но оно не предоставлено")
                validation_ok = False
            
            if info['requires_video'] and not has_video:
                print(f"  ⚠ Воркфлоу требует видео, но оно не предоставлено")
                validation_ok = False
            
            if validation_ok:
                print(f"  ✓ Входные данные соответствуют требованиям")
            
        except Exception as e:
            print(f"  ✗ Ошибка анализа: {e}")
    
    print()


def main():
    """Основная функция тестирования"""
    print("Тестирование новой системы JSON воркфлоу\n")
    
    try:
        test_workflow_analysis()
        test_workflow_processing()
        test_validation()
        test_json_cases()
        
        print("=== Все тесты завершены ===")
        
    except Exception as e:
        print(f"Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()