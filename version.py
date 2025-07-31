#!/usr/bin/env python3
"""Управление версиями для WAN 2.2 RunPod Worker."""

__version__ = "1.0.0"
__version_info__ = tuple(map(int, __version__.split(".")))

def get_version():
    """Возвращает текущую версию."""
    return __version__

def get_version_info():
    """Возвращает информацию о версии как кортеж (major, minor, patch)."""
    return __version_info__