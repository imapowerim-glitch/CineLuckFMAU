#!/usr/bin/env python3
"""
Simple test to verify CineLuck can import and basic functionality works
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test core imports
        import cineluck
        print("✓ Core package imported")
        
        from cineluck.config.manager import ConfigManager
        print("✓ ConfigManager imported")
        
        from cineluck.state.machine import StateMachine, CameraState
        print("✓ StateMachine imported")
        
        from cineluck.camera.manager import CameraManager
        print("✓ CameraManager imported")
        
        from cineluck.audio.manager import AudioManager
        print("✓ AudioManager imported")
        
        from cineluck.utils.system_info import SystemInfo
        print("✓ SystemInfo imported")
        
        from cineluck.utils.file_utils import FileUtils
        print("✓ FileUtils imported")
        
        # Test UI imports (may fail without display)
        try:
            from cineluck.ui.main_window import MainWindow
            print("✓ MainWindow imported")
        except ImportError as e:
            print(f"⚠ MainWindow import failed (expected without display): {e}")
        
        print("\nAll critical imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without GUI"""
    try:
        print("\nTesting basic functionality...")
        
        # Test configuration manager
        from cineluck.config.manager import ConfigManager
        config = ConfigManager()
        print("✓ ConfigManager created")
        
        # Test state machine
        from cineluck.state.machine import StateMachine, CameraState
        state_machine = StateMachine()
        print(f"✓ StateMachine created, initial state: {state_machine.current_state}")
        
        # Test system info
        from cineluck.utils.system_info import SystemInfo
        system_info = SystemInfo()
        is_pi = system_info.is_raspberry_pi()
        print(f"✓ SystemInfo created, is_raspberry_pi: {is_pi}")
        
        # Test file utils
        from cineluck.utils.file_utils import FileUtils
        from pathlib import Path
        file_utils = FileUtils(Path("/tmp/test_recordings"))
        print("✓ FileUtils created")
        
        print("\nBasic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("CineLuck Basic Test Suite")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()