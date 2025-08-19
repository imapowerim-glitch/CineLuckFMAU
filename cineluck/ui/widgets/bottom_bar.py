"""
Bottom Bar Widget
Contains main recording controls and quick access buttons
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel, 
    QFrame, QVBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...state.machine import CameraState


class BottomBar(QWidget):
    """Bottom bar with recording controls and quick settings"""
    
    # Signals
    exposure_panel_requested = pyqtSignal()
    color_panel_requested = pyqtSignal()
    safe_stop_requested = pyqtSignal()
    recording_started = pyqtSignal()
    
    def __init__(self, config_manager, state_machine, camera_manager, 
                 encoder_manager, audio_manager, file_utils, safe_stop_manager):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.state_machine = state_machine
        self.camera_manager = camera_manager
        self.encoder_manager = encoder_manager
        self.audio_manager = audio_manager
        self.file_utils = file_utils
        self.safe_stop_manager = safe_stop_manager
        
        # UI elements
        self.record_button = None
        self.fps_combo = None
        self.codec_combo = None
        self.container_combo = None
        self.exposure_button = None
        self.wb_button = None
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.debug("Bottom bar initialized")
    
    def _setup_ui(self):
        """Set up the bottom bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Set height and styling
        self.setFixedHeight(80)
        self.setStyleSheet("""
            BottomBar {
                background-color: #2a2a2a;
                border-top: 1px solid #444;
            }
        """)
        
        # Left side - Quick exposure controls
        left_layout = QVBoxLayout()
        
        self.exposure_button = QPushButton("EXPOSURE")
        self.exposure_button.setFixedSize(100, 50)
        self.exposure_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                background-color: #444;
                border: 2px solid #666;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #555;
            }
        """)
        self.exposure_button.clicked.connect(self.exposure_panel_requested.emit)
        left_layout.addWidget(self.exposure_button)
        
        layout.addLayout(left_layout)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Frame rate selection
        fps_layout = QVBoxLayout()
        fps_label = QLabel("FPS")
        fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fps_label.setStyleSheet("color: #ccc; font-size: 11px;")
        fps_layout.addWidget(fps_label)
        
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["24", "25", "30", "50", "60"])
        self.fps_combo.setCurrentText(str(self.config_manager.get("default_frame_rate", 25)))
        self.fps_combo.setFixedSize(70, 35)
        self.fps_combo.currentTextChanged.connect(self._handle_fps_change)
        fps_layout.addWidget(self.fps_combo)
        
        layout.addLayout(fps_layout)
        
        # Codec selection
        codec_layout = QVBoxLayout()
        codec_label = QLabel("CODEC")
        codec_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        codec_label.setStyleSheet("color: #ccc; font-size: 11px;")
        codec_layout.addWidget(codec_label)
        
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264", "H.265"])
        self.codec_combo.setCurrentText("H.264")
        self.codec_combo.setFixedSize(80, 35)
        self.codec_combo.currentTextChanged.connect(self._handle_codec_change)
        codec_layout.addWidget(self.codec_combo)
        
        layout.addLayout(codec_layout)
        
        # Container selection
        container_layout = QVBoxLayout()
        container_label = QLabel("FORMAT")
        container_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_label.setStyleSheet("color: #ccc; font-size: 11px;")
        container_layout.addWidget(container_label)
        
        self.container_combo = QComboBox()
        self.container_combo.addItems(["MKV", "MP4"])
        self.container_combo.setCurrentText("MKV")
        self.container_combo.setFixedSize(70, 35)
        self.container_combo.currentTextChanged.connect(self._handle_container_change)
        container_layout.addWidget(self.container_combo)
        
        layout.addLayout(container_layout)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Center - Big record button
        self.record_button = QPushButton("⬤ REC")
        self.record_button.setFixedSize(120, 60)
        self.record_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #d32f2f;
                color: white;
                border: 3px solid #f44336;
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
                border-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #555;
                border-color: #777;
                color: #999;
            }
        """)
        self.record_button.clicked.connect(self._handle_record_button)
        layout.addWidget(self.record_button)
        
        # Separator
        layout.addWidget(self._create_separator())
        
        # Right side - Color/WB controls
        right_layout = QVBoxLayout()
        
        self.wb_button = QPushButton("WB/COLOR")
        self.wb_button.setFixedSize(100, 50)
        self.wb_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                background-color: #444;
                border: 2px solid #666;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #555;
            }
        """)
        self.wb_button.clicked.connect(self.color_panel_requested.emit)
        right_layout.addWidget(self.wb_button)
        
        layout.addLayout(right_layout)
        
        # Add stretch to center the record button
        layout.insertStretch(4, 1)  # Before record button
        layout.insertStretch(6, 1)  # After record button
    
    def _create_separator(self):
        """Create a visual separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #666;")
        return separator
    
    def _connect_signals(self):
        """Connect signals"""
        try:
            # Safe stop manager signals
            self.safe_stop_manager.stop_completed.connect(self._handle_stop_completed)
            
        except Exception as e:
            self.logger.error(f"Failed to connect bottom bar signals: {e}")
    
    def _handle_record_button(self):
        """Handle record button click"""
        try:
            current_state = self.state_machine.current_state
            
            if current_state == CameraState.PREVIEW:
                self.start_recording()
            elif current_state == CameraState.RECORDING:
                self.safe_stop_requested.emit()
            else:
                self.logger.warning(f"Cannot record in state: {current_state}")
                
        except Exception as e:
            self.logger.error(f"Record button error: {e}")
    
    def start_recording(self):
        """Start recording with current settings"""
        try:
            # Get recording parameters
            fps = int(self.fps_combo.currentText())
            codec = self.codec_combo.currentText().lower().replace('.', '').replace('-', '')  # h264 or h265
            container = self.container_combo.currentText().lower()  # mkv or mp4
            
            # Validate settings
            is_valid, error_msg = self.encoder_manager.validate_encoding_settings(
                codec, container, fps, (2048, 1080)
            )
            
            if not is_valid:
                self.logger.error(f"Invalid encoding settings: {error_msg}")
                return
            
            # Check storage space
            estimated_duration = 60  # Assume 60 minutes max
            has_space, estimated_size = self.file_utils.check_storage_requirements(
                estimated_duration, self.config_manager.get("default_bitrate", 20000000) // 1000000
            )
            
            if not has_space:
                self.logger.error("Insufficient storage space for recording")
                return
            
            # Generate filename and path
            output_path = self.file_utils.get_next_filepath(fps, codec, container)
            
            # Start recording
            if self.camera_manager.start_recording(output_path, codec):
                # Update state
                self.state_machine.transition_to(CameraState.RECORDING)
                
                # Create metadata sidecar
                camera_settings = {
                    "fps": fps,
                    "codec": codec,
                    "container": container,
                    "resolution": "2048x1080",
                    "auto_exposure": self.config_manager.get("auto_exposure", True),
                    "auto_white_balance": self.config_manager.get("auto_white_balance", True)
                }
                
                recording_info = {
                    "start_time": str(output_path.stem.split('_')[1]),  # Extract time from filename
                    "bitrate": self.config_manager.get("default_bitrate", 20000000),
                    "audio_enabled": self.audio_manager.selected_device_id is not None
                }
                
                self.file_utils.create_sidecar_metadata(output_path, camera_settings, recording_info)
                
                self.logger.info(f"Recording started: {output_path}")
                self.recording_started.emit()
                
            else:
                self.logger.error("Failed to start recording")
                
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
    
    def _handle_fps_change(self, fps_text):
        """Handle frame rate change"""
        try:
            fps = int(fps_text)
            self.camera_manager.set_frame_rate(fps)
            self.logger.debug(f"Frame rate changed to {fps}")
            
        except Exception as e:
            self.logger.error(f"Failed to change frame rate: {e}")
    
    def _handle_codec_change(self, codec_text):
        """Handle codec change"""
        try:
            self.config_manager.set("default_codec", codec_text.lower())
            self.logger.debug(f"Codec changed to {codec_text}")
            
        except Exception as e:
            self.logger.error(f"Failed to change codec: {e}")
    
    def _handle_container_change(self, container_text):
        """Handle container format change"""
        try:
            self.config_manager.set("default_container", container_text.lower())
            self.logger.debug(f"Container changed to {container_text}")
            
        except Exception as e:
            self.logger.error(f"Failed to change container: {e}")
    
    def _handle_stop_completed(self, success):
        """Handle safe stop completion"""
        if success:
            self.logger.info("Recording stopped successfully")
        else:
            self.logger.error("Recording stop had errors")
    
    def handle_state_change(self, new_state: CameraState, old_state: CameraState):
        """Handle state changes"""
        try:
            if new_state == CameraState.RECORDING:
                # Update record button to stop button
                self.record_button.setText("⬛ STOP")
                self.record_button.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        background-color: #ff9800;
                        color: white;
                        border: 3px solid #ffc107;
                        border-radius: 8px;
                    }
                    QPushButton:pressed {
                        background-color: #f57c00;
                        border-color: #ff9800;
                    }
                """)
                
                # Disable settings controls during recording
                self.fps_combo.setEnabled(False)
                self.codec_combo.setEnabled(False)
                self.container_combo.setEnabled(False)
                
            elif new_state == CameraState.STOPPING:
                # Show stopping state
                self.record_button.setText("STOPPING...")
                self.record_button.setEnabled(False)
                
            elif new_state == CameraState.PREVIEW:
                # Reset to record button
                self.record_button.setText("⬤ REC")
                self.record_button.setEnabled(True)
                self.record_button.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        background-color: #d32f2f;
                        color: white;
                        border: 3px solid #f44336;
                        border-radius: 8px;
                    }
                    QPushButton:pressed {
                        background-color: #b71c1c;
                        border-color: #d32f2f;
                    }
                """)
                
                # Re-enable settings controls
                self.fps_combo.setEnabled(True)
                self.codec_combo.setEnabled(True)
                self.container_combo.setEnabled(True)
                
            elif new_state == CameraState.ERROR:
                # Disable all controls
                self.record_button.setEnabled(False)
                self.fps_combo.setEnabled(False)
                self.codec_combo.setEnabled(False)
                self.container_combo.setEnabled(False)
                
            elif new_state == CameraState.IDLE:
                # Disable record button
                self.record_button.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Error handling state change in bottom bar: {e}")