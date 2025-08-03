"""
🚨 КРИТИЧЕСКИ ВАЖНЫЙ ПАТЧ torchaudio 🚨
Создаёт агрессивный mock модуль torchaudio ДО любых импортов.
Копируется в /usr/local/lib/python3.11/dist-packages/sitecustomize.py контейнера,
что гарантирует загрузку при каждом запуске Python.
"""
import sys
import types
import importlib.util


def create_aggressive_mock_torchaudio():
    """Создаёт агрессивный mock-модуль torchaudio, совместимый с ComfyUI."""
    
    # Создаем все необходимые подмодули
    modules_to_mock = [
        'torchaudio',
        'torchaudio.lib',
        'torchaudio.lib._torchaudio', 
        'torchaudio._extension',
        'torchaudio._extension.utils',
        'torchaudio.functional',
        'torchaudio.transforms',
        'torchaudio.datasets',
        'torchaudio.io',
        'torchaudio.backend',
        'torchaudio.compliance'
    ]
    
    # Создаем базовые mock модули
    for module_name in modules_to_mock:
        if module_name not in sys.modules:
            mock_module = types.ModuleType(module_name)
            sys.modules[module_name] = mock_module
    
    # Настраиваем основной torchaudio модуль
    torchaudio = sys.modules['torchaudio']
    torchaudio.__version__ = '2.5.0'
    torchaudio.__file__ = '/usr/local/lib/python3.11/dist-packages/torchaudio/__init__.py'
    
    # Настраиваем torchaudio.lib._torchaudio с нужными функциями
    _torchaudio = sys.modules['torchaudio.lib._torchaudio']
    _torchaudio.cuda_version = lambda: '12.8'
    _torchaudio.is_available = lambda: True
    
    # Настраиваем torchaudio.lib
    lib = sys.modules['torchaudio.lib']
    lib._torchaudio = _torchaudio
    torchaudio.lib = lib
    
    # Настраиваем torchaudio._extension с функциями проверки CUDA
    extension = sys.modules['torchaudio._extension']
    extension._check_cuda_version = lambda: None
    extension._init_extension = lambda: None
    torchaudio._extension = extension
    
    # Настраиваем torchaudio._extension.utils
    utils = sys.modules['torchaudio._extension.utils']
    utils._check_cuda_version = lambda: None
    utils._get_cuda_version = lambda: '12.8'
    extension.utils = utils
    
    # Добавляем другие часто используемые атрибуты
    torchaudio.functional = sys.modules['torchaudio.functional']
    torchaudio.transforms = sys.modules['torchaudio.transforms']
    torchaudio.datasets = sys.modules['torchaudio.datasets']
    torchaudio.io = sys.modules['torchaudio.io']
    torchaudio.backend = sys.modules['torchaudio.backend']
    torchaudio.compliance = sys.modules['torchaudio.compliance']
    
    return torchaudio


def block_torchaudio_import():
    """Блокирует реальные импорты torchaudio через import hook."""
    original_import = __builtins__.__import__
    
    def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Если пытаются импортировать torchaudio - возвращаем наш mock
        if name == 'torchaudio' or name.startswith('torchaudio.'):
            if name in sys.modules:
                return sys.modules[name]
            else:
                # Создаем недостающий подмодуль на лету
                mock_module = types.ModuleType(name)
                sys.modules[name] = mock_module
                return mock_module
        
        # Для всех остальных модулей - обычный импорт
        return original_import(name, globals, locals, fromlist, level)
    
    __builtins__.__import__ = patched_import


# 🚨 ПРИМЕНЯЕМ ПАТЧИ НЕМЕДЛЕННО 🚨
print("🔧 Применяем агрессивный torchaudio mock...")
create_aggressive_mock_torchaudio()
block_torchaudio_import()
print("✅ torchaudio mock активирован через sitecustomize.py")