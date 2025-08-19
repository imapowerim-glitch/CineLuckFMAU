"""
Main Application Class for CineLuck
Coordinates all components and manages the application lifecycle
"""

import logging
import sys
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor

from .config.manager import ConfigManager
from .state.machine import StateMachine, CameraState, SafeStopManager
from .camera.manager import CameraManager
from .camera.encoder import EncoderManager
from .audio.manager import AudioManager
from .utils.system_info import SystemInfo
from .utils.file_utils import FileUtils
from .ui.main_window import MainWindow


class CineLuckApp(QMainWindow):
    """Main CineLuck application class"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.config_manager = config_manager
        self.state_machine = StateMachine()
        self.safe_stop_manager = SafeStopManager(self.state_machine)
        
        # Managers
        self.camera_manager = CameraManager(config_manager)
        self.encoder_manager = EncoderManager(config_manager)
        self.audio_manager = AudioManager(config_manager)
        self.system_info = SystemInfo()
        self.file_utils = FileUtils(config_manager.get_recording_dir())
        
        # UI
        self.main_window = None
        
        # Monitoring timers
        self.system_monitor_timer = QTimer()
        self.system_monitor_timer.timeout.connect(self._update_system_status)
        self.system_monitor_timer.setInterval(2000)  # Update every 2 seconds
        
        self.logger.info("CineLuck application initialized")
        
        # Initialize application
        self._setup_application()
        self._connect_signals()
        self._startup_checks()
    
    def _setup_application(self):
        """Set up the main application"""
        try:
            # Configure for touch interface
            self.setWindowTitle("CineLuck Professional Video Camera")
            
            # Set application styling for touch interface
            self._setup_touch_styling()
            
            # Create main window
            self.main_window = MainWindow(
                self.config_manager,
                self.state_machine,
                self.camera_manager,
                self.encoder_manager,
                self.audio_manager,
                self.system_info,
                self.file_utils,
                self.safe_stop_manager
            )
            
            # Set main window as central widget
            self.setCentralWidget(self.main_window)
            
            # Configure window for full screen on 800x640 display
            screen_size = QApplication.primaryScreen().size()
            if screen_size.width() == 800 and screen_size.height() == 640:
                self.showFullScreen()
            else:
                self.resize(800, 640)
                self.show()
            
            self.logger.info("Application setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup application: {e}")
            raise
    
    def _setup_touch_styling(self):
        """Configure application for touch interface"""
        try:
            app = QApplication.instance()
            
            # Set up font scaling for touch interface
            ui_scale = self.config_manager.get("ui_scale", 1.0)
            base_font_size = int(12 * ui_scale)
            
            font = QFont()
            font.setPointSize(base_font_size)
            app.setFont(font)
            
            # Set up dark theme for professional video interface
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            
            app.setPalette(dark_palette)
            
            # Set stylesheet for touch-friendly controls
            app.setStyleSheet("""
                QPushButton {
                    min-height: 40px;
                    min-width: 60px;
                    border: 2px solid #555;
                    border-radius: 6px;
                    padding: 5px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #666;
                    border-color: #777;
                }
                QPushButton:checked {
                    background-color: #2a82da;
                    border-color: #3a92ea;
                }
                QSlider::groove:horizontal {
                    height: 6px;
                    border-radius: 3px;
                    background: #444;
                }
                QSlider::handle:horizontal {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    background: #2a82da;
                    margin: -7px 0;
                }
                QComboBox {
                    min-height: 35px;
                    padding: 5px;
                    border: 2px solid #555;
                    border-radius: 4px;
                }
                QSpinBox, QDoubleSpinBox {
                    min-height: 35px;
                    padding: 5px;
                    border: 2px solid #555;
                    border-radius: 4px;
                }
            """)
            
        except Exception as e:
            self.logger.error(f"Failed to setup touch styling: {e}")
    
    def _connect_signals(self):
        """Connect signals between components"""
        try:
            # State machine signals
            self.state_machine.state_changed.connect(self._handle_state_change)
            self.state_machine.error_occurred.connect(self._handle_error)
            
            # Camera signals
            self.camera_manager.camera_error.connect(self._handle_camera_error)
            self.camera_manager.recording_started.connect(self._handle_recording_started)
            self.camera_manager.recording_stopped.connect(self._handle_recording_stopped)
            
            # Audio signals
            self.audio_manager.audio_error.connect(self._handle_audio_error)
            
            # Safe stop signals
            self.safe_stop_manager.stop_completed.connect(self._handle_safe_stop_completed)
            
            self.logger.debug("Signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect signals: {e}")
    
    def _startup_checks(self):
        """Perform startup system checks"""
        try:
            self.logger.info("Performing startup checks...")
            
            # Check if running on Raspberry Pi
            if self.system_info.is_raspberry_pi():
                pi_model = self.system_info.get_pi_model()
                self.logger.info(f"Running on {pi_model}")
            else:
                self.logger.warning("Not running on Raspberry Pi - some features may not work")
            
            # Check camera availability
            cameras = self.system_info.check_camera_devices()
            if cameras:
                self.logger.info(f"Found cameras: {cameras}")
            else:
                self.logger.warning("No cameras detected")
            
            # Check audio devices
            audio_devices = self.system_info.check_audio_devices()
            input_count = len(audio_devices.get('input', []))
            self.logger.info(f"Found {input_count} audio input devices")
            
            # Check storage
            recording_dir = self.config_manager.get_recording_dir()
            recording_dir.mkdir(parents=True, exist_ok=True)
            free_space = self.file_utils.get_free_space_gb()
            self.logger.info(f"Recording directory: {recording_dir}")
            self.logger.info(f"Free space: {free_space:.1f} GB")
            
            # Start system monitoring
            self.system_monitor_timer.start()
            
            # Initialize camera
            if not self.camera_manager.initialize_camera():
                self.logger.warning("Camera initialization failed")
            
            # Transition to preview state
            self.state_machine.transition_to(CameraState.PREVIEW)
            
            self.logger.info("Startup checks completed")
            
        except Exception as e:
            self.logger.error(f"Startup checks failed: {e}")
            self.state_machine.transition_to(CameraState.ERROR)
    
    def _update_system_status(self):
        """Update system status (called by timer)"""
        try:
            # Update temperature
            temp = self.system_info.get_cpu_temperature()
            if temp and temp > self.config_manager.get("thermal_throttle_temp", 70):
                self.logger.warning(f"High CPU temperature: {temp:.1f}°C")
            
            # Update storage
            free_space = self.file_utils.get_free_space_gb()
            min_space = self.config_manager.get("min_free_space_gb", 2.0)
            if free_space < min_space:
                self.logger.warning(f"Low storage space: {free_space:.1f} GB")
                if self.state_machine.is_state(CameraState.RECORDING):
                    self.logger.error("Stopping recording due to low storage")
                    self.safe_stop_manager.safe_stop_recording(
                        self.camera_manager, self.encoder_manager
                    )
            
        except Exception as e:
            self.logger.debug(f"System status update error: {e}")
    
    def _handle_state_change(self, new_state: CameraState, old_state: CameraState):
        """Handle state machine state changes"""
        self.logger.info(f"State changed: {old_state.value} -> {new_state.value}")
        
        try:
            if new_state == CameraState.PREVIEW:
                if not self.camera_manager.is_preview_active:
                    self.camera_manager.start_preview()
            
            elif new_state == CameraState.RECORDING:
                # Recording start is handled by the UI
                pass
            
            elif new_state == CameraState.IDLE:
                self.camera_manager.stop_preview()
            
            elif new_state == CameraState.ERROR:
                self.camera_manager.stop_recording()
                self.audio_manager.stop_recording()
            
        except Exception as e:
            self.logger.error(f"Error handling state change: {e}")
    
    def _handle_error(self, error_message: str):
        """Handle error from state machine"""
        self.logger.error(f"State machine error: {error_message}")
        
        # Show error to user through UI
        if self.main_window:
            self.main_window.show_error_message(error_message)
    
    def _handle_camera_error(self, error_message: str):
        """Handle camera error"""
        self.logger.error(f"Camera error: {error_message}")
        self.state_machine.transition_to(CameraState.ERROR)
    
    def _handle_audio_error(self, error_message: str):
        """Handle audio error"""
        self.logger.warning(f"Audio error: {error_message}")
        # Audio errors are not fatal, just log them
    
    def _handle_recording_started(self, filename: str):
        """Handle recording started"""
        self.logger.info(f"Recording started: {filename}")
        self.audio_manager.start_recording(filename)
    
    def _handle_recording_stopped(self):
        """Handle recording stopped"""
        self.logger.info("Recording stopped")
        self.audio_manager.stop_recording()
    
    def _handle_safe_stop_completed(self, success: bool):
        """Handle safe stop completion"""
        if success:
            self.logger.info("Safe stop completed successfully")
        else:
            self.logger.error("Safe stop completed with errors")
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.logger.info("Application closing...")
        
        try:
            # Stop all operations
            self.system_monitor_timer.stop()
            
            # Safe stop if recording
            if self.state_machine.is_state(CameraState.RECORDING):
                self.safe_stop_manager.safe_stop_recording(
                    self.camera_manager, self.encoder_manager
                )
                # Wait briefly for stop to complete
                QApplication.processEvents()
            
            # Shutdown components
            self.camera_manager.close_camera()
            self.audio_manager.shutdown()
            self.state_machine.shutdown()
            
            # Cleanup incomplete files
            self.file_utils.cleanup_incomplete_files()
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        event.accept()