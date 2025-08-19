"""
CineLuck - Professional Raspberry Pi Video Camera
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "CineLuck Development Team"
__description__ = "Professional Raspberry Pi 5 video camera using Picamera2"

from .app import CineLuckApp
from .config.manager import ConfigManager
from .state.machine import StateMachine

__all__ = [
    "CineLuckApp",
    "ConfigManager", 
    "StateMachine",
    "__version__",
]