"""
File management utilities
Handles video file organization and metadata
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class FileUtils:
    """File management utilities for CineLuck"""
    
    def __init__(self, base_dir: Path):
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(base_dir)
        self.current_date_dir = None
        self.take_counter = 1
    
    def ensure_recording_directory(self) -> Path:
        """Ensure today's recording directory exists"""
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_dir / today
        
        try:
            date_dir.mkdir(parents=True, exist_ok=True)
            self.current_date_dir = date_dir
            self.logger.info(f"Recording directory: {date_dir}")
            
            # Update take counter
            self._update_take_counter()
            
            return date_dir
        except Exception as e:
            self.logger.error(f"Failed to create recording directory: {e}")
            raise
    
    def _update_take_counter(self):
        """Update take counter based on existing files"""
        if not self.current_date_dir:
            return
        
        try:
            # Find highest numbered take
            max_take = 0
            for file_path in self.current_date_dir.glob("*.mkv"):
                try:
                    # Extract take number from filename
                    name = file_path.stem
                    parts = name.split('_')
                    if len(parts) >= 2:
                        # Look for take number in filename
                        for part in parts:
                            if part.startswith('take') and part[4:].isdigit():
                                take_num = int(part[4:])
                                max_take = max(max_take, take_num)
                except:
                    continue
            
            self.take_counter = max_take + 1
            self.logger.debug(f"Take counter set to {self.take_counter}")
            
        except Exception as e:
            self.logger.warning(f"Failed to update take counter: {e}")
            self.take_counter = 1
    
    def generate_filename(self, 
                         fps: int, 
                         codec: str, 
                         container: str = "mkv",
                         custom_suffix: str = "") -> str:
        """
        Generate filename according to spec:
        YYYY-MM-DD_HH-MM-SS_2Kfps_codec.mkv
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        
        # Add take counter if there are multiple takes
        take_suffix = f"_take{self.take_counter:03d}" if self.take_counter > 1 else ""
        
        # Add custom suffix if provided
        custom_part = f"_{custom_suffix}" if custom_suffix else ""
        
        filename = f"{date_str}_{time_str}_2K{fps}_{codec}{take_suffix}{custom_part}.{container}"
        
        # Increment take counter for next file
        self.take_counter += 1
        
        return filename
    
    def get_next_filepath(self, 
                         fps: int, 
                         codec: str, 
                         container: str = "mkv",
                         custom_suffix: str = "") -> Path:
        """Get full path for next recording file"""
        recording_dir = self.ensure_recording_directory()
        filename = self.generate_filename(fps, codec, container, custom_suffix)
        return recording_dir / filename
    
    def create_sidecar_metadata(self, 
                               video_path: Path, 
                               camera_settings: Dict,
                               recording_info: Dict) -> Path:
        """Create JSON sidecar file with camera settings and metadata"""
        metadata = {
            "video_file": video_path.name,
            "timestamp": datetime.now().isoformat(),
            "camera_settings": camera_settings,
            "recording_info": recording_info,
            "cineluck_version": "1.0.0"
        }
        
        sidecar_path = video_path.with_suffix('.json')
        
        try:
            with open(sidecar_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            self.logger.info(f"Sidecar metadata created: {sidecar_path}")
            return sidecar_path
            
        except Exception as e:
            self.logger.error(f"Failed to create sidecar metadata: {e}")
            raise
    
    def get_free_space_gb(self, path: Path = None) -> float:
        """Get free space in GB for given path or recording directory"""
        check_path = path or self.current_date_dir or self.base_dir
        
        try:
            stat = shutil.disk_usage(str(check_path))
            return stat.free / (1024**3)  # Convert to GB
        except Exception as e:
            self.logger.error(f"Failed to get free space for {check_path}: {e}")
            return 0.0
    
    def check_storage_requirements(self, 
                                  duration_minutes: int, 
                                  bitrate_mbps: int) -> Tuple[bool, float]:
        """
        Check if there's enough storage for recording
        Returns (has_space, estimated_size_gb)
        """
        # Estimate file size: bitrate * duration + 10% overhead
        estimated_size_gb = (bitrate_mbps * duration_minutes * 60) / (8 * 1024) * 1.1
        
        free_space = self.get_free_space_gb()
        has_space = free_space > (estimated_size_gb + 2.0)  # Keep 2GB buffer
        
        return has_space, estimated_size_gb
    
    def cleanup_incomplete_files(self):
        """Clean up incomplete or zero-size files"""
        if not self.current_date_dir or not self.current_date_dir.exists():
            return
        
        try:
            for file_path in self.current_date_dir.iterdir():
                if file_path.is_file() and file_path.suffix in ['.mkv', '.mp4']:
                    # Check if file is empty or very small (likely incomplete)
                    if file_path.stat().st_size < 1024:  # Less than 1KB
                        self.logger.warning(f"Removing incomplete file: {file_path}")
                        file_path.unlink()
                        
                        # Also remove corresponding sidecar
                        sidecar = file_path.with_suffix('.json')
                        if sidecar.exists():
                            sidecar.unlink()
        except Exception as e:
            self.logger.error(f"Failed to cleanup incomplete files: {e}")
    
    def get_recent_recordings(self, limit: int = 10) -> list:
        """Get list of recent recording files"""
        recordings = []
        
        try:
            # Search in the last few days
            for days_back in range(7):
                check_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                check_date = check_date.replace(day=check_date.day - days_back)
                date_str = check_date.strftime("%Y-%m-%d")
                date_dir = self.base_dir / date_str
                
                if date_dir.exists():
                    for file_path in date_dir.glob("*.mkv"):
                        recordings.append({
                            'path': file_path,
                            'name': file_path.name,
                            'size_mb': file_path.stat().st_size / (1024**2),
                            'created': datetime.fromtimestamp(file_path.stat().st_ctime)
                        })
                
                if len(recordings) >= limit:
                    break
            
            # Sort by creation time, newest first
            recordings.sort(key=lambda x: x['created'], reverse=True)
            return recordings[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get recent recordings: {e}")
            return []
    
    def estimate_recording_bitrate(self, target_size_gb: float, duration_minutes: int) -> int:
        """Estimate required bitrate for target file size"""
        if duration_minutes <= 0:
            return 20000000  # Default 20 Mbps
        
        # Calculate bitrate in bits per second
        target_size_bits = target_size_gb * 8 * 1024 * 1024 * 1024
        duration_seconds = duration_minutes * 60
        bitrate_bps = target_size_bits / duration_seconds
        
        # Add overhead for container and audio
        bitrate_bps *= 0.9  # 90% for video, 10% for audio/overhead
        
        return int(bitrate_bps)