# Makefile для WAN 2.2 RunPod Worker

.PHONY: help patch minor major commit push deploy status

help: ## Показать помощь
	@echo "Доступные команды:"
	@echo "  make patch  - Создать patch релиз (1.0.0 -> 1.0.1)"
	@echo "  make minor  - Создать minor релиз (1.0.0 -> 1.1.0)"  
	@echo "  make major  - Создать major релиз (1.0.0 -> 2.0.0)"
	@echo "  make commit - Добавить и закоммитить изменения"
	@echo "  make push   - Отправить изменения в Git репозиторий"
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

commit: ## Добавить и закоммитить изменения
	@VERSION=$$(python -c "from version import get_version; print(get_version())") && \
	echo "Коммичу изменения версии v$$VERSION" && \
	git add . && \
	git commit -m "Release v$$VERSION"

push: ## Отправить изменения в Git репозиторий
	@VERSION=$$(python -c "from version import get_version; print(get_version())") && \
	echo "Отправляю изменения в репозиторий..." && \
	git push origin master && \
	git tag "v$$VERSION" && \
	git push origin "v$$VERSION"

deploy: ## Развернуть на RunPod (требует runpod CLI)
	@if command -v runpod >/dev/null 2>&1; then \
		runpod project deploy; \
	else \
		echo "❌ RunPod CLI не установлен. Установите: pip install runpod"; \
		echo "💡 Или разверните вручную через RunPod Console"; \
	fi

# Показать версию как зависимость по умолчанию
%: status