# -*- coding: utf-8 -*-
"""
Базовый класс для воркфлоу
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time


class WorkflowBase(ABC):
    """Базовый класс для всех воркфлоу"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0"
    
    @abstractmethod
    def create_workflow(self, prompt: str, image_filename: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Создает воркфлоу для ComfyUI
        
        Args:
            prompt: Текстовый промпт
            image_filename: Имя файла изображения
            options: Дополнительные опции
            
        Returns:
            Словарь с воркфлоу для ComfyUI
        """
        pass
    
    @abstractmethod
    def get_default_options(self) -> Dict[str, Any]:
        """
        Возвращает опции по умолчанию для воркфлоу
        
        Returns:
            Словарь с опциями по умолчанию
        """
        pass
    
    @abstractmethod
    def supports_t2v(self) -> bool:
        """
        Поддерживает ли воркфлоу режим Text-to-Video
        
        Returns:
            True если поддерживает T2V режим
        """
        pass
    
    @abstractmethod
    def supports_i2v(self) -> bool:
        """
        Поддерживает ли воркфлоу режим Image-to-Video
        
        Returns:
            True если поддерживает I2V режим
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о воркфлоу
        
        Returns:
            Словарь с информацией о воркфлоу
        """
        return {
            "name": self.name,
            "version": self.version,
            "supports_t2v": self.supports_t2v(),
            "supports_i2v": self.supports_i2v(),
            "default_options": self.get_default_options()
        }
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидирует и нормализует опции
        
        Args:
            options: Входные опции
            
        Returns:
            Нормализованные опции
        """
        default_options = self.get_default_options()
        validated_options = default_options.copy()
        
        if options:
            validated_options.update(options)
            
        return validated_options
    
    def generate_seed(self) -> int:
        """Генерирует случайный сид"""
        return int(time.time())