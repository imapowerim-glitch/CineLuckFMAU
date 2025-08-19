"""
System information utilities
Hardware monitoring and system checks
"""

import logging
import psutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class SystemInfo:
    """System information and monitoring utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature in Celsius"""
        try:
            # Try vcgencmd first (Raspberry Pi specific)
            result = subprocess.run(
                ['vcgencmd', 'measure_temp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                if temp_str.startswith('temp=') and temp_str.endswith("'C"):
                    return float(temp_str[5:-2])
            
            # Fallback to thermal zone
            thermal_path = Path('/sys/class/thermal/thermal_zone0/temp')
            if thermal_path.exists():
                temp = int(thermal_path.read_text().strip())
                return temp / 1000.0
            
        except Exception as e:
            self.logger.debug(f"Failed to get CPU temperature: {e}")
        
        return None
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get memory usage information"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent': memory.percent
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory info: {e}")
            return {}
    
    def get_disk_usage(self, path: Path) -> Dict[str, float]:
        """Get disk usage for given path"""
        try:
            usage = psutil.disk_usage(str(path))
            return {
                'total_gb': usage.total / (1024**3),
                'free_gb': usage.free / (1024**3),
                'used_gb': usage.used / (1024**3),
                'percent': (usage.used / usage.total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage for {path}: {e}")
            return {}
    
    def get_gpu_memory(self) -> Optional[Dict[str, int]]:
        """Get GPU memory information (Raspberry Pi specific)"""
        try:
            # Get GPU memory split
            result = subprocess.run(
                ['vcgencmd', 'get_mem', 'gpu'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                gpu_mem_str = result.stdout.strip()
                if gpu_mem_str.startswith('gpu=') and gpu_mem_str.endswith('M'):
                    gpu_mb = int(gpu_mem_str[4:-1])
                    
                    # Get total memory to calculate CPU memory
                    total_mem = psutil.virtual_memory().total / (1024**2)  # MB
                    cpu_mb = int(total_mem - gpu_mb)
                    
                    return {
                        'gpu_mb': gpu_mb,
                        'cpu_mb': cpu_mb,
                        'total_mb': int(total_mem)
                    }
        except Exception as e:
            self.logger.debug(f"Failed to get GPU memory: {e}")
        
        return None
    
    def check_camera_devices(self) -> list:
        """Check available camera devices"""
        devices = []
        try:
            # Check for libcamera devices
            result = subprocess.run(
                ['libcamera-hello', '--list-cameras'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Available cameras' in line or line.strip().startswith('['):
                        devices.append(line.strip())
        except Exception as e:
            self.logger.debug(f"Failed to check camera devices: {e}")
        
        return devices
    
    def check_audio_devices(self) -> Dict[str, list]:
        """Check available audio devices"""
        devices = {'input': [], 'output': []}
        try:
            import sounddevice as sd
            device_list = sd.query_devices()
            
            for i, device in enumerate(device_list):
                device_info = {
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'] if device['max_input_channels'] > 0 else device['max_output_channels'],
                    'default_samplerate': device['default_samplerate']
                }
                
                if device['max_input_channels'] > 0:
                    devices['input'].append(device_info)
                if device['max_output_channels'] > 0:
                    devices['output'].append(device_info)
                    
        except Exception as e:
            self.logger.debug(f"Failed to check audio devices: {e}")
        
        return devices
    
    def test_storage_speed(self, path: Path, test_size_mb: int = 100) -> Optional[float]:
        """Test storage write speed in MB/s"""
        try:
            test_file = path / "speed_test.tmp"
            test_data = b'0' * (1024 * 1024)  # 1MB of data
            
            import time
            start_time = time.time()
            
            with open(test_file, 'wb') as f:
                for _ in range(test_size_mb):
                    f.write(test_data)
                f.flush()
                f.sync()  # Force write to disk
            
            end_time = time.time()
            duration = end_time - start_time
            speed_mbps = test_size_mb / duration
            
            # Clean up
            test_file.unlink(missing_ok=True)
            
            return speed_mbps
            
        except Exception as e:
            self.logger.error(f"Storage speed test failed: {e}")
            return None
    
    def get_system_load(self) -> Dict[str, float]:
        """Get system load information"""
        try:
            load_avg = psutil.getloadavg()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'load_1min': load_avg[0],
                'load_5min': load_avg[1],
                'load_15min': load_avg[2],
                'cpu_percent': cpu_percent
            }
        except Exception as e:
            self.logger.error(f"Failed to get system load: {e}")
            return {}
    
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                return 'Raspberry Pi' in content or 'BCM' in content
        except:
            return False
    
    def get_pi_model(self) -> Optional[str]:
        """Get Raspberry Pi model information"""
        if not self.is_raspberry_pi():
            return None
        
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return f.read().strip('\x00')
        except:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('Model'):
                            return line.split(':', 1)[1].strip()
            except:
                pass
        
        return "Unknown Raspberry Pi"