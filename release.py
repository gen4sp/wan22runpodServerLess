#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инкрементирования версии и создания GitHub release.

Использование:
    python release.py patch   # 1.0.0 -> 1.0.1
    python release.py minor   # 1.0.0 -> 1.1.0
    python release.py major   # 1.0.0 -> 2.0.0
"""

import sys
import json
import subprocess
import os
import re
from pathlib import Path

def get_current_version():
    """Получает текущую версию из version.py."""
    with open("version.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r'__version__ = "(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Не удалось найти версию в version.py")
    
    return match.group(1)

def increment_version(version, increment_type):
    """Инкрементирует версию."""
    major, minor, patch = map(int, version.split("."))
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    elif increment_type == "patch":
        patch += 1
    else:
        raise ValueError("Тип инкремента должен быть 'major', 'minor' или 'patch'")
    
    return f"{major}.{minor}.{patch}"

def update_version_file(new_version):
    """Обновляет файл version.py с новой версией."""
    with open("version.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Обновляем версию
    content = re.sub(
        r'__version__ = "\d+\.\d+\.\d+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    # Обновляем версию инфо
    version_info = ', '.join(new_version.split('.'))
    content = re.sub(
        r'__version_info__ = tuple\(map\(int, __version__\.split\("\."\)\)\)',
        f'__version_info__ = ({version_info})',
        content
    )
    
    with open("version.py", "w", encoding="utf-8") as f:
        f.write(content)

def update_deploy_config(new_version):
    """Обновляет deploy_config.json с новой версией в Docker image."""
    with open("deploy_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Обновляем Docker image tag
    current_image = config.get("dockerImage", "")
    base_image = current_image.split(":")[0] if ":" in current_image else current_image
    config["dockerImage"] = f"{base_image}:v{new_version}"
    
    with open("deploy_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def run_command(command, check=True):
    """Выполняет команду в shell."""
    print(f"Выполняется: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Ошибка при выполнении команды: {command}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    
    return result

def git_commit_and_tag(version):
    """Создает git commit и tag."""
    run_command("git add version.py deploy_config.json")
    run_command(f'git commit -m "chore: bump version to {version}"')
    run_command(f"git tag -a v{version} -m 'Release v{version}'")

def create_github_release(version):
    """Создает GitHub release используя gh CLI."""
    # Проверяем, установлен ли gh CLI
    result = run_command("which gh", check=False)
    if result.returncode != 0:
        print("⚠️  GitHub CLI (gh) не установлен. Пропускаем создание GitHub release.")
        print("Установите gh CLI: https://cli.github.com/")
        return
    
    # Проверяем авторизацию
    result = run_command("gh auth status", check=False)
    if result.returncode != 0:
        print("⚠️  Не авторизованы в GitHub CLI. Пропускаем создание GitHub release.")
        print("Выполните: gh auth login")
        return
    
    # Создаем release
    release_notes = f"""# WAN 2.2 RunPod Worker v{version}

## Изменения
- Обновление версии до {version}

## Docker Image
```
docker pull $(jq -r '.dockerImage' deploy_config.json)
```

## Развертывание на RunPod
1. Обновите конфигурацию в `deploy_config.json`
2. Разверните через RunPod Console или API
"""
    
    # Создаем временный файл с release notes
    with open("temp_release_notes.md", "w", encoding="utf-8") as f:
        f.write(release_notes)
    
    try:
        run_command(f'gh release create v{version} --title "v{version}" --notes-file temp_release_notes.md')
        print(f"✅ GitHub release v{version} создан успешно!")
    finally:
        # Удаляем временный файл
        if os.path.exists("temp_release_notes.md"):
            os.remove("temp_release_notes.md")

def main():
    if len(sys.argv) != 2:
        print("Использование: python release.py [patch|minor|major]")
        sys.exit(1)
    
    increment_type = sys.argv[1].lower()
    if increment_type not in ["patch", "minor", "major"]:
        print("Тип инкремента должен быть 'patch', 'minor' или 'major'")
        sys.exit(1)
    
    try:
        # Проверяем, что мы в git репозитории
        run_command("git status")
        
        # Проверяем, что нет незакоммиченных изменений
        result = run_command("git status --porcelain", check=False)
        if result.stdout.strip():
            print("⚠️  Есть незакоммиченные изменения. Закоммитьте их перед созданием релиза.")
            print(result.stdout)
            sys.exit(1)
        
        current_version = get_current_version()
        new_version = increment_version(current_version, increment_type)
        
        print(f"Текущая версия: {current_version}")
        print(f"Новая версия: {new_version}")
        
        # Подтверждение
        response = input(f"Создать релиз v{new_version}? (y/N): ")
        if response.lower() != 'y':
            print("Отменено.")
            sys.exit(0)
        
        # Обновляем файлы
        print("Обновляем файлы версии...")
        update_version_file(new_version)
        update_deploy_config(new_version)
        
        # Git операции
        print("Создаем git commit и tag...")
        git_commit_and_tag(new_version)
        
        # Пушим изменения
        print("Отправляем изменения в remote...")
        run_command("git push")
        run_command("git push --tags")
        
        # Создаем GitHub release
        print("Создаем GitHub release...")
        create_github_release(new_version)
        
        print(f"🎉 Релиз v{new_version} создан успешно!")
        print(f"📝 Обновите Docker image и разверните на RunPod:")
        print(f"   docker build -t your-dockerhub-username/wan22-worker:v{new_version} .")
        print(f"   docker push your-dockerhub-username/wan22-worker:v{new_version}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()