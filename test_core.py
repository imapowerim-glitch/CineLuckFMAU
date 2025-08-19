#!/usr/bin/env python3
"""
Test script that can run without GUI dependencies
Tests core functionality only
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_core_imports():
    """Test that core non-GUI modules can be imported"""
    try:
        print("Testing core imports...")
        
        from cineluck.config.manager import ConfigManager
        print("✓ ConfigManager imported")
        
        from cineluck.config.defaults import DefaultConfig
        print("✓ DefaultConfig imported")
        
        from cineluck.state.machine import StateMachine, CameraState
        print("✓ StateMachine imported")
        
        from cineluck.utils.system_info import SystemInfo
        print("✓ SystemInfo imported")
        
        from cineluck.utils.file_utils import FileUtils
        print("✓ FileUtils imported")
        
        from cineluck.utils.logging_setup import setup_logging
        print("✓ Logging setup imported")
        
        # Test camera manager (may fail without picamera2)
        try:
            from cineluck.camera.manager import CameraManager
            print("✓ CameraManager imported")
        except ImportError as e:
            print(f"⚠ CameraManager import failed (expected without picamera2): {e}")
        
        # Test audio manager (may fail without audio libs)
        try:
            from cineluck.audio.manager import AudioManager
            print("✓ AudioManager imported")
        except ImportError as e:
            print(f"⚠ AudioManager import failed (expected without audio libs): {e}")
        
        print("\nCore imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Core import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_system():
    """Test configuration system"""
    try:
        print("\nTesting configuration system...")
        
        from cineluck.config.manager import ConfigManager
        from cineluck.config.defaults import DefaultConfig
        import tempfile
        from pathlib import Path
        
        # Create temporary config directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override config directory for testing
            config_manager = ConfigManager()
            config_manager.config_dir = Path(temp_dir) / "test_config"
            config_manager.config_file = config_manager.config_dir / "settings.json"
            
            # Test default config
            defaults = DefaultConfig.get_config_dict()
            assert "display_width" in defaults
            assert defaults["display_width"] == 800
            print("✓ Default configuration loaded")
            
            # Test config manager
            config_manager.ensure_config_dir()
            assert config_manager.config_dir.exists()
            print("✓ Config directory created")
            
            # Test setting and getting values
            config_manager.set("test_key", "test_value")
            assert config_manager.get("test_key") == "test_value"
            print("✓ Config set/get working")
            
            # Test config file persistence
            config_manager._save_config()
            assert config_manager.config_file.exists()
            print("✓ Config file saved")
        
        print("Configuration system tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_machine():
    """Test state machine functionality"""
    try:
        print("\nTesting state machine...")
        
        from cineluck.state.machine import StateMachine, CameraState
        
        # Create state machine
        state_machine = StateMachine()
        assert state_machine.current_state == CameraState.IDLE
        print("✓ State machine initialized in IDLE state")
        
        # Test valid transitions
        assert state_machine.can_transition_to(CameraState.PREVIEW)
        success = state_machine.transition_to(CameraState.PREVIEW)
        assert success
        assert state_machine.current_state == CameraState.PREVIEW
        print("✓ Valid state transition working")
        
        # Test invalid transitions
        assert not state_machine.can_transition_to(CameraState.STOPPING)
        success = state_machine.transition_to(CameraState.STOPPING)
        assert not success
        assert state_machine.current_state == CameraState.PREVIEW  # Should remain unchanged
        print("✓ Invalid state transition blocked")
        
        # Test force transition
        success = state_machine.transition_to(CameraState.IDLE, force=True)
        assert success
        assert state_machine.current_state == CameraState.IDLE
        print("✓ Force transition working")
        
        # Cleanup
        state_machine.shutdown()
        print("✓ State machine shutdown")
        
        print("State machine tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ State machine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_utils():
    """Test file management utilities"""
    try:
        print("\nTesting file utilities...")
        
        from cineluck.utils.file_utils import FileUtils
        from pathlib import Path
        import tempfile
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "recordings"
            file_utils = FileUtils(base_dir)
            
            # Test directory creation
            recording_dir = file_utils.ensure_recording_directory()
            assert recording_dir.exists()
            print("✓ Recording directory created")
            
            # Test filename generation
            filename = file_utils.generate_filename(25, "h264", "mkv")
            assert "2K25" in filename
            assert filename.endswith(".mkv")
            print(f"✓ Filename generated: {filename}")
            
            # Test file path generation
            file_path = file_utils.get_next_filepath(30, "h264", "mkv")
            assert file_path.parent.exists()
            print("✓ File path generation working")
            
            # Test storage check
            free_space = file_utils.get_free_space_gb()
            assert free_space > 0
            print(f"✓ Free space check: {free_space:.1f} GB")
        
        print("File utilities tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ File utilities test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_info():
    """Test system information utilities"""
    try:
        print("\nTesting system information...")
        
        from cineluck.utils.system_info import SystemInfo
        
        system_info = SystemInfo()
        
        # Test basic system checks
        is_pi = system_info.is_raspberry_pi()
        print(f"✓ Raspberry Pi detection: {is_pi}")
        
        if is_pi:
            pi_model = system_info.get_pi_model()
            print(f"✓ Pi model: {pi_model}")
        
        # Test memory info
        memory_info = system_info.get_memory_info()
        assert "total_gb" in memory_info
        print(f"✓ Memory info: {memory_info.get('total_gb', 0):.1f} GB total")
        
        # Test disk usage
        disk_usage = system_info.get_disk_usage(Path("/"))
        assert "free_gb" in disk_usage
        print(f"✓ Disk usage: {disk_usage.get('free_gb', 0):.1f} GB free")
        
        # Test system load
        load_info = system_info.get_system_load()
        print(f"✓ System load: {load_info.get('cpu_percent', 0):.1f}% CPU")
        
        print("System information tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ System information test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all core tests"""
    print("CineLuck Core Test Suite")
    print("=" * 40)
    
    success = True
    
    # Test core imports
    if not test_core_imports():
        success = False
    
    # Test configuration system
    if not test_config_system():
        success = False
    
    # Test state machine
    if not test_state_machine():
        success = False
    
    # Test file utilities
    if not test_file_utils():
        success = False
    
    # Test system information
    if not test_system_info():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All core tests passed!")
        print("\nNote: GUI and hardware-specific tests require")
        print("PyQt6, Picamera2, and audio libraries.")
        sys.exit(0)
    else:
        print("✗ Some core tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()