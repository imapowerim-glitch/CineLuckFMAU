"""
Safe Stop Dialog
Modal dialog for safe recording stop with progress indication
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class SafeStopDialog(QDialog):
    """Modal dialog for safe stop operation"""
    
    def __init__(self, safe_stop_manager):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.safe_stop_manager = safe_stop_manager
        
        # UI elements
        self.status_label = None
        self.progress_bar = None
        self.force_stop_btn = None
        self.cancel_btn = None
        
        # State
        self.stop_initiated = False
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.debug("Safe stop dialog initialized")
    
    def _setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Stopping Recording")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        # Style for touch interface
        self.setStyleSheet("""
            QDialog {
                background-color: #333;
                border: 2px solid #555;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                min-height: 40px;
                min-width: 80px;
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #555;
            }
            QProgressBar {
                border: 1px solid #666;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Safely Stopping Recording")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        layout.addWidget(title_label)
        
        # Status message
        self.status_label = QLabel("Preparing to stop...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #ccc;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Warning message
        warning_label = QLabel("Please wait for safe stop to complete.\\nForcing stop may corrupt the recording.")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_label.setStyleSheet("color: #ff9800; font-size: 12px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #666;")
        layout.addWidget(separator)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
            }
            QPushButton:pressed {
                background-color: #777;
            }
        """)
        self.cancel_btn.clicked.connect(self._handle_cancel)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.force_stop_btn = QPushButton("Force Stop")
        self.force_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.force_stop_btn.clicked.connect(self._handle_force_stop)
        button_layout.addWidget(self.force_stop_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect safe stop manager signals"""
        try:
            self.safe_stop_manager.stop_progress.connect(self._update_progress)
            self.safe_stop_manager.stop_completed.connect(self._handle_stop_completed)
            
        except Exception as e:
            self.logger.error(f"Failed to connect safe stop dialog signals: {e}")
    
    def show(self):
        """Show dialog and start safe stop"""
        try:
            super().show()
            
            if not self.stop_initiated:
                self.stop_initiated = True
                self.status_label.setText("Initiating safe stop...")
                
                # Start safe stop process
                # Note: The actual managers would be passed from the calling context
                # For now, we'll simulate the process
                self._start_safe_stop_simulation()
                
        except Exception as e:
            self.logger.error(f"Failed to show safe stop dialog: {e}")
    
    def _start_safe_stop_simulation(self):
        """Start simulated safe stop process"""
        # This would normally call:
        # self.safe_stop_manager.safe_stop_recording(camera_manager, encoder_manager)
        
        # For simulation, we'll use a timer to simulate the process
        self.simulation_timer = QTimer()
        self.simulation_step = 0
        self.simulation_steps = [
            "Stopping recording...",
            "Draining encoder...",
            "Finalizing file...",
            "Finalizing camera...",
            "Returning to preview...",
            "Ready"
        ]
        
        def simulate_step():
            if self.simulation_step < len(self.simulation_steps):
                self._update_progress(self.simulation_steps[self.simulation_step])
                self.simulation_step += 1
            else:
                self.simulation_timer.stop()
                self._handle_stop_completed(True)
        
        self.simulation_timer.timeout.connect(simulate_step)
        self.simulation_timer.start(800)  # 800ms between steps
    
    def _update_progress(self, status_message):
        """Update progress status"""
        try:
            self.status_label.setText(status_message)
            self.logger.debug(f"Safe stop progress: {status_message}")
            
            # Update button states based on progress
            if "Ready" in status_message or "completed" in status_message.lower():
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                self.cancel_btn.setText("Close")
                self.force_stop_btn.setEnabled(False)
            
        except Exception as e:
            self.logger.error(f"Failed to update safe stop progress: {e}")
    
    def _handle_stop_completed(self, success):
        """Handle safe stop completion"""
        try:
            if success:
                self.status_label.setText("Recording stopped successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
            else:
                self.status_label.setText("Stop completed with errors")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
            
            # Update buttons
            self.cancel_btn.setText("Close")
            self.force_stop_btn.setEnabled(False)
            
            # Auto-close after a delay
            QTimer.singleShot(2000, self.accept)
            
        except Exception as e:
            self.logger.error(f"Failed to handle stop completion: {e}")
    
    def _handle_cancel(self):
        """Handle cancel button"""
        try:
            if self.cancel_btn.text() == "Close":
                self.accept()
            else:
                # User wants to cancel the stop operation
                # This would resume recording, but for safety we don't allow this
                self.logger.warning("Cancel not allowed during safe stop")
                
        except Exception as e:
            self.logger.error(f"Failed to handle cancel: {e}")
    
    def _handle_force_stop(self):
        """Handle force stop button"""
        try:
            self.logger.warning("Force stop requested")
            
            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Force Stop Warning")
            msg_box.setText("Force stopping may corrupt the recording file.\\n\\nAre you sure you want to force stop?")
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                # Force stop
                self.status_label.setText("Force stopping...")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                
                # Stop simulation timer if running
                if hasattr(self, 'simulation_timer'):
                    self.simulation_timer.stop()
                
                # Simulate immediate stop
                QTimer.singleShot(500, lambda: self._handle_stop_completed(False))
                
        except Exception as e:
            self.logger.error(f"Failed to handle force stop: {e}")
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        try:
            # Don't allow closing during active stop operation
            if self.stop_initiated and self.cancel_btn.text() != "Close":
                event.ignore()
                return
            
            # Stop simulation timer if running
            if hasattr(self, 'simulation_timer'):
                self.simulation_timer.stop()
            
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error closing safe stop dialog: {e}")
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Disable escape key during active stop
        if event.key() == Qt.Key.Key_Escape:
            if self.stop_initiated and self.cancel_btn.text() != "Close":
                return
        
        super().keyPressEvent(event)