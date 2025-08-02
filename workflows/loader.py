# -*- coding: utf-8 -*-
"""
Система загрузки воркфлоу
"""
from typing import Dict, Type, Optional
import importlib
import logging
from .base import WorkflowBase
from .wan22 import WAN22Workflow
from .simple_test import SimpleTestWorkflow

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Реестр доступных воркфлоу"""
    
    def __init__(self):
        self._workflows: Dict[str, Type[WorkflowBase]] = {}
        self._register_default_workflows()
    
    def _register_default_workflows(self):
        """Регистрирует воркфлоу по умолчанию"""
        self.register("wan22", WAN22Workflow)
        self.register("wan2.2", WAN22Workflow)  # Альтернативное имя
        self.register("default", WAN22Workflow)  # По умолчанию
        self.register("test", SimpleTestWorkflow)  # Тестовый воркфлоу
        self.register("simple", SimpleTestWorkflow)  # Альтернативное имя
    
    def register(self, name: str, workflow_class: Type[WorkflowBase]):
        """
        Регистрирует воркфлоу в реестре
        
        Args:
            name: Имя воркфлоу
            workflow_class: Класс воркфлоу
        """
        if not issubclass(workflow_class, WorkflowBase):
            raise ValueError(f"Класс {workflow_class} должен наследовать WorkflowBase")
        
        self._workflows[name.lower()] = workflow_class
        logger.info(f"Зарегистрирован воркфлоу: {name}")
    
    def get_workflow(self, name: str) -> Optional[WorkflowBase]:
        """
        Получает экземпляр воркфлоу по имени
        
        Args:
            name: Имя воркфлоу
            
        Returns:
            Экземпляр воркфлоу или None
        """
        workflow_class = self._workflows.get(name.lower())
        if workflow_class:
            return workflow_class()
        return None
    
    def list_workflows(self) -> Dict[str, Dict]:
        """
        Возвращает список всех доступных воркфлоу
        
        Returns:
            Словарь с информацией о воркфлоу
        """
        workflows_info = {}
        for name, workflow_class in self._workflows.items():
            try:
                workflow_instance = workflow_class()
                workflows_info[name] = workflow_instance.get_info()
            except Exception as e:
                logger.error(f"Ошибка получения информации о воркфлоу {name}: {e}")
                workflows_info[name] = {"error": str(e)}
        
        return workflows_info
    
    def workflow_exists(self, name: str) -> bool:
        """
        Проверяет, существует ли воркфлоу с данным именем
        
        Args:
            name: Имя воркфлоу
            
        Returns:
            True если воркфлоу существует
        """
        return name.lower() in self._workflows
    
    def load_workflow_from_module(self, module_path: str, class_name: str, workflow_name: str):
        """
        Загружает воркфлоу из внешнего модуля
        
        Args:
            module_path: Путь к модулю
            class_name: Имя класса воркфлоу
            workflow_name: Имя для регистрации
        """
        try:
            module = importlib.import_module(module_path)
            workflow_class = getattr(module, class_name)
            self.register(workflow_name, workflow_class)
            logger.info(f"Загружен воркфлоу {workflow_name} из {module_path}.{class_name}")
        except Exception as e:
            logger.error(f"Ошибка загрузки воркфлоу {workflow_name}: {e}")
            raise


# Глобальный экземпляр реестра
workflow_registry = WorkflowRegistry()


def get_workflow(name: str) -> Optional[WorkflowBase]:
    """
    Удобная функция для получения воркфлоу
    
    Args:
        name: Имя воркфлоу
        
    Returns:
        Экземпляр воркфлоу или None
    """
    return workflow_registry.get_workflow(name)


def list_available_workflows() -> Dict[str, Dict]:
    """
    Возвращает список всех доступных воркфлоу
    
    Returns:
        Словарь с информацией о воркфлоу
    """
    return workflow_registry.list_workflows()


def register_workflow(name: str, workflow_class: Type[WorkflowBase]):
    """
    Регистрирует новый воркфлоу
    
    Args:
        name: Имя воркфлоу
        workflow_class: Класс воркфлоу
    """
    workflow_registry.register(name, workflow_class)