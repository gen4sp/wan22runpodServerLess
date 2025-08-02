# -*- coding: utf-8 -*-
"""
Простой тестовый воркфлоу для демонстрации системы
"""
from typing import Dict, Any, Optional
from .base import WorkflowBase


class SimpleTestWorkflow(WorkflowBase):
    """Простой тестовый воркфлоу для отладки"""
    
    def __init__(self):
        super().__init__()
        self.name = "Simple Test"
        self.version = "1.0"
    
    def get_default_options(self) -> Dict[str, Any]:
        """Опции по умолчанию для тестового воркфлоу"""
        return {
            'width': 512,
            'height': 512,
            'steps': 4,
            'cfg': 7.0,
            'sampler_name': 'euler',
            'scheduler': 'normal'
        }
    
    def supports_t2v(self) -> bool:
        """Тестовый воркфлоу не поддерживает T2V"""
        return False
    
    def supports_i2v(self) -> bool:
        """Тестовый воркфлоу поддерживает только I2I генерацию"""
        return True
    
    def create_workflow(self, prompt: str, image_filename: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Создает простой тестовый воркфлоу"""
        validated_options = self.validate_options(options or {})
        seed = validated_options.get('seed', self.generate_seed())
        
        # Простой воркфлоу для тестирования
        workflow = {
            "1": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "2": {
                "inputs": {
                    "text": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode", 
                "_meta": {"title": "CLIP Text Encode (Negative)"}
            },
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": validated_options['steps'],
                    "cfg": validated_options['cfg'],
                    "sampler_name": validated_options['sampler_name'],
                    "scheduler": validated_options['scheduler'],
                    "denoise": 0.75,
                    "model": ["4", 0],
                    "positive": ["1", 0],
                    "negative": ["2", 0],
                    "latent_image": ["7", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "image": image_filename
                },
                "class_type": "LoadImage",
                "_meta": {"title": "Load Image"}
            },
            "6": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "7": {
                "inputs": {
                    "pixels": ["8", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "VAE Encode"}
            },
            "8": {
                "inputs": {
                    "width": validated_options['width'],
                    "height": validated_options['height'],
                    "interpolation": "lanczos",
                    "method": "stretch",
                    "condition": "always",
                    "multiple_of": 0,
                    "image": ["5", 0]
                },
                "class_type": "ImageResize+",
                "_meta": {"title": "🔧 Image Resize"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "SimpleTest",
                    "images": ["6", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
        }
        
        return workflow