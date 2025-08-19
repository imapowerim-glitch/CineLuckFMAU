#!/usr/bin/env python3
"""
CineLuck - Professional Raspberry Pi Video Camera
Main application entry point
"""

import sys
import signal
import logging
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from .app import CineLuckApp
from .config.manager import ConfigManager
from .utils.logging_setup import setup_logging


def signal_handler(signum, frame):
    """Handle system signals gracefully"""
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    QApplication.quit()


def main():
    """Main application entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize configuration
    config_manager = ConfigManager()
    config_manager.ensure_config_dir()
    
    # Set up logging
    setup_logging(config_manager.get_log_file())
    logger = logging.getLogger(__name__)
    
    logger.info("Starting CineLuck Professional Video Camera")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("CineLuck")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CineLuck")
    
    # Configure for touch interface
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    try:
        # Create and run main application
        main_app = CineLuckApp(config_manager)
        main_app.show()
        
        logger.info("CineLuck application started successfully")
        
        # Run the application
        exit_code = app.exec()
        
        logger.info(f"CineLuck application exiting with code {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error starting CineLuck: {e}", exc_info=True)
        return 1
    finally:
        logger.info("CineLuck shutdown complete")


if __name__ == "__main__":
    sys.exit(main())