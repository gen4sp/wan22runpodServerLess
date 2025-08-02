# -*- coding: utf-8 -*-
"""
Обработчик произвольных JSON воркфлоу
"""
from typing import Dict, Any, Optional, Tuple
import logging
from .base import WorkflowType, WorkflowAnalyzer, WorkflowProcessor

logger = logging.getLogger(__name__)


class WorkflowHandler:
    """Обрабатывает произвольные JSON воркфлоу"""
    
    @staticmethod
    def process_workflow_request(
        workflow: Dict[str, Any],
        prompt: Optional[str] = None,
        image_data: Optional[str] = None,
        video_data: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], WorkflowType, Dict[str, Any]]:
        """
        Обрабатывает запрос с произвольным воркфлоу
        
        Args:
            workflow: JSON воркфлоу ComfyUI
            prompt: Текстовый промпт
            image_data: Данные изображения (base64)
            video_data: Данные видео (base64) 
            options: Дополнительные опции
            
        Returns:
            Tuple (подготовленный_воркфлоу, тип_воркфлоу, метаданные)
        """
        try:
            # Анализируем тип воркфлоу
            workflow_type = WorkflowAnalyzer.analyze_workflow(workflow)
            logger.info(f"Определен тип воркфлоу: {workflow_type.value}")
            
            # Подготавливаем файлы входных данных
            image_filename = None
            video_filename = None
            
            if image_data:
                image_filename = WorkflowHandler._save_input_image(image_data)
                logger.info(f"Сохранено входное изображение: {image_filename}")
            
            if video_data:
                video_filename = WorkflowHandler._save_input_video(video_data)
                logger.info(f"Сохранено входное видео: {video_filename}")
            
            # Валидируем совместимость данных с типом воркфлоу
            WorkflowHandler._validate_inputs(workflow_type, prompt, image_filename, video_filename)
            
            # Подготавливаем воркфлоу к выполнению
            prepared_workflow = WorkflowProcessor.prepare_workflow(
                workflow=workflow,
                workflow_type=workflow_type,
                prompt=prompt,
                image_filename=image_filename,
                video_filename=video_filename,
                options=options
            )
            
            # Собираем метаданные
            metadata = {
                "workflow_type": workflow_type.value,
                "has_prompt": bool(prompt),
                "has_image": bool(image_filename),
                "has_video": bool(video_filename),
                "node_count": len(workflow),
                "options_applied": bool(options)
            }
            
            return prepared_workflow, workflow_type, metadata
            
        except Exception as e:
            logger.error(f"Ошибка обработки воркфлоу: {e}")
            raise
    
    @staticmethod
    def _save_input_image(image_data: str) -> str:
        """Сохраняет входное изображение из base64"""
        import base64
        import os
        from PIL import Image
        import io
        
        try:
            # Декодируем base64 если есть префикс data:image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Декодируем base64
            image_bytes = base64.b64decode(image_data)
            
            # Открываем изображение через PIL для валидации
            image = Image.open(io.BytesIO(image_bytes))
            
            # Генерируем уникальное имя файла
            import time
            filename = f"input_image_{int(time.time())}.png"
            
            # Сохраняем в input директорию ComfyUI
            input_dir = "/comfyui/input"
            os.makedirs(input_dir, exist_ok=True)
            
            image_path = os.path.join(input_dir, filename)
            image.save(image_path)
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка сохранения изображения: {e}")
            raise ValueError(f"Не удалось обработать входное изображение: {e}")
    
    @staticmethod
    def _save_input_video(video_data: str) -> str:
        """Сохраняет входное видео из base64"""
        import base64
        import os
        import time
        
        try:
            # Декодируем base64
            if video_data.startswith('data:video'):
                video_data = video_data.split(',')[1]
            
            video_bytes = base64.b64decode(video_data)
            
            # Генерируем уникальное имя файла
            filename = f"input_video_{int(time.time())}.mp4"
            
            # Сохраняем в input директорию ComfyUI
            input_dir = "/comfyui/input"
            os.makedirs(input_dir, exist_ok=True)
            
            video_path = os.path.join(input_dir, filename)
            with open(video_path, "wb") as f:
                f.write(video_bytes)
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка сохранения видео: {e}")
            raise ValueError(f"Не удалось обработать входное видео: {e}")
    
    @staticmethod
    def _validate_inputs(
        workflow_type: WorkflowType, 
        prompt: Optional[str], 
        image_filename: Optional[str], 
        video_filename: Optional[str]
    ):
        """Валидирует совместимость входных данных с типом воркфлоу"""
        
        if workflow_type == WorkflowType.T2V:
            # Text-to-Video требует промпт, изображение опционально
            if not prompt:
                raise ValueError("T2V воркфлоу требует текстовый промпт")
        
        elif workflow_type == WorkflowType.T2I:
            # Text-to-Image требует промпт
            if not prompt:
                raise ValueError("T2I воркфлоу требует текстовый промпт")
        
        elif workflow_type == WorkflowType.IMG2IMG:
            # Image-to-Image требует изображение, промпт опционален
            if not image_filename:
                raise ValueError("Img2Img воркфлоу требует входное изображение")
        
        elif workflow_type == WorkflowType.VIDEO_UPSCALE:
            # Video Upscale требует видео
            if not video_filename:
                raise ValueError("Video Upscale воркфлоу требует входное видео")
        
        elif workflow_type == WorkflowType.UNKNOWN:
            logger.warning("Тип воркфлоу не определен, валидация пропущена")
    
    @staticmethod
    def get_expected_output_type(workflow_type: WorkflowType) -> str:
        """Возвращает ожидаемый тип выходного файла"""
        if workflow_type in [WorkflowType.T2V, WorkflowType.VIDEO_UPSCALE]:
            return "video"
        elif workflow_type in [WorkflowType.T2I, WorkflowType.IMG2IMG]:
            return "image"
        else:
            return "unknown"
    
    @staticmethod
    def get_workflow_info(workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Возвращает информацию о воркфлоу"""
        workflow_type = WorkflowAnalyzer.analyze_workflow(workflow)
        node_types = WorkflowAnalyzer._extract_node_types(workflow)
        
        return {
            "workflow_type": workflow_type.value,
            "node_count": len(workflow),
            "node_types": list(node_types),
            "expected_output": WorkflowHandler.get_expected_output_type(workflow_type),
            "supports_prompt": workflow_type in [WorkflowType.T2V, WorkflowType.T2I],
            "requires_image": workflow_type == WorkflowType.IMG2IMG,
            "requires_video": workflow_type == WorkflowType.VIDEO_UPSCALE
        }


# Глобальный экземпляр обработчика
workflow_handler = WorkflowHandler()


# Удобные функции для совместимости
def process_workflow(
    workflow: Dict[str, Any],
    prompt: Optional[str] = None,
    image_data: Optional[str] = None,
    video_data: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], WorkflowType, Dict[str, Any]]:
    """
    Обрабатывает произвольный JSON воркфлоу
    """
    return workflow_handler.process_workflow_request(
        workflow, prompt, image_data, video_data, options
    )


def analyze_workflow(workflow: Dict[str, Any]) -> WorkflowType:
    """
    Анализирует тип воркфлоу
    """
    return WorkflowAnalyzer.analyze_workflow(workflow)


def get_workflow_info(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Получает информацию о воркфлоу
    """
    return WorkflowHandler.get_workflow_info(workflow)