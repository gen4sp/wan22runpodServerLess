#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления torchaudio
"""

def test_torchaudio_import():
    """Тестирует импорт torchaudio"""
    try:
        import torchaudio
        print(f"✅ torchaudio импортирован успешно: {torchaudio.__version__}")
        
        # Проверяем все необходимые атрибуты
        required_attrs = ['lib', 'transforms', 'functional', 'backend', '__version__']
        missing_attrs = []
        
        for attr in required_attrs:
            if hasattr(torchaudio, attr):
                print(f"✅ {attr}: найден")
            else:
                missing_attrs.append(attr)
                print(f"❌ {attr}: отсутствует")
        
        if missing_attrs:
            print(f"❌ Отсутствуют атрибуты: {missing_attrs}")
            return False
        else:
            print("✅ Все необходимые атрибуты найдены")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка импорта torchaudio: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_submodules():
    """Тестирует импорт подмодулей torchaudio"""
    try:
        import torchaudio.transforms
        import torchaudio.functional
        import torchaudio.lib
        print("✅ Все подмодули импортированы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта подмодулей: {e}")
        return False

def test_circular_import():
    """Тестирует отсутствие круговых импортов"""
    try:
        # Это должно работать без ошибок
        import sys
        if 'torchaudio' in sys.modules:
            del sys.modules['torchaudio']
        if 'torchaudio.transforms' in sys.modules:
            del sys.modules['torchaudio.transforms']
        if 'torchaudio.functional' in sys.modules:
            del sys.modules['torchaudio.functional']
        if 'torchaudio.lib' in sys.modules:
            del sys.modules['torchaudio.lib']
            
        # Переимпортируем
        import torchaudio
        print("✅ Круговые импорты отсутствуют")
        return True
    except Exception as e:
        print(f"❌ Проблема с круговыми импортами: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование исправления torchaudio...")
    
    results = []
    results.append(test_torchaudio_import())
    results.append(test_submodules())
    results.append(test_circular_import())
    
    if all(results):
        print("\n🎉 Все тесты пройдены успешно!")
        exit(0)
    else:
        print(f"\n❌ Некоторые тесты не пройдены: {sum(results)}/{len(results)}")
        exit(1)