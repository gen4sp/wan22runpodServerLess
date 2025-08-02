# -*- coding: utf-8 -*-
"""
Система обработки воркфлоу ComfyUI
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Set
import time
import logging

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Типы воркфлоу"""
    T2V = "text_to_video"           # Text to Video
    T2I = "text_to_image"           # Text to Image  
    IMG2IMG = "image_to_image"      # Image to Image
    VIDEO_UPSCALE = "video_upscale" # Video Upscaling
    UNKNOWN = "unknown"


class WorkflowAnalyzer:
    """Анализирует JSON воркфлоу и определяет его тип"""
    
    # Узлы, указывающие на различные типы воркфлоу
    VIDEO_OUTPUT_NODES = {
        "VHS_VideoCombine", "SaveVideo", "VideoOutput", 
        "WanImageToVideo", "AnimateDiff", "SVD_img2vid_Conditioning"
    }
    
    IMAGE_OUTPUT_NODES = {
        "SaveImage", "ImageOutput", "PreviewImage"
    }
    
    VIDEO_INPUT_NODES = {
        "LoadVideo", "VideoInput", "VHS_LoadVideo"
    }
    
    IMAGE_INPUT_NODES = {
        "LoadImage", "ImageInput"
    }
    
    TEXT_ENCODE_NODES = {
        "CLIPTextEncode", "TextEncode"
    }
    
    UPSCALE_NODES = {
        "VideoUpscale", "ESRGAN", "RealESRGAN", "ImageUpscaleWithModel",
        "VideoLinearCFGGuidance", "VideoUpscaler"
    }
    
    WAN_SPECIFIC_NODES = {
        "WanImageToVideo", "WanTextToVideo"
    }
    
    @classmethod
    def analyze_workflow(cls, workflow: Dict[str, Any]) -> WorkflowType:
        """
        Анализирует воркфлоу и определяет его тип
        
        Args:
            workflow: JSON воркфлоу ComfyUI
            
        Returns:
            Тип воркфлоу
        """
        try:
            node_types = cls._extract_node_types(workflow)
            return WorkflowType.T2I
            # Проверяем на Video Upscale
            # if cls._has_video_upscale_pattern(node_types, workflow):
            #     return WorkflowType.VIDEO_UPSCALE
            
            # # Проверяем на T2V (Text to Video)
            # if cls._has_t2v_pattern(node_types, workflow):
            #     return WorkflowType.T2V
            
            # # Проверяем на T2I (Text to Image)
            # if cls._has_t2i_pattern(node_types, workflow):
            #     return WorkflowType.T2I
            
            # # Проверяем на Img2Img
            # if cls._has_img2img_pattern(node_types, workflow):
            #     return WorkflowType.IMG2IMG
            
            # logger.warning(f"Не удалось определить тип воркфлоу. Найденные узлы: {node_types}")
            # return WorkflowType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Ошибка анализа воркфлоу: {e}")
            return WorkflowType.UNKNOWN
    
    @classmethod
    def _extract_node_types(cls, workflow: Dict[str, Any]) -> Set[str]:
        """Извлекает типы узлов из воркфлоу"""
        node_types = set()
        
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and "class_type" in node_data:
                node_types.add(node_data["class_type"])
        
        return node_types
    
    @classmethod
    def _has_video_upscale_pattern(cls, node_types: Set[str], workflow: Dict[str, Any]) -> bool:
        """Проверяет паттерн Video Upscale"""
        # Есть узлы загрузки видео И узлы апскейла И узлы сохранения видео
        has_video_input = bool(node_types & cls.VIDEO_INPUT_NODES)
        has_upscale = bool(node_types & cls.UPSCALE_NODES)
        has_video_output = bool(node_types & cls.VIDEO_OUTPUT_NODES)
        
        return has_video_input and has_upscale and has_video_output
    
    @classmethod
    def _has_t2v_pattern(cls, node_types: Set[str], workflow: Dict[str, Any]) -> bool:
        """Проверяет паттерн Text to Video"""
        # Есть текстовое кодирование И видео вывод И НЕТ загрузки видео
        has_text_encode = bool(node_types & cls.TEXT_ENCODE_NODES)
        has_video_output = bool(node_types & cls.VIDEO_OUTPUT_NODES)
        has_video_input = bool(node_types & cls.VIDEO_INPUT_NODES)
        has_wan_t2v = bool(node_types & cls.WAN_SPECIFIC_NODES)
        
        return (has_text_encode and has_video_output and not has_video_input) or has_wan_t2v
    
    @classmethod
    def _has_t2i_pattern(cls, node_types: Set[str], workflow: Dict[str, Any]) -> bool:
        """Проверяет паттерн Text to Image"""
        # Есть текстовое кодирование И вывод изображения И НЕТ загрузки изображения
        has_text_encode = bool(node_types & cls.TEXT_ENCODE_NODES)
        has_image_output = bool(node_types & cls.IMAGE_OUTPUT_NODES)
        has_image_input = bool(node_types & cls.IMAGE_INPUT_NODES)
        has_video_output = bool(node_types & cls.VIDEO_OUTPUT_NODES)
        
        return has_text_encode and has_image_output and not has_image_input and not has_video_output
    
    @classmethod
    def _has_img2img_pattern(cls, node_types: Set[str], workflow: Dict[str, Any]) -> bool:
        """Проверяет паттерн Image to Image"""
        # Есть загрузка изображения И вывод изображения И НЕТ видео вывода
        has_image_input = bool(node_types & cls.IMAGE_INPUT_NODES)
        has_image_output = bool(node_types & cls.IMAGE_OUTPUT_NODES)
        has_video_output = bool(node_types & cls.VIDEO_OUTPUT_NODES)
        
        return has_image_input and has_image_output and not has_video_output


class WorkflowProcessor:
    """Обрабатывает воркфлоу и подготавливает его к выполнению"""
    
    @staticmethod
    def prepare_workflow(
        workflow: Dict[str, Any], 
        workflow_type: WorkflowType,
        prompt: Optional[str] = None,
        image_filename: Optional[str] = None,
        video_filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Подготавливает воркфлоу к выполнению, заполняя нужные параметры
        
        Args:
            workflow: Исходный JSON воркфлоу
            workflow_type: Тип воркфлоу
            prompt: Текстовый промпт (для T2V, T2I)
            image_filename: Имя файла изображения (для Img2Img, T2V с изображением)
            video_filename: Имя файла видео (для Video Upscale)
            options: Дополнительные опции
            
        Returns:
            Подготовленный воркфлоу
        """
        prepared_workflow = workflow.copy()
        
        try:
            # Обновляем промпт в текстовых узлах
            if prompt:
                WorkflowProcessor._update_text_prompts(prepared_workflow, prompt)
            
            # Обновляем файлы изображений
            if image_filename:
                WorkflowProcessor._update_image_inputs(prepared_workflow, image_filename)
            
            # Обновляем файлы видео
            if video_filename:
                WorkflowProcessor._update_video_inputs(prepared_workflow, video_filename)
            
            # Применяем опции
            if options:
                WorkflowProcessor._apply_options(prepared_workflow, options)
            
            logger.info(f"Воркфлоу подготовлен для типа {workflow_type.value}")
            return prepared_workflow
            
        except Exception as e:
            logger.error(f"Ошибка подготовки воркфлоу: {e}")
            return prepared_workflow
    
    @staticmethod
    def _update_text_prompts(workflow: Dict[str, Any], prompt: str):
        """Обновляет текстовые промпты в воркфлоу"""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") in ["CLIPTextEncode", "TextEncode"]:
                if "inputs" in node_data and "text" in node_data["inputs"]:
                    # Обновляем только положительные промпты (не negative)
                    meta_title = node_data.get("_meta", {}).get("title", "").lower()
                    if "negative" not in meta_title and "bad" not in meta_title:
                        node_data["inputs"]["text"] = prompt
                        logger.debug(f"Обновлен промпт в узле {node_id}")
    
    @staticmethod
    def _update_image_inputs(workflow: Dict[str, Any], image_filename: str):
        """Обновляет входные изображения в воркфлоу"""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") in ["LoadImage", "ImageInput"]:
                if "inputs" in node_data and "image" in node_data["inputs"]:
                    node_data["inputs"]["image"] = image_filename
                    logger.debug(f"Обновлено изображение в узле {node_id}: {image_filename}")
    
    @staticmethod
    def _update_video_inputs(workflow: Dict[str, Any], video_filename: str):
        """Обновляет входные видео в воркфлоу"""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") in ["LoadVideo", "VideoInput", "VHS_LoadVideo"]:
                if "inputs" in node_data and "video" in node_data["inputs"]:
                    node_data["inputs"]["video"] = video_filename
                    logger.debug(f"Обновлено видео в узле {node_id}: {video_filename}")
    
    @staticmethod
    def _apply_options(workflow: Dict[str, Any], options: Dict[str, Any]):
        """Применяет опции к воркфлоу"""
        seed = options.get("seed", int(time.time()))
        
        # Обновляем сиды в KSampler узлах
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and "KSampler" in node_data.get("class_type", ""):
                if "inputs" in node_data:
                    if "seed" in node_data["inputs"]:
                        node_data["inputs"]["seed"] = seed
                    if "noise_seed" in node_data["inputs"]:
                        node_data["inputs"]["noise_seed"] = seed
        
        # Обновляем другие параметры
        for option_key, option_value in options.items():
            if option_key == "seed":
                continue
                
            WorkflowProcessor._update_workflow_parameter(workflow, option_key, option_value)
    
    @staticmethod
    def _update_workflow_parameter(workflow: Dict[str, Any], param_name: str, param_value: Any):
        """Обновляет конкретный параметр в воркфлоу"""
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and "inputs" in node_data:
                if param_name in node_data["inputs"]:
                    node_data["inputs"][param_name] = param_value
                    logger.debug(f"Обновлен параметр {param_name} в узле {node_id}: {param_value}")