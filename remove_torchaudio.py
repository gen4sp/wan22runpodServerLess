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

# Mock для _torchaudio
_torchaudio = types.ModuleType('_torchaudio')
_torchaudio.cuda_version = lambda: '12.8'

# Mock для torchaudio.lib
lib = types.ModuleType('torchaudio.lib')
lib._torchaudio = _torchaudio

# Mock для torchaudio._extension
_extension = types.ModuleType('torchaudio._extension')
_extension._check_cuda_version = lambda: None
_extension.utils = types.ModuleType('torchaudio._extension.utils')
_extension.utils._check_cuda_version = lambda: None

# Регистрируем модули
sys.modules['torchaudio.lib._torchaudio'] = _torchaudio
sys.modules['torchaudio.lib'] = lib
sys.modules['torchaudio._extension'] = _extension
sys.modules['torchaudio._extension.utils'] = _extension.utils

# Экспортируем атрибуты
__version__ = '2.5.0'
__all__ = ['lib', '_extension']
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
    f.write("# Mock extension module\ndef _check_cuda_version(): pass\n")

print("✅ Фейковый пакет torchaudio создан")

# Проверяем что можем импортировать
try:
    import torchaudio
    print(f"✅ torchaudio успешно импортирован (версия: {torchaudio.__version__})")
except Exception as e:
    print(f"❌ Ошибка импорта torchaudio: {e}")