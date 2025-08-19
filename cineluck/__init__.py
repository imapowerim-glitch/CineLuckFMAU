"""
CineLuck - Professional Raspberry Pi Video Camera
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "CineLuck Development Team"
__description__ = "Professional Raspberry Pi 5 video camera using Picamera2"

# Import core components that don't require GUI
def get_config_manager():
    """Get ConfigManager instance"""
    from .config.manager import ConfigManager
    return ConfigManager

def get_state_machine():
    """Get StateMachine instance"""
    from .state.machine import StateMachine
    return StateMachine

# Only import GUI components when explicitly requested
def get_app():
    """Get CineLuckApp instance (requires GUI dependencies)"""
    from .app import CineLuckApp
    return CineLuckApp

__all__ = [
    "get_config_manager",
    "get_state_machine", 
    "get_app",
    "__version__",
]