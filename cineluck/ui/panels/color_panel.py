"""
Color Panel
Right slide-in panel for white balance and color controls
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QSpinBox, QCheckBox, QComboBox, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...state.machine import CameraState


class ColorPanel(QWidget):
    """Right panel for white balance and color controls"""
    
    close_requested = pyqtSignal()
    
    def __init__(self, config_manager, camera_manager, state_machine):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.camera_manager = camera_manager
        self.state_machine = state_machine
        
        # Control widgets
        self.auto_wb_check = None
        self.wb_preset_combo = None
        self.cct_slider = None
        self.tint_slider = None
        self.contrast_slider = None
        self.saturation_slider = None
        self.sharpness_slider = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        
        self.logger.debug("Color panel initialized")
    
    def _setup_ui(self):
        """Set up the color panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Panel styling
        self.setStyleSheet("""
            ColorPanel {
                background-color: #333;
                border-left: 1px solid #555;
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
        header_layout.addWidget(QLabel("WB & COLOR"))
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # White Balance
        wb_group = QGroupBox("White Balance")
        wb_layout = QVBoxLayout(wb_group)
        
        self.auto_wb_check = QCheckBox("Auto White Balance")
        self.auto_wb_check.setChecked(True)
        self.auto_wb_check.toggled.connect(self._handle_auto_wb_toggle)
        wb_layout.addWidget(self.auto_wb_check)
        
        # WB Presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.wb_preset_combo = QComboBox()
        self.wb_preset_combo.addItems(["Auto", "Daylight", "Cloudy", "Tungsten", "Fluorescent", "Flash"])
        self.wb_preset_combo.currentTextChanged.connect(self._handle_wb_preset_change)
        preset_layout.addWidget(self.wb_preset_combo)
        wb_layout.addLayout(preset_layout)
        
        layout.addWidget(wb_group)
        
        # Manual Color Temperature
        manual_wb_group = QGroupBox("Manual White Balance")
        manual_wb_layout = QVBoxLayout(manual_wb_group)
        
        # Color Temperature
        cct_layout = QVBoxLayout()
        cct_layout.addWidget(QLabel("Color Temperature (K)"))
        
        self.cct_slider = QSlider(Qt.Orientation.Horizontal)
        self.cct_slider.setMinimum(2000)   # 2000K
        self.cct_slider.setMaximum(8000)   # 8000K
        self.cct_slider.setValue(3200)     # 3200K default
        self.cct_slider.valueChanged.connect(self._handle_cct_change)
        cct_layout.addWidget(self.cct_slider)
        
        self.cct_label = QLabel("3200K")
        self.cct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cct_layout.addWidget(self.cct_label)
        
        manual_wb_layout.addLayout(cct_layout)
        
        # Tint
        tint_layout = QVBoxLayout()
        tint_layout.addWidget(QLabel("Tint"))
        
        self.tint_slider = QSlider(Qt.Orientation.Horizontal)
        self.tint_slider.setMinimum(-100)  # Magenta
        self.tint_slider.setMaximum(100)   # Green
        self.tint_slider.setValue(0)       # Neutral
        self.tint_slider.valueChanged.connect(self._handle_tint_change)
        tint_layout.addWidget(self.tint_slider)
        
        self.tint_label = QLabel("0 (Neutral)")
        self.tint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tint_layout.addWidget(self.tint_label)
        
        manual_wb_layout.addLayout(tint_layout)
        
        layout.addWidget(manual_wb_group)
        
        # Image Processing
        processing_group = QGroupBox("Image Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        # Contrast
        contrast_layout = QVBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast"))
        
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setMinimum(-100)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self._handle_contrast_change)
        contrast_layout.addWidget(self.contrast_slider)
        
        self.contrast_label = QLabel("0")
        self.contrast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contrast_layout.addWidget(self.contrast_label)
        
        processing_layout.addLayout(contrast_layout)
        
        # Saturation
        saturation_layout = QVBoxLayout()
        saturation_layout.addWidget(QLabel("Saturation"))
        
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setMinimum(-100)
        self.saturation_slider.setMaximum(100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(self._handle_saturation_change)
        saturation_layout.addWidget(self.saturation_slider)
        
        self.saturation_label = QLabel("0")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        saturation_layout.addWidget(self.saturation_label)
        
        processing_layout.addLayout(saturation_layout)
        
        # Sharpness
        sharpness_layout = QVBoxLayout()
        sharpness_layout.addWidget(QLabel("Sharpness"))
        
        self.sharpness_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharpness_slider.setMinimum(-100)
        self.sharpness_slider.setMaximum(100)
        self.sharpness_slider.setValue(0)
        self.sharpness_slider.valueChanged.connect(self._handle_sharpness_change)
        sharpness_layout.addWidget(self.sharpness_slider)
        
        self.sharpness_label = QLabel("0")
        self.sharpness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sharpness_layout.addWidget(self.sharpness_label)
        
        processing_layout.addLayout(sharpness_layout)
        
        layout.addWidget(processing_group)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:pressed {
                background-color: #777;
            }
        """)
        layout.addWidget(reset_btn)
        
        # Add stretch to push controls to top
        layout.addStretch()
        
        # Enable/disable controls based on auto WB
        self._update_manual_wb_controls_state()
    
    def _connect_signals(self):
        """Connect camera signals"""
        try:
            # Camera signals would be connected here if needed
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to connect color panel signals: {e}")
    
    def _load_settings(self):
        """Load settings from config"""
        try:
            # Load auto white balance setting
            auto_wb = self.config_manager.get("auto_white_balance", True)
            self.auto_wb_check.setChecked(auto_wb)
            
            # Load color temperature
            cct = self.config_manager.get("color_temperature", 3200)
            self.cct_slider.setValue(cct)
            self._update_cct_label(cct)
            
            # Load tint
            tint = self.config_manager.get("tint", 0)
            self.tint_slider.setValue(tint)
            self._update_tint_label(tint)
            
            # Load image processing settings
            contrast = self.config_manager.get("contrast", 0)
            self.contrast_slider.setValue(contrast)
            self._update_contrast_label(contrast)
            
            saturation = self.config_manager.get("saturation", 0)
            self.saturation_slider.setValue(saturation)
            self._update_saturation_label(saturation)
            
            sharpness = self.config_manager.get("sharpness", 0)
            self.sharpness_slider.setValue(sharpness)
            self._update_sharpness_label(sharpness)
            
        except Exception as e:
            self.logger.error(f"Failed to load color settings: {e}")
    
    def _handle_auto_wb_toggle(self, checked):
        """Handle auto white balance toggle"""
        try:
            self.config_manager.set("auto_white_balance", checked)
            self.camera_manager.set_white_balance(checked)
            self._update_manual_wb_controls_state()
            
            self.logger.debug(f"Auto white balance: {checked}")
            
        except Exception as e:
            self.logger.error(f"Failed to toggle auto white balance: {e}")
    
    def _handle_wb_preset_change(self, preset_text):
        """Handle white balance preset change"""
        try:
            # Map preset to color temperature values
            preset_map = {
                "Auto": (None, True),
                "Daylight": (5600, False),
                "Cloudy": (6500, False), 
                "Tungsten": (3200, False),
                "Fluorescent": (4000, False),
                "Flash": (5500, False)
            }
            
            cct, auto_mode = preset_map.get(preset_text, (None, True))
            
            if auto_mode:
                self.auto_wb_check.setChecked(True)
            else:
                self.auto_wb_check.setChecked(False)
                if cct:
                    self.cct_slider.setValue(cct)
                    self._handle_cct_change(cct)
            
            self.logger.debug(f"WB preset: {preset_text}")
            
        except Exception as e:
            self.logger.error(f"Failed to change WB preset: {e}")
    
    def _handle_cct_change(self, value):
        """Handle color temperature change"""
        try:
            self.config_manager.set("color_temperature", value)
            self._update_cct_label(value)
            
            # Apply to camera if in manual mode
            if not self.auto_wb_check.isChecked():
                self.camera_manager.set_white_balance(
                    False, cct=value, tint=self.tint_slider.value()
                )
            
        except Exception as e:
            self.logger.error(f"Failed to change color temperature: {e}")
    
    def _handle_tint_change(self, value):
        """Handle tint change"""
        try:
            self.config_manager.set("tint", value)
            self._update_tint_label(value)
            
            # Apply to camera if in manual mode
            if not self.auto_wb_check.isChecked():
                self.camera_manager.set_white_balance(
                    False, cct=self.cct_slider.value(), tint=value
                )
            
        except Exception as e:
            self.logger.error(f"Failed to change tint: {e}")
    
    def _handle_contrast_change(self, value):
        """Handle contrast change"""
        try:
            self.config_manager.set("contrast", value)
            self._update_contrast_label(value)
            
            # Apply to camera
            # Note: Actual implementation would depend on camera API
            self.logger.debug(f"Contrast: {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to change contrast: {e}")
    
    def _handle_saturation_change(self, value):
        """Handle saturation change"""
        try:
            self.config_manager.set("saturation", value)
            self._update_saturation_label(value)
            
            # Apply to camera
            self.logger.debug(f"Saturation: {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to change saturation: {e}")
    
    def _handle_sharpness_change(self, value):
        """Handle sharpness change"""
        try:
            self.config_manager.set("sharpness", value)
            self._update_sharpness_label(value)
            
            # Apply to camera
            self.logger.debug(f"Sharpness: {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to change sharpness: {e}")
    
    def _update_cct_label(self, cct):
        """Update color temperature label"""
        self.cct_label.setText(f"{cct}K")
    
    def _update_tint_label(self, tint):
        """Update tint label"""
        if tint == 0:
            self.tint_label.setText("0 (Neutral)")
        elif tint > 0:
            self.tint_label.setText(f"+{tint} (Green)")
        else:
            self.tint_label.setText(f"{tint} (Magenta)")
    
    def _update_contrast_label(self, contrast):
        """Update contrast label"""
        if contrast >= 0:
            self.contrast_label.setText(f"+{contrast}")
        else:
            self.contrast_label.setText(str(contrast))
    
    def _update_saturation_label(self, saturation):
        """Update saturation label"""
        if saturation >= 0:
            self.saturation_label.setText(f"+{saturation}")
        else:
            self.saturation_label.setText(str(saturation))
    
    def _update_sharpness_label(self, sharpness):
        """Update sharpness label"""
        if sharpness >= 0:
            self.sharpness_label.setText(f"+{sharpness}")
        else:
            self.sharpness_label.setText(str(sharpness))
    
    def _update_manual_wb_controls_state(self):
        """Enable/disable manual WB controls based on auto WB"""
        manual_enabled = not self.auto_wb_check.isChecked()
        
        self.cct_slider.setEnabled(manual_enabled)
        self.tint_slider.setEnabled(manual_enabled)
        self.cct_label.setEnabled(manual_enabled)
        self.tint_label.setEnabled(manual_enabled)
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            self.auto_wb_check.setChecked(True)
            self.wb_preset_combo.setCurrentText("Auto")
            self.cct_slider.setValue(3200)
            self.tint_slider.setValue(0)
            self.contrast_slider.setValue(0)
            self.saturation_slider.setValue(0)
            self.sharpness_slider.setValue(0)
            
            # Update labels
            self._update_cct_label(3200)
            self._update_tint_label(0)
            self._update_contrast_label(0)
            self._update_saturation_label(0)
            self._update_sharpness_label(0)
            
            # Save to config
            self.config_manager.set("auto_white_balance", True)
            self.config_manager.set("color_temperature", 3200)
            self.config_manager.set("tint", 0)
            self.config_manager.set("contrast", 0)
            self.config_manager.set("saturation", 0)
            self.config_manager.set("sharpness", 0)
            
            # Apply to camera
            self.camera_manager.set_white_balance(True)
            
            self.logger.info("Color settings reset to defaults")
            
        except Exception as e:
            self.logger.error(f"Failed to reset color settings: {e}")