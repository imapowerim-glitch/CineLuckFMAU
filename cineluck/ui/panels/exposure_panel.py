"""
Exposure Panel
Left slide-in panel for exposure controls
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QSpinBox, QCheckBox, QComboBox, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...state.machine import CameraState


class ExposurePanel(QWidget):
    """Left panel for exposure and camera controls"""
    
    close_requested = pyqtSignal()
    
    def __init__(self, config_manager, camera_manager, state_machine):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.camera_manager = camera_manager
        self.state_machine = state_machine
        
        # Control widgets
        self.auto_exposure_check = None
        self.shutter_slider = None
        self.iso_slider = None
        self.metering_combo = None
        self.flicker_combo = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        
        self.logger.debug("Exposure panel initialized")
    
    def _setup_ui(self):
        """Set up the exposure panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Panel styling
        self.setStyleSheet("""
            ExposurePanel {
                background-color: #333;
                border-right: 1px solid #555;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #666;
                border: 1px solid #888;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #777;
            }
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("EXPOSURE"))
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Auto Exposure
        auto_group = QGroupBox("Auto Exposure")
        auto_layout = QVBoxLayout(auto_group)
        
        self.auto_exposure_check = QCheckBox("Enable Auto Exposure")
        self.auto_exposure_check.setChecked(True)
        self.auto_exposure_check.toggled.connect(self._handle_auto_exposure_toggle)
        auto_layout.addWidget(self.auto_exposure_check)
        
        # Metering mode
        metering_layout = QHBoxLayout()
        metering_layout.addWidget(QLabel("Metering:"))
        self.metering_combo = QComboBox()
        self.metering_combo.addItems(["Average", "Center", "Spot"])
        self.metering_combo.currentTextChanged.connect(self._handle_metering_change)
        metering_layout.addWidget(self.metering_combo)
        auto_layout.addLayout(metering_layout)
        
        layout.addWidget(auto_group)
        
        # Manual Exposure
        manual_group = QGroupBox("Manual Controls")
        manual_layout = QVBoxLayout(manual_group)
        
        # Shutter Speed
        shutter_layout = QVBoxLayout()
        shutter_layout.addWidget(QLabel("Shutter Speed (µs)"))
        
        self.shutter_slider = QSlider(Qt.Orientation.Horizontal)
        self.shutter_slider.setMinimum(100)      # 100 µs
        self.shutter_slider.setMaximum(1000000)  # 1 second
        self.shutter_slider.setValue(40000)      # 40ms default
        self.shutter_slider.valueChanged.connect(self._handle_shutter_change)
        shutter_layout.addWidget(self.shutter_slider)
        
        self.shutter_label = QLabel("40000 µs (1/25s)")
        self.shutter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shutter_layout.addWidget(self.shutter_label)
        
        manual_layout.addLayout(shutter_layout)
        
        # ISO/Gain
        iso_layout = QVBoxLayout()
        iso_layout.addWidget(QLabel("ISO"))
        
        self.iso_slider = QSlider(Qt.Orientation.Horizontal)
        self.iso_slider.setMinimum(100)   # ISO 100
        self.iso_slider.setMaximum(3200)  # ISO 3200
        self.iso_slider.setValue(100)     # ISO 100 default
        self.iso_slider.valueChanged.connect(self._handle_iso_change)
        iso_layout.addWidget(self.iso_slider)
        
        self.iso_label = QLabel("ISO 100")
        self.iso_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        iso_layout.addWidget(self.iso_label)
        
        manual_layout.addLayout(iso_layout)
        
        layout.addWidget(manual_group)
        
        # Anti-Flicker
        flicker_group = QGroupBox("Anti-Flicker")
        flicker_layout = QVBoxLayout(flicker_group)
        
        flicker_select_layout = QHBoxLayout()
        flicker_select_layout.addWidget(QLabel("Frequency:"))
        self.flicker_combo = QComboBox()
        self.flicker_combo.addItems(["Off", "50 Hz", "60 Hz"])
        self.flicker_combo.currentTextChanged.connect(self._handle_flicker_change)
        flicker_select_layout.addWidget(self.flicker_combo)
        flicker_layout.addLayout(flicker_select_layout)
        
        layout.addWidget(flicker_group)
        
        # Add stretch to push controls to top
        layout.addStretch()
        
        # Enable/disable controls based on auto exposure
        self._update_manual_controls_state()
    
    def _connect_signals(self):
        """Connect camera signals"""
        try:
            self.camera_manager.camera_stats_updated.connect(self._update_camera_stats)
            
        except Exception as e:
            self.logger.error(f"Failed to connect exposure panel signals: {e}")
    
    def _load_settings(self):
        """Load settings from config"""
        try:
            # Load auto exposure setting
            auto_exposure = self.config_manager.get("auto_exposure", True)
            self.auto_exposure_check.setChecked(auto_exposure)
            
            # Load metering mode
            metering_mode = self.config_manager.get("metering_mode", "average")
            metering_index = {"average": 0, "center": 1, "spot": 2}.get(metering_mode, 0)
            self.metering_combo.setCurrentIndex(metering_index)
            
            # Load manual settings
            shutter_us = self.config_manager.get("shutter_speed_us", 40000)
            self.shutter_slider.setValue(shutter_us)
            self._update_shutter_label(shutter_us)
            
            iso_value = self.config_manager.get("iso_value", 100)
            self.iso_slider.setValue(iso_value)
            self._update_iso_label(iso_value)
            
        except Exception as e:
            self.logger.error(f"Failed to load exposure settings: {e}")
    
    def _handle_auto_exposure_toggle(self, checked):
        """Handle auto exposure toggle"""
        try:
            self.config_manager.set("auto_exposure", checked)
            self.camera_manager.set_exposure_settings(checked)
            self._update_manual_controls_state()
            
            self.logger.debug(f"Auto exposure: {checked}")
            
        except Exception as e:
            self.logger.error(f"Failed to toggle auto exposure: {e}")
    
    def _handle_metering_change(self, mode_text):
        """Handle metering mode change"""
        try:
            mode_map = {"Average": "average", "Center": "center", "Spot": "spot"}
            mode = mode_map.get(mode_text, "average")
            
            self.config_manager.set("metering_mode", mode)
            # Camera will pick up the change on next settings application
            
            self.logger.debug(f"Metering mode: {mode}")
            
        except Exception as e:
            self.logger.error(f"Failed to change metering mode: {e}")
    
    def _handle_shutter_change(self, value):
        """Handle shutter speed change"""
        try:
            self.config_manager.set("shutter_speed_us", value)
            self._update_shutter_label(value)
            
            # Apply to camera if in manual mode
            if not self.auto_exposure_check.isChecked():
                self.camera_manager.set_exposure_settings(
                    False, shutter_us=value, iso=self.iso_slider.value()
                )
            
        except Exception as e:
            self.logger.error(f"Failed to change shutter speed: {e}")
    
    def _handle_iso_change(self, value):
        """Handle ISO change"""
        try:
            self.config_manager.set("iso_value", value)
            self._update_iso_label(value)
            
            # Apply to camera if in manual mode
            if not self.auto_exposure_check.isChecked():
                self.camera_manager.set_exposure_settings(
                    False, shutter_us=self.shutter_slider.value(), iso=value
                )
            
        except Exception as e:
            self.logger.error(f"Failed to change ISO: {e}")
    
    def _handle_flicker_change(self, flicker_text):
        """Handle anti-flicker change"""
        try:
            flicker_map = {"Off": 0, "50 Hz": 50, "60 Hz": 60}
            flicker_freq = flicker_map.get(flicker_text, 0)
            
            self.config_manager.set("anti_flicker_freq", flicker_freq)
            self.logger.debug(f"Anti-flicker: {flicker_freq} Hz")
            
        except Exception as e:
            self.logger.error(f"Failed to change anti-flicker: {e}")
    
    def _update_shutter_label(self, shutter_us):
        """Update shutter speed label"""
        try:
            # Convert to fraction representation
            if shutter_us >= 1000000:  # 1 second or more
                seconds = shutter_us / 1000000
                self.shutter_label.setText(f"{shutter_us} µs ({seconds:.1f}s)")
            else:
                # Calculate fraction
                shutter_speed = 1000000 / shutter_us
                if shutter_speed >= 1:
                    self.shutter_label.setText(f"{shutter_us} µs (1/{int(shutter_speed)}s)")
                else:
                    ms = shutter_us / 1000
                    self.shutter_label.setText(f"{shutter_us} µs ({ms:.1f}ms)")
                    
        except Exception as e:
            self.logger.debug(f"Shutter label update error: {e}")
    
    def _update_iso_label(self, iso_value):
        """Update ISO label"""
        self.iso_label.setText(f"ISO {iso_value}")
    
    def _update_manual_controls_state(self):
        """Enable/disable manual controls based on auto exposure"""
        manual_enabled = not self.auto_exposure_check.isChecked()
        
        self.shutter_slider.setEnabled(manual_enabled)
        self.iso_slider.setEnabled(manual_enabled)
        self.shutter_label.setEnabled(manual_enabled)
        self.iso_label.setEnabled(manual_enabled)
    
    def _update_camera_stats(self, stats):
        """Update display with current camera statistics"""
        try:
            # Update labels with current camera values when in auto mode
            if self.auto_exposure_check.isChecked():
                exposure_time = stats.get('exposure_time', 0)
                if exposure_time > 0:
                    self._update_shutter_label(exposure_time)
                
                gain = stats.get('analogue_gain', 0)
                if gain > 0:
                    iso_equivalent = int(gain * 100)
                    self.iso_label.setText(f"ISO {iso_equivalent} (auto)")
                    
        except Exception as e:
            self.logger.debug(f"Camera stats update error: {e}")