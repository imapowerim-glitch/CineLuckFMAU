"""
Preview Area Widget
Displays camera preview with monitoring tools
"""

import logging
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
import cv2

from ...state.machine import CameraState


class PreviewArea(QWidget):
    """Central preview area with monitoring tools"""
    
    preview_clicked = pyqtSignal(int, int)  # x, y coordinates
    
    def __init__(self, config_manager, camera_manager, state_machine):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.camera_manager = camera_manager
        self.state_machine = state_machine
        
        # Preview display
        self.preview_label = None
        self.info_overlay = None
        
        # Current frame data
        self.current_frame = None
        self.preview_size = (800, 480)  # Letterboxed preview size
        
        # Monitoring tools state
        self.show_zebras = config_manager.get("show_zebras", False)
        self.show_histogram = config_manager.get("show_histogram", False)
        self.show_waveform = config_manager.get("show_waveform", False)
        self.show_focus_peaking = config_manager.get("show_focus_peaking", False)
        self.show_center_marker = True
        self.punch_in_mode = False
        
        # Zebra settings
        self.zebra_threshold = config_manager.get("zebra_threshold", 90)
        
        # Recording info
        self.recording_duration = 0
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self._update_recording_info)
        self.recording_timer.setInterval(1000)  # Update every second
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.debug("Preview area initialized")
    
    def _setup_ui(self):
        """Set up the preview area UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main preview container
        preview_container = QFrame()
        preview_container.setStyleSheet("""
            QFrame {
                background-color: #000;
                border: 1px solid #333;
            }
        """)
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000;")
        self.preview_label.setMinimumSize(800, 480)
        self.preview_label.setScaledContents(True)
        self.preview_label.mousePressEvent = self._handle_preview_click
        preview_layout.addWidget(self.preview_label)
        
        # Info overlay for recording info, timecode, etc.
        self.info_overlay = QLabel()
        self.info_overlay.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.info_overlay.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 128);
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 3px;
            }
        """)
        self.info_overlay.setVisible(False)
        preview_layout.addWidget(self.info_overlay)
        
        layout.addWidget(preview_container, 1)
        
        # Tool buttons row
        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(4, 4, 4, 4)
        
        # Monitoring tools buttons
        self.zebras_btn = QPushButton("Zebras")
        self.zebras_btn.setCheckable(True)
        self.zebras_btn.setChecked(self.show_zebras)
        self.zebras_btn.clicked.connect(self.toggle_zebras)
        tools_layout.addWidget(self.zebras_btn)
        
        self.histogram_btn = QPushButton("Histogram")
        self.histogram_btn.setCheckable(True)
        self.histogram_btn.setChecked(self.show_histogram)
        self.histogram_btn.clicked.connect(self.toggle_histogram)
        tools_layout.addWidget(self.histogram_btn)
        
        self.waveform_btn = QPushButton("Waveform")
        self.waveform_btn.setCheckable(True)
        self.waveform_btn.setChecked(self.show_waveform)
        self.waveform_btn.clicked.connect(self.toggle_waveform)
        tools_layout.addWidget(self.waveform_btn)
        
        self.focus_btn = QPushButton("Focus Peak")
        self.focus_btn.setCheckable(True)
        self.focus_btn.setChecked(self.show_focus_peaking)
        self.focus_btn.clicked.connect(self.toggle_focus_peaking)
        tools_layout.addWidget(self.focus_btn)
        
        self.punchin_btn = QPushButton("2× Punch In")
        self.punchin_btn.setCheckable(True)
        self.punchin_btn.clicked.connect(self.toggle_punch_in)
        tools_layout.addWidget(self.punchin_btn)
        
        tools_layout.addStretch()
        
        layout.addLayout(tools_layout)
        
        # Show default message
        self._show_no_preview_message()
    
    def _connect_signals(self):
        """Connect camera signals"""
        try:
            self.camera_manager.preview_frame_ready.connect(self._update_preview_frame)
            
        except Exception as e:
            self.logger.error(f"Failed to connect preview signals: {e}")
    
    def _show_no_preview_message(self):
        """Show message when no preview is available"""
        # Create a simple black image with text
        pixmap = QPixmap(800, 480)
        pixmap.fill(Qt.GlobalColor.black)
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 16))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No Preview\\nCamera Initializing...")
        painter.end()
        
        self.preview_label.setPixmap(pixmap)
    
    def _update_preview_frame(self, frame_data):
        """Update preview with new frame data"""
        try:
            if frame_data is None or frame_data.size == 0:
                return
            
            self.current_frame = frame_data.copy()
            
            # Convert YUV to RGB if needed
            if len(frame_data.shape) == 3:
                # Assume YUV420 format from camera
                height, width = frame_data.shape[:2]
                if frame_data.shape[2] == 1:  # Grayscale
                    rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_GRAY2RGB)
                else:
                    rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_YUV2RGB_I420)
            else:
                # Grayscale
                rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_GRAY2RGB)
            
            # Apply monitoring tools
            processed_frame = self._apply_monitoring_tools(rgb_frame)
            
            # Apply punch-in if enabled
            if self.punch_in_mode:
                processed_frame = self._apply_punch_in(processed_frame)
            
            # Convert to Qt format and display
            self._display_frame(processed_frame)
            
        except Exception as e:
            self.logger.debug(f"Preview frame update error: {e}")
    
    def _apply_monitoring_tools(self, frame):
        """Apply enabled monitoring tools to frame"""
        processed_frame = frame.copy()
        
        try:
            # Apply zebras
            if self.show_zebras:
                processed_frame = self._apply_zebras(processed_frame)
            
            # Apply focus peaking
            if self.show_focus_peaking:
                processed_frame = self._apply_focus_peaking(processed_frame)
            
            # Apply center marker
            if self.show_center_marker:
                processed_frame = self._apply_center_marker(processed_frame)
            
            return processed_frame
            
        except Exception as e:
            self.logger.debug(f"Monitoring tools error: {e}")
            return frame
    
    def _apply_zebras(self, frame):
        """Apply zebra pattern to overexposed areas"""
        try:
            # Convert to grayscale for luminance calculation
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Calculate threshold (0-255 range)
            threshold = int((self.zebra_threshold / 100.0) * 255)
            
            # Create zebra mask
            zebra_mask = gray > threshold
            
            # Create zebra pattern
            height, width = gray.shape
            zebra_pattern = np.zeros_like(gray)
            
            # Create diagonal stripes
            for y in range(height):
                for x in range(width):
                    if (x + y) % 8 < 4:  # 4-pixel wide stripes
                        zebra_pattern[y, x] = 255
            
            # Apply zebra pattern to overexposed areas
            zebra_areas = zebra_mask & (zebra_pattern > 0)
            
            # Overlay zebras in magenta
            frame[zebra_areas] = [255, 0, 255]  # Magenta
            
            return frame
            
        except Exception as e:
            self.logger.debug(f"Zebra application error: {e}")
            return frame
    
    def _apply_focus_peaking(self, frame):
        """Apply focus peaking overlay"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Apply Laplacian filter to detect edges (focus)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian = np.absolute(laplacian)
            
            # Normalize and threshold
            laplacian = (laplacian / laplacian.max() * 255).astype(np.uint8)
            focus_mask = laplacian > 30  # Threshold for focus detection
            
            # Apply focus peaking in red
            frame[focus_mask] = [255, 0, 0]  # Red overlay
            
            return frame
            
        except Exception as e:
            self.logger.debug(f"Focus peaking error: {e}")
            return frame
    
    def _apply_center_marker(self, frame):
        """Apply center marker cross"""
        try:
            height, width = frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Draw cross
            cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (255, 255, 255), 1)
            cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (255, 255, 255), 1)
            
            # Draw center dot
            cv2.circle(frame, (center_x, center_y), 2, (255, 255, 255), -1)
            
            return frame
            
        except Exception as e:
            self.logger.debug(f"Center marker error: {e}")
            return frame
    
    def _apply_punch_in(self, frame):
        """Apply 2x punch-in (center crop and scale)"""
        try:
            height, width = frame.shape[:2]
            
            # Calculate center crop area (50% of frame)
            crop_width = width // 2
            crop_height = height // 2
            start_x = (width - crop_width) // 2
            start_y = (height - crop_height) // 2
            
            # Crop center area
            cropped = frame[start_y:start_y + crop_height, start_x:start_x + crop_width]
            
            # Scale back to original size
            scaled = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
            
            return scaled
            
        except Exception as e:
            self.logger.debug(f"Punch-in error: {e}")
            return frame
    
    def _display_frame(self, frame):
        """Convert frame to Qt pixmap and display"""
        try:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            
            # Create QImage
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert to pixmap and display
            pixmap = QPixmap.fromImage(q_image)
            self.preview_label.setPixmap(pixmap)
            
        except Exception as e:
            self.logger.debug(f"Frame display error: {e}")
    
    def _handle_preview_click(self, event):
        """Handle clicks on preview area"""
        try:
            if self.current_frame is not None:
                x = event.x()
                y = event.y()
                
                # Convert to frame coordinates
                label_size = self.preview_label.size()
                frame_x = int((x / label_size.width()) * self.current_frame.shape[1])
                frame_y = int((y / label_size.height()) * self.current_frame.shape[0])
                
                self.preview_clicked.emit(frame_x, frame_y)
                self.logger.debug(f"Preview clicked at ({frame_x}, {frame_y})")
        
        except Exception as e:
            self.logger.debug(f"Preview click error: {e}")
    
    def toggle_zebras(self):
        """Toggle zebra display"""
        self.show_zebras = self.zebras_btn.isChecked()
        self.config_manager.set("show_zebras", self.show_zebras)
        self.logger.debug(f"Zebras: {self.show_zebras}")
    
    def toggle_histogram(self):
        """Toggle histogram display"""
        self.show_histogram = self.histogram_btn.isChecked()
        self.config_manager.set("show_histogram", self.show_histogram)
        self.logger.debug(f"Histogram: {self.show_histogram}")
    
    def toggle_waveform(self):
        """Toggle waveform display"""
        self.show_waveform = self.waveform_btn.isChecked()
        self.config_manager.set("show_waveform", self.show_waveform)
        self.logger.debug(f"Waveform: {self.show_waveform}")
    
    def toggle_focus_peaking(self):
        """Toggle focus peaking"""
        self.show_focus_peaking = self.focus_btn.isChecked()
        self.config_manager.set("show_focus_peaking", self.show_focus_peaking)
        self.logger.debug(f"Focus peaking: {self.show_focus_peaking}")
    
    def toggle_punch_in(self):
        """Toggle 2x punch-in magnification"""
        self.punch_in_mode = self.punchin_btn.isChecked()
        self.logger.debug(f"Punch-in: {self.punch_in_mode}")
    
    def handle_state_change(self, new_state: CameraState, old_state: CameraState):
        """Handle state changes"""
        try:
            if new_state == CameraState.RECORDING:
                # Start recording timer and show overlay
                self.recording_duration = 0
                self.recording_timer.start()
                self.info_overlay.setVisible(True)
                self._update_recording_info()
                
                # Disable monitoring tools during recording for performance
                self._disable_monitoring_tools()
                
            elif old_state == CameraState.RECORDING:
                # Stop recording timer and hide overlay
                self.recording_timer.stop()
                self.info_overlay.setVisible(False)
                
                # Re-enable monitoring tools
                self._enable_monitoring_tools()
            
            elif new_state == CameraState.PREVIEW:
                self._show_no_preview_message()
            
        except Exception as e:
            self.logger.error(f"Error handling state change in preview: {e}")
    
    def _update_recording_info(self):
        """Update recording information overlay"""
        try:
            self.recording_duration += 1
            
            # Format duration as HH:MM:SS
            hours = self.recording_duration // 3600
            minutes = (self.recording_duration % 3600) // 60
            seconds = self.recording_duration % 60
            
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Get current timecode (simplified)
            from datetime import datetime
            timecode = datetime.now().strftime("%H:%M:%S:%f")[:-5]  # Remove microseconds except first digit
            
            info_text = f"REC {duration_str}\\nTC {timecode}"
            self.info_overlay.setText(info_text)
            
        except Exception as e:
            self.logger.debug(f"Recording info update error: {e}")
    
    def _disable_monitoring_tools(self):
        """Disable monitoring tools during recording"""
        self.zebras_btn.setEnabled(False)
        self.histogram_btn.setEnabled(False)
        self.waveform_btn.setEnabled(False)
        self.focus_btn.setEnabled(False)
        self.punchin_btn.setEnabled(False)
    
    def _enable_monitoring_tools(self):
        """Enable monitoring tools after recording"""
        self.zebras_btn.setEnabled(True)
        self.histogram_btn.setEnabled(True)
        self.waveform_btn.setEnabled(True)
        self.focus_btn.setEnabled(True)
        self.punchin_btn.setEnabled(True)