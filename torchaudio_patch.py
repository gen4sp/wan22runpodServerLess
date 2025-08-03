#!/usr/bin/env python3
"""
АГРЕССИВНЫЙ патч для обхода циклического импорта в torchaudio
Полностью заменяет torchaudio на mock-версию ДО любых импортов
"""
import sys
import types
import os

# Устанавливаем переменные окружения АГРЕССИВНО
os.environ['TORCH_AUDIO_BACKEND'] = 'soundfile'
os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'
os.environ['DISABLE_TORCHAUDIO_CUDA_CHECK'] = '1'
os.environ['CM_DISABLE_TORCHAUDIO'] = '1'

def create_mock_torchaudio():
    """Создает mock модули для torchaudio"""
    
    # Создаем mock модуль для torchaudio.lib._torchaudio
    _torchaudio_module = types.ModuleType('_torchaudio')
    _torchaudio_module.cuda_version = lambda: '12.8'  # Возвращаем версию CUDA
    
    # Создаем mock модуль для torchaudio._extension.utils
    utils_module = types.ModuleType('torchaudio._extension.utils')
    utils_module._check_cuda_version = lambda: None  # Пустая функция
    
    # Создаем mock модуль для torchaudio._extension
    extension_module = types.ModuleType('torchaudio._extension')
    extension_module.utils = utils_module
    extension_module._check_cuda_version = lambda: None
    
    # Создаем mock модуль для torchaudio.lib
    lib_module = types.ModuleType('torchaudio.lib')
    lib_module._torchaudio = _torchaudio_module

    # Создаем основной mock для torchaudio  
    torchaudio_module = types.ModuleType('torchaudio')
    torchaudio_module.lib = lib_module
    torchaudio_module._extension = extension_module
    torchaudio_module.__version__ = '2.5.0'  # Указываем версию
    torchaudio_module.__file__ = '/usr/local/lib/python3.11/dist-packages/torchaudio/__init__.py'
    
    # Добавляем mock модули в sys.modules
    sys.modules['torchaudio._extension.utils'] = utils_module
    sys.modules['torchaudio._extension'] = extension_module
    sys.modules['torchaudio.lib._torchaudio'] = _torchaudio_module
    sys.modules['torchaudio.lib'] = lib_module
    sys.modules['torchaudio'] = torchaudio_module
    
    return torchaudio_module

# АГРЕССИВНАЯ ОЧИСТКА - удаляем любые следы torchaudio из sys.modules
modules_to_remove = [key for key in sys.modules.keys() if key == 'torchaudio' or key.startswith('torchaudio.')]
for module_name in modules_to_remove:
    del sys.modules[module_name]
    print(f'🧹 Удален модуль: {module_name}')

# СОЗДАЕМ mock модули ПРИНУДИТЕЛЬНО
try:
    create_mock_torchaudio()
    print('✅ torchaudio mock создан агрессивно')
except Exception as e:
    print(f'❌ Ошибка создания torchaudio mock: {e}')

# БЛОКИРОВЩИК импорта - перехватывает ВСЕ попытки импорта torchaudio
class AggressiveTorchaudioBlocker:
    def find_spec(self, fullname, path, target=None):
        if fullname == 'torchaudio' or fullname.startswith('torchaudio.'):
            print(f'🚫 Блокирован импорт: {fullname}')
            # Если модуля нет в sys.modules, создаем mock
            if fullname not in sys.modules:
                if fullname == 'torchaudio':
                    create_mock_torchaudio()
                # Для подмодулей возвращаем что уже есть
            return None
        return None

# Устанавливаем блокировщик В НАЧАЛО meta_path чтобы он перехватывал все
sys.meta_path.insert(0, AggressiveTorchaudioBlocker())
print('🚫 Агрессивный блокировщик torchaudio установлен')

print('✅ АГРЕССИВНЫЙ torchaudio патч применен')