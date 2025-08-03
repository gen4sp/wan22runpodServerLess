#!/usr/bin/env python3
"""
Патч для создания mock-версии torchaudio
"""
import os
import sys

# Создаем mock torchaudio модуль
torchaudio_mock = '''
"""Mock torchaudio module для ComfyUI"""

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

# Находим директорию site-packages
site_packages = None
for path in sys.path:
    if 'site-packages' in path or 'dist-packages' in path:
        site_packages = path
        break

if site_packages:
    torchaudio_dir = os.path.join(site_packages, 'torchaudio')
    os.makedirs(torchaudio_dir, exist_ok=True)
    
    # Создаем __init__.py
    with open(os.path.join(torchaudio_dir, '__init__.py'), 'w') as f:
        f.write(torchaudio_mock)
    
    print(f"✅ Создан mock torchaudio в {torchaudio_dir}")
else:
    print("❌ Не удалось найти site-packages")