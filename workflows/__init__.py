# -*- coding: utf-8 -*-
"""
Система воркфлоу для RunPod хендлера
"""

from .base import WorkflowBase
from .wan22 import WAN22Workflow
from .loader import (
    get_workflow,
    list_available_workflows,
    register_workflow,
    workflow_registry
)

__all__ = [
    'WorkflowBase',
    'WAN22Workflow',
    'get_workflow',
    'list_available_workflows',
    'register_workflow',
    'workflow_registry'
]