#!/usr/bin/env python3
"""
Скрипт для первоначальной настройки проекта версионирования.
"""

import json
import subprocess
import sys
import os

def run_command(command, check=True):
    """Выполняет команду в shell."""
    print(f"Выполняется: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Ошибка при выполнении команды: {command}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    
    return True

def setup_git_hooks():
    """Создает git hooks для автоматической проверки версий."""
    hooks_dir = ".git/hooks"
    if not os.path.exists(hooks_dir):
        print("❌ Директория .git/hooks не найдена. Убедитесь что вы в git репозитории.")
        return False
    
    # Pre-commit hook для проверки версии
    pre_commit_content = """#!/bin/sh
# Pre-commit hook для проверки версии

python3 -c "
try:
    from version import get_version
    print(f'Текущая версия: {get_version()}')
except Exception as e:
    print(f'❌ Ошибка в version.py: {e}')
    exit(1)
"
"""
    
    hook_path = os.path.join(hooks_dir, "pre-commit")
    with open(hook_path, "w") as f:
        f.write(pre_commit_content)
    
    os.chmod(hook_path, 0o755)
    print("✅ Git pre-commit hook создан")
    return True

def update_docker_config():
    """Обновляет Docker конфигурацию с корректными именами."""
    dockerhub_username = input("Введите ваш Docker Hub username (или нажмите Enter для пропуска): ").strip()
    
    if not dockerhub_username:
        print("⏭️  Пропускаем настройку Docker Hub")
        return True
    
    try:
        with open("deploy_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Обновляем Docker image
        config["dockerImage"] = f"{dockerhub_username}/wan22-worker:v1.0.0"
        
        with open("deploy_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Docker image обновлен: {dockerhub_username}/wan22-worker:v1.0.0")
        
        # Обновляем GitHub Actions workflow
        with open(".github/workflows/release.yml", "r", encoding="utf-8") as f:
            workflow = f.read()
        
        workflow = workflow.replace(
            "IMAGE_NAME: your-dockerhub-username/wan22-worker",
            f"IMAGE_NAME: {dockerhub_username}/wan22-worker"
        )
        
        with open(".github/workflows/release.yml", "w", encoding="utf-8") as f:
            f.write(workflow)
        
        print("✅ GitHub Actions workflow обновлен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления конфигурации: {e}")
        return False

def check_dependencies():
    """Проверяет необходимые зависимости."""
    print("Проверка зависимостей...")
    
    # Git
    if not run_command("git --version", check=False):
        print("❌ Git не установлен")
        return False
    print("✅ Git установлен")
    
    # Python
    if not run_command("python3 --version", check=False):
        print("❌ Python 3 не установлен")
        return False
    print("✅ Python 3 установлен")
    
    # jq (для Makefile)
    if not run_command("jq --version", check=False):
        print("⚠️  jq не установлен. Некоторые команды Makefile могут не работать.")
        print("   Установите: brew install jq (macOS) или apt install jq (Ubuntu)")
    else:
        print("✅ jq установлен")
    
    # GitHub CLI (опционально)
    if not run_command("gh --version", check=False):
        print("⚠️  GitHub CLI не установлен. Автоматическое создание releases не будет работать.")
        print("   Установите: https://cli.github.com/")
    else:
        print("✅ GitHub CLI установлен")
        
        # Проверяем авторизацию
        if not run_command("gh auth status", check=False):
            print("⚠️  Не авторизованы в GitHub CLI. Выполните: gh auth login")
        else:
            print("✅ GitHub CLI авторизован")
    
    return True

def main():
    print("🚀 Настройка системы версионирования для WAN 2.2 RunPod Worker")
    print("=" * 60)
    
    # Проверяем зависимости
    if not check_dependencies():
        print("❌ Не все зависимости установлены. Исправьте ошибки и попробуйте снова.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Настраиваем Docker конфигурацию
    if not update_docker_config():
        print("❌ Ошибка настройки Docker конфигурации")
        sys.exit(1)
    
    # Настраиваем git hooks
    if not setup_git_hooks():
        print("❌ Ошибка настройки git hooks")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Настройка завершена!")
    print("\nТеперь вы можете:")
    print("  • Создавать релизы: make patch/minor/major")
    print("  • Собирать Docker images: make build")
    print("  • Просматривать статус: make status")
    print("  • Получать помощь: make help")
    
    print(f"\n📖 Полная документация: docs/releases.md")
    
    # Предлагаем создать первый релиз
    response = input("\n❓ Создать первый релиз (v1.0.0)? (y/N): ")
    if response.lower() == 'y':
        if run_command("python release.py patch", check=False):
            print("🎉 Первый релиз создан!")
        else:
            print("❌ Ошибка создания релиза. Попробуйте вручную: python release.py patch")

if __name__ == "__main__":
    main()