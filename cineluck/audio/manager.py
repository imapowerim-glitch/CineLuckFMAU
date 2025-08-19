"""
Audio Manager for CineLuck
Handles USB audio devices via ALSA and audio monitoring
"""

import logging
import threading
import time
from typing import Dict, List, Optional
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

try:
    import sounddevice as sd
    import audioop
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Audio libraries not available - audio features disabled")


class AudioManager(QObject):
    """Manages audio input and monitoring for CineLuck"""
    
    # Signals
    device_list_updated = pyqtSignal(list)    # Available audio devices
    audio_level_updated = pyqtSignal(float)   # Peak level (0.0 - 1.0)
    audio_error = pyqtSignal(str)             # Error message
    recording_started = pyqtSignal(str)       # Device name
    recording_stopped = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # Audio settings
        self.sample_rate = config_manager.get("audio_sample_rate", 48000)
        self.channels = config_manager.get("audio_channels", 2)
        self.bitrate = config_manager.get("audio_bitrate", 128000)
        
        # Device management
        self.input_devices = []
        self.selected_device_id = None
        self.selected_device_name = ""
        
        # Recording state
        self.is_recording = False
        self.audio_stream = None
        self.current_output_path = None
        
        # Level monitoring
        self.peak_level = 0.0
        self.input_gain = 1.0
        self.monitoring_enabled = True
        
        # Update timer
        self.device_scan_timer = QTimer()
        self.device_scan_timer.timeout.connect(self._scan_audio_devices)
        self.device_scan_timer.setInterval(5000)  # Scan every 5 seconds
        
        # Level update timer
        self.level_timer = QTimer()
        self.level_timer.timeout.connect(self._update_audio_level)
        self.level_timer.setInterval(50)  # Update at 20 Hz
        
        # Thread safety
        self._lock = threading.RLock()
        
        self.logger.info(f"Audio manager initialized (Audio available: {AUDIO_AVAILABLE})")
        
        if AUDIO_AVAILABLE:
            self._scan_audio_devices()
            self.device_scan_timer.start()
    
    def _scan_audio_devices(self):
        """Scan for available audio input devices"""
        if not AUDIO_AVAILABLE:
            return
        
        try:
            devices = sd.query_devices()
            input_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_info = {
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'is_usb': 'USB' in device['name'].upper(),
                        'is_default': i == sd.default.device[0]
                    }
                    input_devices.append(device_info)
            
            # Check if device list changed
            if input_devices != self.input_devices:
                self.input_devices = input_devices
                self.device_list_updated.emit(input_devices)
                
                self.logger.info(f"Found {len(input_devices)} audio input devices")
                for device in input_devices:
                    self.logger.debug(f"  {device['name']} (ID: {device['id']})")
                
                # Auto-select USB device if available and none selected
                if not self.selected_device_id:
                    self._auto_select_device()
        
        except Exception as e:
            self.logger.error(f"Failed to scan audio devices: {e}")
            self.audio_error.emit(f"Audio device scan failed: {e}")
    
    def _auto_select_device(self):
        """Auto-select best available audio device"""
        if not self.input_devices:
            return
        
        # Prefer USB devices
        usb_devices = [d for d in self.input_devices if d['is_usb']]
        if usb_devices:
            device = usb_devices[0]
            self.select_input_device(device['id'])
            self.logger.info(f"Auto-selected USB audio device: {device['name']}")
            return
        
        # Fallback to default device
        default_devices = [d for d in self.input_devices if d['is_default']]
        if default_devices:
            device = default_devices[0]
            self.select_input_device(device['id'])
            self.logger.info(f"Auto-selected default audio device: {device['name']}")
    
    def get_input_devices(self) -> List[Dict]:
        """Get list of available input devices"""
        return self.input_devices.copy()
    
    def select_input_device(self, device_id: int) -> bool:
        """Select audio input device"""
        if not AUDIO_AVAILABLE:
            return False
        
        try:
            # Find device in list
            device_info = None
            for device in self.input_devices:
                if device['id'] == device_id:
                    device_info = device
                    break
            
            if not device_info:
                self.logger.error(f"Audio device ID {device_id} not found")
                return False
            
            # Test device
            try:
                with sd.InputStream(
                    device=device_id,
                    channels=min(self.channels, device_info['channels']),
                    samplerate=self.sample_rate,
                    blocksize=1024
                ):
                    pass  # Just test if we can open the device
            except Exception as e:
                self.logger.error(f"Failed to test audio device: {e}")
                return False
            
            self.selected_device_id = device_id
            self.selected_device_name = device_info['name']
            
            self.logger.info(f"Selected audio device: {self.selected_device_name}")
            
            # Start level monitoring if enabled
            if self.monitoring_enabled:
                self._start_level_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to select audio device: {e}")
            self.audio_error.emit(f"Audio device selection failed: {e}")
            return False
    
    def _start_level_monitoring(self):
        """Start audio level monitoring"""
        if not AUDIO_AVAILABLE or not self.selected_device_id:
            return
        
        try:
            # Stop existing monitoring
            self._stop_level_monitoring()
            
            def audio_callback(indata, frames, time, status):
                if status:
                    self.logger.debug(f"Audio callback status: {status}")
                
                # Calculate peak level
                try:
                    # Apply gain
                    gained_data = indata * self.input_gain
                    
                    # Calculate RMS level
                    rms = np.sqrt(np.mean(gained_data**2))
                    
                    # Convert to dB and normalize
                    if rms > 0:
                        db_level = 20 * np.log10(rms)
                        # Normalize to 0.0-1.0 range (-60dB to 0dB)
                        normalized_level = max(0.0, min(1.0, (db_level + 60) / 60))
                    else:
                        normalized_level = 0.0
                    
                    self.peak_level = normalized_level
                    
                except Exception as e:
                    self.logger.debug(f"Audio level calculation error: {e}")
            
            # Start input stream for monitoring
            self.audio_stream = sd.InputStream(
                device=self.selected_device_id,
                channels=min(self.channels, 2),
                samplerate=self.sample_rate,
                blocksize=1024,
                callback=audio_callback
            )
            
            self.audio_stream.start()
            self.level_timer.start()
            
            self.logger.debug("Audio level monitoring started")
            
        except Exception as e:
            self.logger.error(f"Failed to start audio monitoring: {e}")
            self.audio_error.emit(f"Audio monitoring failed: {e}")
    
    def _stop_level_monitoring(self):
        """Stop audio level monitoring"""
        try:
            self.level_timer.stop()
            
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            self.peak_level = 0.0
            
        except Exception as e:
            self.logger.debug(f"Error stopping audio monitoring: {e}")
    
    def _update_audio_level(self):
        """Update audio level signal (called by timer)"""
        self.audio_level_updated.emit(self.peak_level)
    
    def set_input_gain(self, gain: float):
        """Set input gain (0.0 to 2.0)"""
        self.input_gain = max(0.0, min(2.0, gain))
        self.config_manager.set("audio_input_gain", self.input_gain)
        self.logger.debug(f"Audio input gain set to {self.input_gain}")
    
    def get_input_gain(self) -> float:
        """Get current input gain"""
        return self.input_gain
    
    def set_monitoring_enabled(self, enabled: bool):
        """Enable/disable audio level monitoring"""
        self.monitoring_enabled = enabled
        
        if enabled and self.selected_device_id:
            self._start_level_monitoring()
        else:
            self._stop_level_monitoring()
    
    def start_recording(self, output_path: str) -> bool:
        """Start audio recording (integrated with video recording)"""
        if not AUDIO_AVAILABLE or not self.selected_device_id:
            self.logger.warning("Audio recording not available")
            return False
        
        try:
            with self._lock:
                if self.is_recording:
                    self.logger.warning("Audio recording already in progress")
                    return False
                
                self.current_output_path = output_path
                self.is_recording = True
                
                self.logger.info(f"Audio recording started: {self.selected_device_name}")
                self.recording_started.emit(self.selected_device_name)
                
                # Note: Actual audio recording is handled by the video encoder
                # This just tracks the state
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start audio recording: {e}")
            self.audio_error.emit(f"Audio recording start failed: {e}")
            return False
    
    def stop_recording(self):
        """Stop audio recording"""
        try:
            with self._lock:
                if not self.is_recording:
                    return
                
                self.is_recording = False
                self.current_output_path = None
                
                self.logger.info("Audio recording stopped")
                self.recording_stopped.emit()
                
        except Exception as e:
            self.logger.error(f"Failed to stop audio recording: {e}")
    
    def get_audio_info(self) -> Dict:
        """Get current audio configuration info"""
        info = {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bitrate": self.bitrate,
            "selected_device": self.selected_device_name,
            "input_gain": self.input_gain,
            "is_recording": self.is_recording,
            "peak_level": self.peak_level,
            "monitoring_enabled": self.monitoring_enabled,
            "devices_available": len(self.input_devices)
        }
        
        return info
    
    def test_audio_device(self, device_id: int) -> bool:
        """Test if audio device is working"""
        if not AUDIO_AVAILABLE:
            return False
        
        try:
            # Try to open device briefly
            with sd.InputStream(
                device=device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=512
            ) as stream:
                # Read a small amount of data
                data = stream.read(512)[0]
                return len(data) > 0
                
        except Exception as e:
            self.logger.debug(f"Audio device test failed: {e}")
            return False
    
    def get_device_latency(self, device_id: int) -> Optional[float]:
        """Get audio device latency in seconds"""
        if not AUDIO_AVAILABLE:
            return None
        
        try:
            device_info = sd.query_devices(device_id)
            return device_info.get('default_low_input_latency', 0.0)
        except:
            return None
    
    def reconnect_device(self):
        """Attempt to reconnect to selected audio device"""
        if self.selected_device_id is not None:
            self.logger.info("Attempting to reconnect audio device")
            return self.select_input_device(self.selected_device_id)
        return False
    
    def shutdown(self):
        """Clean shutdown of audio manager"""
        self.logger.info("Shutting down audio manager")
        
        self.device_scan_timer.stop()
        self._stop_level_monitoring()
        self.stop_recording()
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.shutdown()
        except:
            pass