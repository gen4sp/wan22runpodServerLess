#!/usr/bin/env python3
"""
Скрипт для полного удаления torchaudio и создания mock-версии
"""
import os
import sys
import shutil
import subprocess

def remove_torchaudio():
    """Полностью удаляет torchaudio из системы"""
    
    # 1. Удаляем через pip
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torchaudio'], 
                      capture_output=True, check=False)
        print("✅ torchaudio удален через pip")
    except Exception as e:
        print(f"⚠️ Ошибка при удалении через pip: {e}")
    
    # 2. Находим все директории site-packages
    site_packages_dirs = []
    for path in sys.path:
        if ('site-packages' in path or 'dist-packages' in path) and os.path.exists(path):
            site_packages_dirs.append(path)
    
    # 3. Удаляем все файлы и директории torchaudio
    removed_count = 0
    for site_dir in site_packages_dirs:
        for item in os.listdir(site_dir):
            if 'torchaudio' in item.lower():
                item_path = os.path.join(site_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    print(f"✅ Удален: {item_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️ Не удалось удалить {item_path}: {e}")
    
    print(f"✅ Удалено {removed_count} файлов/директорий torchaudio")
    
    # 4. Создаем mock torchaudio
    create_mock_torchaudio()

def create_mock_torchaudio():
    """Создает mock-версию torchaudio"""
    
    torchaudio_mock = '''"""Mock torchaudio module для ComfyUI"""

__version__ = "2.1.0+mock"
__file__ = "/mock/torchaudio/__init__.py"

def load(*args, **kwargs):
    raise RuntimeError("torchaudio отключен в этой сборке")

def save(*args, **kwargs):
    raise RuntimeError("torchaudio отключен в этой сборке")

class lib:
    """Mock lib module"""
    pass

class transforms:
    @staticmethod
    def Resample(*args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")

class functional:
    @staticmethod
    def resample(*args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")

# Добавляем все необходимые атрибуты
backend = None
'''
    
    # Находим первую доступную директорию site-packages
    site_packages = None
    for path in sys.path:
        if ('site-packages' in path or 'dist-packages' in path) and os.path.exists(path):
            site_packages = path
            break
    
    if site_packages:
        torchaudio_dir = os.path.join(site_packages, 'torchaudio')
        os.makedirs(torchaudio_dir, exist_ok=True)
        
        # Создаем __init__.py
        with open(os.path.join(torchaudio_dir, '__init__.py'), 'w') as f:
            f.write(torchaudio_mock)
        
        print(f"✅ Создан mock torchaudio в {torchaudio_dir}")
        
        # Проверяем что mock работает
        try:
            import torchaudio
            print(f"✅ Mock torchaudio успешно импортирован: {torchaudio.__version__}")
        except Exception as e:
            print(f"❌ Ошибка при импорте mock torchaudio: {e}")
    else:
        print("❌ Не удалось найти site-packages для создания mock")

if __name__ == "__main__":
    print("🚀 Начинаем удаление torchaudio...")
    remove_torchaudio()
    print("✅ Готово!")