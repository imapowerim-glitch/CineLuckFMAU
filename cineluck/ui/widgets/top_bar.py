"""
Top Bar Widget
Displays status information: FPS, shutter, gain/ISO, WB, free space, temperature
"""

import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ...state.machine import CameraState


class TopBar(QWidget):
    """Top status bar showing camera and system information"""
    
    def __init__(self, config_manager, system_info, file_utils, camera_manager):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.system_info = system_info
        self.file_utils = file_utils
        self.camera_manager = camera_manager
        
        # Status labels
        self.fps_label = None
        self.shutter_label = None
        self.iso_label = None
        self.wb_label = None
        self.storage_label = None
        self.temp_label = None
        self.time_label = None
        self.status_label = None
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.setInterval(1000)  # Update every second
        
        self._setup_ui()
        self.update_timer.start()
        
        self.logger.debug("Top bar initialized")
    
    def _setup_ui(self):
        """Set up the top bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)
        
        # Set height and styling
        self.setFixedHeight(40)
        self.setStyleSheet("""
            TopBar {
                background-color: #2a2a2a;
                border-bottom: 1px solid #444;
            }
            QLabel {
                color: #fff;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet("color: #ff6b6b; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Frame rate
        self.fps_label = QLabel("25 fps")
        layout.addWidget(self.fps_label)
        
        # Shutter speed
        self.shutter_label = QLabel("1/25s")
        layout.addWidget(self.shutter_label)
        
        # ISO/Gain
        self.iso_label = QLabel("ISO 100")
        layout.addWidget(self.iso_label)
        
        # White balance
        self.wb_label = QLabel("AUTO")
        layout.addWidget(self.wb_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Storage space
        self.storage_label = QLabel("-- GB")
        layout.addWidget(self.storage_label)
        
        # Temperature
        self.temp_label = QLabel("--°C")
        layout.addWidget(self.temp_label)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Current time
        self.time_label = QLabel("--:--:--")
        layout.addWidget(self.time_label)
        
        # Add stretch to push elements
        layout.addStretch()
    
    def _create_separator(self):
        """Create a visual separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #666;")
        return separator
    
    def _update_status(self):
        """Update status information"""
        try:
            # Update camera info
            camera_stats = self.camera_manager.get_camera_stats()
            
            # Frame rate
            fps = camera_stats.get('fps', 25)
            self.fps_label.setText(f"{fps} fps")
            
            # Shutter speed
            exposure_time = camera_stats.get('exposure_time', 0)
            if exposure_time > 0:
                # Convert microseconds to fraction
                shutter_speed = 1000000 / exposure_time
                if shutter_speed >= 1:
                    self.shutter_label.setText(f"1/{int(shutter_speed)}s")
                else:
                    self.shutter_label.setText(f"{exposure_time/1000:.1f}ms")
            else:
                self.shutter_label.setText("AUTO")
            
            # ISO/Gain
            gain = camera_stats.get('analogue_gain', 0)
            if gain > 0:
                iso_value = int(gain * 100)
                self.iso_label.setText(f"ISO {iso_value}")
            else:
                self.iso_label.setText("AUTO")
            
            # White balance
            if self.config_manager.get("auto_white_balance", True):
                self.wb_label.setText("AUTO")
            else:
                cct = self.config_manager.get("color_temperature", 3200)
                self.wb_label.setText(f"{cct}K")
            
            # Storage space
            free_space = self.file_utils.get_free_space_gb()
            if free_space >= 10:
                color = "#4CAF50"  # Green
            elif free_space >= 2:
                color = "#FF9800"  # Orange
            else:
                color = "#F44336"  # Red
            
            self.storage_label.setText(f"{free_space:.1f} GB")
            self.storage_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # Temperature
            temp = self.system_info.get_cpu_temperature()
            if temp:
                if temp < 60:
                    color = "#4CAF50"  # Green
                elif temp < 70:
                    color = "#FF9800"  # Orange
                else:
                    color = "#F44336"  # Red
                
                self.temp_label.setText(f"{temp:.0f}°C")
                self.temp_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                self.temp_label.setText("--°C")
            
            # Current time
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.setText(current_time)
            
        except Exception as e:
            self.logger.debug(f"Status update error: {e}")
    
    def handle_state_change(self, new_state: CameraState, old_state: CameraState):
        """Handle state changes"""
        try:
            # Update status indicator
            status_colors = {
                CameraState.IDLE: ("#888", "IDLE"),
                CameraState.PREVIEW: ("#4CAF50", "READY"), 
                CameraState.RECORDING: ("#F44336", "REC"),
                CameraState.STOPPING: ("#FF9800", "STOP"),
                CameraState.ERROR: ("#F44336", "ERROR")
            }
            
            color, text = status_colors.get(new_state, ("#888", "UNKNOWN"))
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            
            # Add blinking effect for recording
            if new_state == CameraState.RECORDING:
                self._start_recording_blink()
            else:
                self._stop_recording_blink()
                
        except Exception as e:
            self.logger.error(f"Error handling state change in top bar: {e}")
    
    def _start_recording_blink(self):
        """Start blinking effect for recording indicator"""
        try:
            self.blink_timer = QTimer()
            self.blink_state = False
            
            def blink():
                self.blink_state = not self.blink_state
                if self.blink_state:
                    self.status_label.setStyleSheet("color: #F44336; font-size: 14px; font-weight: bold;")
                else:
                    self.status_label.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
            
            self.blink_timer.timeout.connect(blink)
            self.blink_timer.start(500)  # Blink every 500ms
            
        except Exception as e:
            self.logger.error(f"Failed to start recording blink: {e}")
    
    def _stop_recording_blink(self):
        """Stop blinking effect"""
        try:
            if hasattr(self, 'blink_timer'):
                self.blink_timer.stop()
                delattr(self, 'blink_timer')
        except Exception as e:
            self.logger.debug(f"Error stopping blink: {e}")