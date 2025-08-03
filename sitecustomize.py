"""
Ранний патч для предотвращения загрузки torchaudio
Этот файл выполняется при каждом запуске Python
"""
import sys
import os

# Создаем mock torchaudio модуль
class MockTorchAudio:
    __version__ = "2.1.0+mock"
    
    def load(self, *args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")
    
    def save(self, *args, **kwargs):
        raise RuntimeError("torchaudio отключен в этой сборке")
    
    class transforms:
        @staticmethod
        def Resample(*args, **kwargs):
            raise RuntimeError("torchaudio отключен в этой сборке")
    
    class functional:
        @staticmethod
        def resample(*args, **kwargs):
            raise RuntimeError("torchaudio отключен в этой сборке")
    
    backend = None

# Заменяем torchaudio на mock версию в sys.modules
sys.modules['torchaudio'] = MockTorchAudio()
sys.modules['torchaudio.transforms'] = MockTorchAudio.transforms()
sys.modules['torchaudio.functional'] = MockTorchAudio.functional()

# Устанавливаем переменные окружения для отключения torchaudio
os.environ['CM_DISABLE_TORCHAUDIO'] = '1'
os.environ['DISABLE_TORCHAUDIO_CUDA_CHECK'] = '1'
os.environ['TORCH_AUDIO_BACKEND'] = 'soundfile'
os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'