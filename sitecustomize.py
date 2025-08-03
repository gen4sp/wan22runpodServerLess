"""\nРанний патч torchaudio: создаёт mock модуль до любых импортов.\nКопируется в /usr/local/lib/python3.11/dist-packages/sitecustomize.py контейнера,\nчто гарантирует загрузку при каждом запуске Python.\n"""
import sys
import types


def create_mock_torchaudio():
    """Создаёт mock-модуль torchaudio, совместимый с ComfyUI."""
    # mock для _torchaudio
    _torchaudio = types.ModuleType('_torchaudio')
    _torchaudio.cuda_version = lambda: '12.8'

    # mock для torchaudio.lib
    lib = types.ModuleType('torchaudio.lib')
    lib._torchaudio = _torchaudio

    # mock для torchaudio._extension
    extension = types.ModuleType('torchaudio._extension')
    extension._check_cuda_version = lambda: None

    # основной mock torchaudio
    torchaudio = types.ModuleType('torchaudio')
    torchaudio.lib = lib
    torchaudio._extension = extension
    torchaudio.__version__ = '2.5.0'

    # регистрируем в sys.modules
    sys.modules['torchaudio'] = torchaudio
    sys.modules['torchaudio.lib'] = lib
    sys.modules['torchaudio.lib._torchaudio'] = _torchaudio
    sys.modules['torchaudio._extension'] = extension

    return torchaudio

# применяем сразу
create_mock_torchaudio()