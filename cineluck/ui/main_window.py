"""
Main Window for CineLuck
Touch-first interface layout for 800x640 display
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from .widgets.top_bar import TopBar
from .widgets.preview_area import PreviewArea  
from .widgets.bottom_bar import BottomBar
from .panels.exposure_panel import ExposurePanel
from .panels.color_panel import ColorPanel
from .dialogs.safe_stop_dialog import SafeStopDialog
from ..state.machine import CameraState


class MainWindow(QWidget):
    """Main application window with touch-first layout"""
    
    def __init__(self, config_manager, state_machine, camera_manager, 
                 encoder_manager, audio_manager, system_info, file_utils, safe_stop_manager):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Store component references
        self.config_manager = config_manager
        self.state_machine = state_machine
        self.camera_manager = camera_manager
        self.encoder_manager = encoder_manager
        self.audio_manager = audio_manager
        self.system_info = system_info
        self.file_utils = file_utils
        self.safe_stop_manager = safe_stop_manager
        
        # UI components
        self.top_bar = None
        self.preview_area = None
        self.bottom_bar = None
        self.exposure_panel = None
        self.color_panel = None
        self.safe_stop_dialog = None
        
        # Panel state
        self.left_panel_visible = False
        self.right_panel_visible = False
        
        # Initialize UI
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Set up the main UI layout"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create top bar (status and info)
        self.top_bar = TopBar(
            self.config_manager,
            self.system_info,
            self.file_utils,
            self.camera_manager
        )
        main_layout.addWidget(self.top_bar)
        
        # Create main content area (horizontal layout)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left panel (exposure controls) - initially hidden
        self.exposure_panel = ExposurePanel(
            self.config_manager,
            self.camera_manager,
            self.state_machine
        )
        self.exposure_panel.setVisible(False)
        self.exposure_panel.setFixedWidth(200)
        content_layout.addWidget(self.exposure_panel)
        
        # Center preview area
        self.preview_area = PreviewArea(
            self.config_manager,
            self.camera_manager,
            self.state_machine
        )
        content_layout.addWidget(self.preview_area, 1)  # Expandable
        
        # Right panel (color/WB controls) - initially hidden
        self.color_panel = ColorPanel(
            self.config_manager,
            self.camera_manager,
            self.state_machine
        )
        self.color_panel.setVisible(False)
        self.color_panel.setFixedWidth(200)
        content_layout.addWidget(self.color_panel)
        
        main_layout.addWidget(content_widget, 1)  # Expandable
        
        # Create bottom bar (recording controls)
        self.bottom_bar = BottomBar(
            self.config_manager,
            self.state_machine,
            self.camera_manager,
            self.encoder_manager,
            self.audio_manager,
            self.file_utils,
            self.safe_stop_manager
        )
        main_layout.addWidget(self.bottom_bar)
        
        # Set window properties
        self.setWindowTitle("CineLuck Professional Video Camera")
        self.setFixedSize(800, 640)
        
        # Create dialogs
        self.safe_stop_dialog = SafeStopDialog(self.safe_stop_manager)
    
    def _connect_signals(self):
        """Connect UI signals"""
        try:
            # State machine signals
            self.state_machine.state_changed.connect(self._handle_state_change)
            
            # Bottom bar signals
            self.bottom_bar.exposure_panel_requested.connect(self.toggle_exposure_panel)
            self.bottom_bar.color_panel_requested.connect(self.toggle_color_panel)
            self.bottom_bar.safe_stop_requested.connect(self.show_safe_stop_dialog)
            
            # Panel close signals
            self.exposure_panel.close_requested.connect(self.hide_exposure_panel)
            self.color_panel.close_requested.connect(self.hide_color_panel)
            
        except Exception as e:
            self.logger.error(f"Failed to connect UI signals: {e}")
    
    def _handle_state_change(self, new_state: CameraState, old_state: CameraState):
        """Handle state changes in the UI"""
        try:
            # Update UI elements based on state
            if new_state == CameraState.RECORDING:
                self.hide_exposure_panel()
                self.hide_color_panel()
            
            # Pass state change to child widgets
            self.top_bar.handle_state_change(new_state, old_state)
            self.bottom_bar.handle_state_change(new_state, old_state)
            self.preview_area.handle_state_change(new_state, old_state)
            
        except Exception as e:
            self.logger.error(f"Error handling state change in UI: {e}")
    
    def toggle_exposure_panel(self):
        """Toggle visibility of exposure panel"""
        if self.left_panel_visible:
            self.hide_exposure_panel()
        else:
            self.show_exposure_panel()
    
    def show_exposure_panel(self):
        """Show exposure panel and hide color panel"""
        if self.state_machine.is_state(CameraState.RECORDING):
            return  # Don't show panels during recording
        
        self.hide_color_panel()
        self.exposure_panel.setVisible(True)
        self.left_panel_visible = True
        self.logger.debug("Exposure panel shown")
    
    def hide_exposure_panel(self):
        """Hide exposure panel"""
        self.exposure_panel.setVisible(False)
        self.left_panel_visible = False
        self.logger.debug("Exposure panel hidden")
    
    def toggle_color_panel(self):
        """Toggle visibility of color panel"""
        if self.right_panel_visible:
            self.hide_color_panel()
        else:
            self.show_color_panel()
    
    def show_color_panel(self):
        """Show color panel and hide exposure panel"""
        if self.state_machine.is_state(CameraState.RECORDING):
            return  # Don't show panels during recording
        
        self.hide_exposure_panel()
        self.color_panel.setVisible(True)
        self.right_panel_visible = True
        self.logger.debug("Color panel shown")
    
    def hide_color_panel(self):
        """Hide color panel"""
        self.color_panel.setVisible(False)
        self.right_panel_visible = False
        self.logger.debug("Color panel hidden")
    
    def show_safe_stop_dialog(self):
        """Show safe stop dialog"""
        if self.state_machine.is_state(CameraState.RECORDING):
            self.safe_stop_dialog.show()
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("CineLuck Error")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Style for touch interface
            msg_box.setStyleSheet("""
                QMessageBox {
                    font-size: 14px;
                }
                QPushButton {
                    min-width: 80px;
                    min-height: 40px;
                }
            """)
            
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"Failed to show error message: {e}")
    
    def show_info_message(self, title: str, message: str):
        """Show information message to user"""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Style for touch interface
            msg_box.setStyleSheet("""
                QMessageBox {
                    font-size: 14px;
                }
                QPushButton {
                    min-width: 80px;
                    min-height: 40px;
                }
            """)
            
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"Failed to show info message: {e}")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        try:
            key = event.key()
            
            # Space bar - toggle recording
            if key == Qt.Key.Key_Space:
                if self.state_machine.is_state(CameraState.PREVIEW):
                    self.bottom_bar.start_recording()
                elif self.state_machine.is_state(CameraState.RECORDING):
                    self.show_safe_stop_dialog()
            
            # F1 - toggle exposure panel
            elif key == Qt.Key.Key_F1:
                self.toggle_exposure_panel()
            
            # F2 - toggle color panel
            elif key == Qt.Key.Key_F2:
                self.toggle_color_panel()
            
            # Escape - hide panels or exit fullscreen
            elif key == Qt.Key.Key_Escape:
                if self.left_panel_visible or self.right_panel_visible:
                    self.hide_exposure_panel()
                    self.hide_color_panel()
                else:
                    if self.isFullScreen():
                        self.showNormal()
            
            # F11 - toggle fullscreen
            elif key == Qt.Key.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
            
            else:
                super().keyPressEvent(event)
                
        except Exception as e:
            self.logger.error(f"Keyboard event error: {e}")
            super().keyPressEvent(event)