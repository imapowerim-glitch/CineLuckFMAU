"""
Encoder Manager for CineLuck
Handles video encoding operations and format management
"""

import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class EncoderManager(QObject):
    """Manages video encoding operations"""
    
    encoding_started = pyqtSignal(str)    # codec_info
    encoding_progress = pyqtSignal(dict)  # progress_info
    encoding_finished = pyqtSignal(bool)  # success
    encoding_error = pyqtSignal(str)      # error_message
    
    def __init__(self, config_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        self.current_encoder = None
        self.current_output_path = None
        self.encoding_process = None
        self.is_encoding = False
        
        # Encoding parameters
        self.supported_codecs = ["h264", "h265"]
        self.supported_containers = ["mkv", "mp4"]
        
        # Hardware encoder settings
        self.hardware_encoder_available = self._check_hardware_encoder()
        
        self.logger.info(f"Encoder manager initialized (HW encoder: {self.hardware_encoder_available})")
    
    def _check_hardware_encoder(self) -> bool:
        """Check if hardware encoder is available"""
        try:
            # Check for V4L2 hardware encoder
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                # Look for encoder devices
                if "encoder" in output or "bcm2835" in output:
                    self.logger.info("Hardware encoder detected")
                    return True
            
            # Fallback check for ffmpeg hardware acceleration
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if "h264_v4l2m2m" in output or "h265_v4l2m2m" in output:
                    self.logger.info("FFmpeg hardware encoder available")
                    return True
            
        except Exception as e:
            self.logger.debug(f"Hardware encoder check failed: {e}")
        
        self.logger.warning("No hardware encoder detected - using software encoding")
        return False
    
    def get_encoding_parameters(self, 
                               codec: str, 
                               container: str, 
                               fps: int, 
                               resolution: tuple) -> Dict:
        """Get encoding parameters for given settings"""
        params = {
            "codec": codec.lower(),
            "container": container.lower(),
            "fps": fps,
            "resolution": resolution,
            "bitrate": self.config_manager.get("default_bitrate", 20000000),
            "use_hardware": self.hardware_encoder_available
        }
        
        # Adjust bitrate based on frame rate and resolution
        width, height = resolution
        pixel_count = width * height
        
        # Base bitrate calculation (bits per pixel per frame)
        if fps >= 50:
            bpp = 0.15  # Higher compression for high frame rates
        elif fps >= 30:
            bpp = 0.2
        else:
            bpp = 0.25
        
        calculated_bitrate = int(pixel_count * fps * bpp)
        
        # Use higher of configured or calculated bitrate
        params["bitrate"] = max(params["bitrate"], calculated_bitrate)
        
        # Codec-specific adjustments
        if codec.lower() == "h265":
            params["bitrate"] = int(params["bitrate"] * 0.7)  # H.265 is more efficient
        
        return params
    
    def start_encoding(self, 
                      input_source, 
                      output_path: Path, 
                      codec: str = "h264",
                      container: str = "mkv",
                      fps: int = 25,
                      resolution: tuple = (2048, 1080)) -> bool:
        """Start encoding process"""
        
        if self.is_encoding:
            self.logger.warning("Encoding already in progress")
            return False
        
        try:
            self.current_output_path = output_path
            params = self.get_encoding_parameters(codec, container, fps, resolution)
            
            self.logger.info(f"Starting encoding: {codec} @ {fps}fps to {container}")
            self.logger.debug(f"Encoding parameters: {params}")
            
            # This method integrates with Picamera2's encoding
            # The actual encoding is handled by the camera manager
            # This class manages the encoding parameters and monitoring
            
            self.is_encoding = True
            self.encoding_started.emit(f"{codec.upper()} {fps}fps")
            
            # Start monitoring thread
            self._start_encoding_monitor()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start encoding: {e}")
            self.encoding_error.emit(f"Encoding start failed: {e}")
            return False
    
    def _start_encoding_monitor(self):
        """Start monitoring encoding progress"""
        def monitor_worker():
            start_time = time.time()
            last_size = 0
            
            while self.is_encoding:
                try:
                    if self.current_output_path and self.current_output_path.exists():
                        current_size = self.current_output_path.stat().st_size
                        duration = time.time() - start_time
                        
                        # Calculate bitrate
                        if duration > 0:
                            current_bitrate = (current_size * 8) / duration  # bits per second
                            
                            progress_info = {
                                "duration_seconds": duration,
                                "file_size_mb": current_size / (1024 * 1024),
                                "current_bitrate": current_bitrate,
                                "growth_rate": (current_size - last_size) / 1024  # KB/s
                            }
                            
                            self.encoding_progress.emit(progress_info)
                            last_size = current_size
                    
                    time.sleep(1.0)  # Update every second
                    
                except Exception as e:
                    self.logger.debug(f"Encoding monitor error: {e}")
                    time.sleep(1.0)
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
    
    def stop_encoding(self) -> bool:
        """Stop encoding process"""
        if not self.is_encoding:
            return True
        
        try:
            self.logger.info("Stopping encoding...")
            self.is_encoding = False
            
            # The actual stop is handled by camera manager
            # This just updates our state
            
            time.sleep(0.5)  # Allow final data to be written
            
            success = True
            if self.current_output_path and self.current_output_path.exists():
                file_size = self.current_output_path.stat().st_size
                success = file_size > 1024  # File should be larger than 1KB
                
                if success:
                    self.logger.info(f"Encoding completed: {file_size / (1024*1024):.1f} MB")
                else:
                    self.logger.warning("Encoding completed but file is very small")
            
            self.encoding_finished.emit(success)
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to stop encoding: {e}")
            self.encoding_error.emit(f"Encoding stop failed: {e}")
            return False
    
    def drain_encoder(self):
        """Drain encoder buffers (part of safe stop sequence)"""
        try:
            self.logger.debug("Draining encoder buffers...")
            
            # For Picamera2, this is handled internally
            # We just need to ensure proper timing
            time.sleep(0.2)
            
        except Exception as e:
            self.logger.error(f"Failed to drain encoder: {e}")
            raise
    
    def finalize_recording(self):
        """Finalize recording (part of safe stop sequence)"""
        try:
            self.logger.debug("Finalizing recording...")
            
            # Ensure all data is written and container is properly closed
            if self.current_output_path:
                # The camera manager handles the actual finalization
                # We just update our state
                pass
            
        except Exception as e:
            self.logger.error(f"Failed to finalize recording: {e}")
            raise
    
    def get_codec_info(self, codec: str) -> Dict:
        """Get information about a codec"""
        codec_info = {
            "name": codec.upper(),
            "hardware_supported": self.hardware_encoder_available,
            "container_support": []
        }
        
        if codec.lower() == "h264":
            codec_info.update({
                "description": "H.264 High Profile",
                "efficiency": "standard",
                "compatibility": "excellent",
                "container_support": ["mkv", "mp4"]
            })
        elif codec.lower() == "h265":
            codec_info.update({
                "description": "H.265 Main Profile", 
                "efficiency": "high",
                "compatibility": "good",
                "container_support": ["mkv", "mp4"]
            })
        
        return codec_info
    
    def get_container_info(self, container: str) -> Dict:
        """Get information about a container format"""
        container_info = {
            "name": container.upper(),
            "codec_support": []
        }
        
        if container.lower() == "mkv":
            container_info.update({
                "description": "Matroska Video (recommended)",
                "crash_safe": True,
                "streaming": False,
                "codec_support": ["h264", "h265"]
            })
        elif container.lower() == "mp4":
            container_info.update({
                "description": "MPEG-4 Part 14",
                "crash_safe": False,
                "streaming": True,
                "codec_support": ["h264", "h265"]
            })
        
        return container_info
    
    def validate_encoding_settings(self, 
                                  codec: str, 
                                  container: str, 
                                  fps: int, 
                                  resolution: tuple) -> tuple:
        """
        Validate encoding settings
        Returns (is_valid, error_message)
        """
        
        # Check codec support
        if codec.lower() not in self.supported_codecs:
            return False, f"Unsupported codec: {codec}"
        
        # Check container support
        if container.lower() not in self.supported_containers:
            return False, f"Unsupported container: {container}"
        
        # Check resolution
        width, height = resolution
        if width < 640 or height < 480:
            return False, "Resolution too small (minimum 640x480)"
        
        if width > 4096 or height > 2160:
            return False, "Resolution too large (maximum 4096x2160)"
        
        # Check frame rate
        supported_fps = self.config_manager.get("frame_rates", [24, 25, 30, 50, 60])
        if fps not in supported_fps:
            return False, f"Unsupported frame rate: {fps}"
        
        # Check high frame rate requirements
        if fps >= 50:
            estimated_bitrate = self.get_encoding_parameters(
                codec, container, fps, resolution
            )["bitrate"]
            
            if estimated_bitrate > 50000000:  # 50 Mbps
                return False, "High frame rate requires SSD storage"
        
        return True, "Settings are valid"
    
    def estimate_file_size(self, 
                          duration_minutes: int, 
                          codec: str, 
                          fps: int, 
                          resolution: tuple) -> float:
        """Estimate file size in GB for given parameters"""
        
        params = self.get_encoding_parameters(codec, "mkv", fps, resolution)
        bitrate_bps = params["bitrate"]
        
        # Calculate size: bitrate * duration + overhead
        duration_seconds = duration_minutes * 60
        size_bits = bitrate_bps * duration_seconds
        size_gb = size_bits / (8 * 1024 * 1024 * 1024)
        
        # Add 10% overhead for container and audio
        size_gb *= 1.1
        
        return size_gb