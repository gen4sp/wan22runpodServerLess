"""
Ранний патч для предотвращения загрузки torchaudio
Этот файл выполняется при каждом запуске Python
"""
import sys
import os
from types import ModuleType

# Создаем mock torchaudio модуль
class MockTorchAudio:
    __version__ = "2.1.0+mock"
    __file__ = "/mock/torchaudio/__init__.py"
    
    def load(self, *args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")
    
    def save(self, *args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")
    
    # Добавляем отсутствующий атрибут lib
    class lib:
        pass
    
    class transforms:
        @staticmethod
        def Resample(*args, **kwargs):
            raise RuntimeError("torchaudio отключен в этой сборке")
    
    class functional:
        @staticmethod
        def resample(*args, **kwargs):
            raise RuntimeError("torchaudio отключен в этой сборке")
    
    backend = None

# Создаем модули для подмодулей
transforms_module = ModuleType('torchaudio.transforms')
transforms_module.Resample = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("torchaudio отключен в этой сборке"))

functional_module = ModuleType('torchaudio.functional')
functional_module.resample = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("torchaudio отключен в этой сборке"))

lib_module = ModuleType('torchaudio.lib')

# Заменяем torchaudio на mock версию в sys.modules
mock_torchaudio = MockTorchAudio()
mock_torchaudio.transforms = MockTorchAudio.transforms
mock_torchaudio.functional = MockTorchAudio.functional
mock_torchaudio.lib = MockTorchAudio.lib

sys.modules['torchaudio'] = mock_torchaudio
sys.modules['torchaudio.transforms'] = transforms_module
sys.modules['torchaudio.functional'] = functional_module
sys.modules['torchaudio.lib'] = lib_module

# Устанавливаем переменные окружения для отключения torchaudio
os.environ['CM_DISABLE_TORCHAUDIO'] = '1'
os.environ['DISABLE_TORCHAUDIO_CUDA_CHECK'] = '1'
os.environ['TORCH_AUDIO_BACKEND'] = 'soundfile'
os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'