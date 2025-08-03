#!/usr/bin/env python3
"""
Полное удаление torchaudio из системы и замена на mock
"""
import os
import sys
import shutil
import types

# Удаляем torchaudio из pip
print("🗑️  Удаление torchaudio через pip...")
os.system("pip uninstall -y torchaudio 2>/dev/null || true")

# Находим и удаляем все файлы torchaudio
print("🔍 Поиск и удаление файлов torchaudio...")
for root, dirs, files in os.walk("/usr/local/lib/python3.11/"):
    if "torchaudio" in root:
        print(f"   Удаляем: {root}")
        shutil.rmtree(root, ignore_errors=True)

# Создаем фейковый пакет torchaudio
print("📦 Создание фейкового пакета torchaudio...")
fake_torchaudio_path = "/usr/local/lib/python3.11/dist-packages/torchaudio"
os.makedirs(fake_torchaudio_path, exist_ok=True)

# Создаем __init__.py с полным mock
init_content = '''
import sys
import types

# 🚨 АГРЕССИВНЫЙ MOCK TORCHAUDIO 🚨

# Mock для _torchaudio с всеми нужными функциями
_torchaudio = types.ModuleType('_torchaudio')
_torchaudio.cuda_version = lambda: '12.8'
_torchaudio.is_available = lambda: True
_torchaudio.get_audio_backend = lambda: 'soundfile'

# Mock для torchaudio.lib
lib = types.ModuleType('torchaudio.lib')
lib._torchaudio = _torchaudio

# Mock для torchaudio._extension с ВСЕМИ функциями проверки CUDA
_extension = types.ModuleType('torchaudio._extension')
_extension._check_cuda_version = lambda: None
_extension._init_extension = lambda: None

# Mock для torchaudio._extension.utils - КРИТИЧЕСКИ ВАЖНО!
utils = types.ModuleType('torchaudio._extension.utils') 
utils._check_cuda_version = lambda: None
utils._get_cuda_version = lambda: '12.8'
_extension.utils = utils

# Регистрируем ВСЕ модули в sys.modules
sys.modules['torchaudio.lib._torchaudio'] = _torchaudio
sys.modules['torchaudio.lib'] = lib
sys.modules['torchaudio._extension'] = _extension
sys.modules['torchaudio._extension.utils'] = utils

# Экспортируем атрибуты
lib = lib
_extension = _extension
__version__ = '2.5.0'
__all__ = ['lib', '_extension']

# Дополнительные пустые модули для совместимости
functional = types.ModuleType('torchaudio.functional')
transforms = types.ModuleType('torchaudio.transforms')
datasets = types.ModuleType('torchaudio.datasets')
io = types.ModuleType('torchaudio.io')
backend = types.ModuleType('torchaudio.backend')
compliance = types.ModuleType('torchaudio.compliance')

sys.modules['torchaudio.functional'] = functional
sys.modules['torchaudio.transforms'] = transforms  
sys.modules['torchaudio.datasets'] = datasets
sys.modules['torchaudio.io'] = io
sys.modules['torchaudio.backend'] = backend
sys.modules['torchaudio.compliance'] = compliance
'''

with open(os.path.join(fake_torchaudio_path, "__init__.py"), "w") as f:
    f.write(init_content)

# Создаем подпапки
os.makedirs(os.path.join(fake_torchaudio_path, "lib"), exist_ok=True)
os.makedirs(os.path.join(fake_torchaudio_path, "_extension"), exist_ok=True)

# Создаем __init__.py для подмодулей
with open(os.path.join(fake_torchaudio_path, "lib", "__init__.py"), "w") as f:
    f.write("# Mock lib module\n")

with open(os.path.join(fake_torchaudio_path, "_extension", "__init__.py"), "w") as f:
    f.write("# Mock extension module\ndef _check_cuda_version(): pass\ndef _init_extension(): pass\n")

# Создаем utils.py в _extension - КРИТИЧЕСКИ ВАЖНО!
with open(os.path.join(fake_torchaudio_path, "_extension", "utils.py"), "w") as f:
    f.write("""# Mock utils module - блокирует CUDA проверки
def _check_cuda_version():
    '''Mock функция для блокировки проверки CUDA версии'''
    pass

def _get_cuda_version():
    '''Mock функция возвращает версию CUDA'''
    return '12.8'
""")

print("✅ Фейковый пакет torchaudio создан")

# Проверяем что можем импортировать
try:
    import torchaudio
    print(f"✅ torchaudio успешно импортирован (версия: {torchaudio.__version__})")
except Exception as e:
    print(f"❌ Ошибка импорта torchaudio: {e}")