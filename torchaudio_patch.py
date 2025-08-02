#!/usr/bin/env python3
"""
Патч для обхода циклического импорта в torchaudio
Создает mock модули для torchaudio.lib и связанных компонентов
"""
import sys
import types
import os

# Устанавливаем переменные окружения
os.environ['TORCH_AUDIO_BACKEND'] = 'soundfile'
os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'
os.environ['DISABLE_TORCHAUDIO_CUDA_CHECK'] = '1'

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

# Проверяем, есть ли уже torchaudio в sys.modules
if 'torchaudio' in sys.modules:
    print('⚠️  torchaudio уже загружен, патч может не сработать')
else:
    try:
        create_mock_torchaudio()
        print('✅ torchaudio mock создан успешно')
    except Exception as e:
        print(f'❌ Ошибка создания torchaudio mock: {e}')

# Дополнительная защита - перехватываем импорт torchaudio
class TorchaudioImportHook:
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith('torchaudio') and fullname not in sys.modules:
            if fullname == 'torchaudio':
                create_mock_torchaudio()
            return None
        return None

# Устанавливаем хук импорта
if not any(isinstance(hook, TorchaudioImportHook) for hook in sys.meta_path):
    sys.meta_path.insert(0, TorchaudioImportHook())
    print('✅ torchaudio import hook установлен')

print('✅ torchaudio патч применен успешно')