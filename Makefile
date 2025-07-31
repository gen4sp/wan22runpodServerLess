# Makefile для WAN 2.2 RunPod Worker

.PHONY: help patch minor major build push deploy status

help: ## Показать помощь
	@echo "Доступные команды:"
	@echo "  make patch  - Создать patch релиз (1.0.0 -> 1.0.1)"
	@echo "  make minor  - Создать minor релиз (1.0.0 -> 1.1.0)"  
	@echo "  make major  - Создать major релиз (1.0.0 -> 2.0.0)"
	@echo "  make build  - Собрать Docker image"
	@echo "  make push   - Отправить Docker image в registry"
	@echo "  make deploy - Развернуть на RunPod"
	@echo "  make status - Показать текущую версию"

patch: ## Создать patch релиз
	python release.py patch

minor: ## Создать minor релиз  
	python release.py minor

major: ## Создать major релиз
	python release.py major

status: ## Показать текущую версию
	@python -c "from version import get_version; print(f'Текущая версия: {get_version()}')"

build: ## Собрать Docker image
	@VERSION=$$(python -c "from version import get_version; print(get_version())") && \
	IMAGE_NAME=$$(jq -r '.dockerImage' deploy_config.json | cut -d':' -f1) && \
	echo "Сборка Docker image: $$IMAGE_NAME:v$$VERSION" && \
	docker build -t $$IMAGE_NAME:v$$VERSION -t $$IMAGE_NAME:latest .

push: ## Отправить Docker image в registry
	@VERSION=$$(python -c "from version import get_version; print(get_version())") && \
	IMAGE_NAME=$$(jq -r '.dockerImage' deploy_config.json | cut -d':' -f1) && \
	echo "Отправка Docker image: $$IMAGE_NAME:v$$VERSION" && \
	docker push $$IMAGE_NAME:v$$VERSION && \
	docker push $$IMAGE_NAME:latest

deploy: ## Развернуть на RunPod (требует runpod CLI)
	@if command -v runpod >/dev/null 2>&1; then \
		runpod project deploy; \
	else \
		echo "❌ RunPod CLI не установлен. Установите: pip install runpod"; \
		echo "💡 Или разверните вручную через RunPod Console"; \
	fi

# Показать версию как зависимость по умолчанию
%: status