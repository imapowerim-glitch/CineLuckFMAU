"""
Camera Manager for CineLuck
Handles Picamera2 operations for video recording and preview
"""

import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import numpy as np

try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, H265Encoder
    from picamera2.outputs import FfmpegOutput
    from libcamera import controls
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logging.warning("Picamera2 not available - running in simulation mode")


class CameraManager(QObject):
    """Manages Picamera2 for video recording and preview"""
    
    # Signals
    preview_frame_ready = pyqtSignal(np.ndarray)  # Raw frame data
    recording_started = pyqtSignal(str)           # filename
    recording_stopped = pyqtSignal()
    camera_error = pyqtSignal(str)                # error_message
    camera_stats_updated = pyqtSignal(dict)      # camera_statistics
    
    def __init__(self, config_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        self.camera = None
        self.is_preview_active = False
        self.is_recording = False
        self.current_recording_path = None
        
        # Camera settings
        self.current_fps = config_manager.get("default_frame_rate", 25)
        self.current_resolution = (
            config_manager.get("sensor_width", 2048),
            config_manager.get("sensor_height", 1080)
        )
        
        # Preview settings
        self.preview_resolution = (
            config_manager.get("display_width", 800),
            config_manager.get("display_height", 640)
        )
        
        # Stats timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.setInterval(1000)  # Update every second
        
        # Thread safety
        self._lock = threading.RLock()
        
        self.logger.info(f"Camera manager initialized (Picamera2 available: {PICAMERA2_AVAILABLE})")
    
    def initialize_camera(self) -> bool:
        """Initialize the camera with default settings"""
        if not PICAMERA2_AVAILABLE:
            self.logger.warning("Picamera2 not available - using simulation mode")
            return True
        
        try:
            with self._lock:
                if self.camera:
                    self.close_camera()
                
                self.logger.info("Initializing Picamera2...")
                self.camera = Picamera2()
                
                # Configure camera for DCI 2K recording
                config = self.camera.create_video_configuration(
                    main={
                        "size": self.current_resolution,
                        "format": "YUV420"
                    },
                    lores={
                        "size": self.preview_resolution,
                        "format": "YUV420"
                    },
                    encode="main"
                )
                
                self.camera.configure(config)
                
                # Set initial camera controls
                self._apply_camera_settings()
                
                self.logger.info("Camera initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            self.camera_error.emit(f"Camera initialization failed: {e}")
            return False
    
    def _apply_camera_settings(self):
        """Apply current settings to camera"""
        if not self.camera or not PICAMERA2_AVAILABLE:
            return
        
        try:
            controls_dict = {}
            
            # Frame rate
            controls_dict[controls.FrameDurationLimits] = (
                int(1000000 / self.current_fps),  # Min frame duration (µs)
                int(1000000 / self.current_fps)   # Max frame duration (µs)
            )
            
            # Exposure settings
            if self.config_manager.get("auto_exposure", True):
                controls_dict[controls.AeEnable] = True
                
                # Metering mode
                metering_mode = self.config_manager.get("metering_mode", "average")
                if metering_mode == "center":
                    controls_dict[controls.AeMeteringMode] = controls.AeMeteringModeEnum.CentreWeighted
                elif metering_mode == "spot":
                    controls_dict[controls.AeMeteringMode] = controls.AeMeteringModeEnum.Spot
                else:
                    controls_dict[controls.AeMeteringMode] = controls.AeMeteringModeEnum.Matrix
            else:
                controls_dict[controls.AeEnable] = False
                controls_dict[controls.ExposureTime] = self.config_manager.get("shutter_speed_us", 40000)
                controls_dict[controls.AnalogueGain] = self.config_manager.get("iso_value", 100) / 100.0
            
            # White balance
            if self.config_manager.get("auto_white_balance", True):
                controls_dict[controls.AwbEnable] = True
                controls_dict[controls.AwbMode] = controls.AwbModeEnum.Auto
            else:
                controls_dict[controls.AwbEnable] = False
                controls_dict[controls.ColourGains] = (1.0, 1.0)  # Will be calculated from CCT
            
            # Apply controls
            self.camera.set_controls(controls_dict)
            self.logger.debug(f"Applied camera controls: {controls_dict}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply camera settings: {e}")
    
    def start_preview(self) -> bool:
        """Start camera preview"""
        if not self.camera and not self.initialize_camera():
            return False
        
        try:
            with self._lock:
                if self.is_preview_active:
                    self.logger.warning("Preview already active")
                    return True
                
                if PICAMERA2_AVAILABLE:
                    self.camera.start()
                    time.sleep(0.5)  # Allow camera to settle
                
                self.is_preview_active = True
                self.stats_timer.start()
                
                # Start preview frame processing
                if PICAMERA2_AVAILABLE:
                    self._start_preview_processing()
                
                self.logger.info("Preview started")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start preview: {e}")
            self.camera_error.emit(f"Preview start failed: {e}")
            return False
    
    def stop_preview(self):
        """Stop camera preview"""
        try:
            with self._lock:
                if not self.is_preview_active:
                    return
                
                self.is_preview_active = False
                self.stats_timer.stop()
                
                if PICAMERA2_AVAILABLE and self.camera:
                    self.camera.stop()
                
                self.logger.info("Preview stopped")
                
        except Exception as e:
            self.logger.error(f"Failed to stop preview: {e}")
    
    def _start_preview_processing(self):
        """Start processing preview frames in separate thread"""
        if not PICAMERA2_AVAILABLE:
            return
        
        def preview_worker():
            while self.is_preview_active:
                try:
                    # Capture frame from lores stream
                    frame = self.camera.capture_array("lores")
                    if frame is not None:
                        self.preview_frame_ready.emit(frame)
                    
                    time.sleep(1.0 / self.config_manager.get("preview_fps", 30))
                    
                except Exception as e:
                    self.logger.debug(f"Preview frame error: {e}")
                    if self.is_preview_active:
                        time.sleep(0.1)  # Brief pause before retry
        
        preview_thread = threading.Thread(target=preview_worker, daemon=True)
        preview_thread.start()
    
    def start_recording(self, output_path: Path, codec: str = "h264") -> bool:
        """Start video recording"""
        if not self.camera or not self.is_preview_active:
            self.logger.error("Camera not ready for recording")
            return False
        
        try:
            with self._lock:
                if self.is_recording:
                    self.logger.warning("Recording already in progress")
                    return False
                
                self.logger.info(f"Starting recording to {output_path}")
                
                if PICAMERA2_AVAILABLE:
                    # Select encoder based on codec
                    if codec.lower() == "h265":
                        encoder = H265Encoder(bitrate=self.config_manager.get("default_bitrate", 20000000))
                    else:
                        encoder = H264Encoder(bitrate=self.config_manager.get("default_bitrate", 20000000))
                    
                    # Start recording
                    output = FfmpegOutput(str(output_path))
                    self.camera.start_recording(encoder, output)
                
                self.is_recording = True
                self.current_recording_path = output_path
                self.recording_started.emit(str(output_path))
                
                self.logger.info("Recording started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.camera_error.emit(f"Recording start failed: {e}")
            return False
    
    def stop_recording(self):
        """Stop video recording"""
        try:
            with self._lock:
                if not self.is_recording:
                    return
                
                self.logger.info("Stopping recording...")
                
                if PICAMERA2_AVAILABLE and self.camera:
                    self.camera.stop_recording()
                
                self.is_recording = False
                self.current_recording_path = None
                self.recording_stopped.emit()
                
                self.logger.info("Recording stopped")
                
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            self.camera_error.emit(f"Recording stop failed: {e}")
    
    def stop_recording_safe(self):
        """Safe recording stop with proper cleanup"""
        try:
            # This method is called by the safe stop manager
            # Additional cleanup can be added here
            self.stop_recording()
            
            # Give camera time to finalize
            time.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"Safe recording stop failed: {e}")
            raise
    
    def set_frame_rate(self, fps: int) -> bool:
        """Set camera frame rate"""
        if fps not in self.config_manager.get("frame_rates", [24, 25, 30, 50, 60]):
            self.logger.error(f"Invalid frame rate: {fps}")
            return False
        
        try:
            self.current_fps = fps
            self.config_manager.set("default_frame_rate", fps)
            
            if self.camera and PICAMERA2_AVAILABLE:
                self._apply_camera_settings()
            
            self.logger.info(f"Frame rate set to {fps} fps")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set frame rate: {e}")
            return False
    
    def set_exposure_settings(self, auto_exposure: bool, shutter_us: int = None, iso: int = None):
        """Set exposure settings"""
        try:
            self.config_manager.set("auto_exposure", auto_exposure)
            
            if not auto_exposure:
                if shutter_us is not None:
                    self.config_manager.set("shutter_speed_us", shutter_us)
                if iso is not None:
                    self.config_manager.set("iso_value", iso)
            
            if self.camera and PICAMERA2_AVAILABLE:
                self._apply_camera_settings()
            
            self.logger.info(f"Exposure settings updated: auto={auto_exposure}")
            
        except Exception as e:
            self.logger.error(f"Failed to set exposure settings: {e}")
    
    def set_white_balance(self, auto_wb: bool, cct: int = None, tint: float = None):
        """Set white balance settings"""
        try:
            self.config_manager.set("auto_white_balance", auto_wb)
            
            if not auto_wb:
                if cct is not None:
                    self.config_manager.set("color_temperature", cct)
                if tint is not None:
                    self.config_manager.set("tint", tint)
            
            if self.camera and PICAMERA2_AVAILABLE:
                self._apply_camera_settings()
            
            self.logger.info(f"White balance updated: auto={auto_wb}")
            
        except Exception as e:
            self.logger.error(f"Failed to set white balance: {e}")
    
    def get_camera_stats(self) -> Dict:
        """Get current camera statistics"""
        stats = {
            "fps": self.current_fps,
            "resolution": f"{self.current_resolution[0]}x{self.current_resolution[1]}",
            "is_recording": self.is_recording,
            "is_preview": self.is_preview_active
        }
        
        if self.camera and PICAMERA2_AVAILABLE:
            try:
                metadata = self.camera.capture_metadata()
                if metadata:
                    stats.update({
                        "exposure_time": metadata.get("ExposureTime", 0),
                        "analogue_gain": metadata.get("AnalogueGain", 0),
                        "digital_gain": metadata.get("DigitalGain", 0),
                        "lux": metadata.get("Lux", 0),
                        "focus_value": metadata.get("FocusFoM", 0)
                    })
            except Exception as e:
                self.logger.debug(f"Failed to get camera metadata: {e}")
        
        return stats
    
    def _update_stats(self):
        """Update camera statistics (called by timer)"""
        try:
            stats = self.get_camera_stats()
            self.camera_stats_updated.emit(stats)
        except Exception as e:
            self.logger.debug(f"Stats update error: {e}")
    
    def close_camera(self):
        """Close camera and cleanup"""
        try:
            with self._lock:
                self.stop_recording()
                self.stop_preview()
                
                if self.camera and PICAMERA2_AVAILABLE:
                    self.camera.close()
                    self.camera = None
                
                self.logger.info("Camera closed")
                
        except Exception as e:
            self.logger.error(f"Failed to close camera: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.close_camera()
        except:
            pass