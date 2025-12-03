#!/usr/bin/env python3
"""
Quick test script to verify platform detection and camera initialization.
Run this before starting the full application.
"""

import sys
import json
from platform_detector import PlatformDetector

def test_platform_detection():
    """Test platform detection."""
    print("\n" + "="*60)
    print("PLATFORM DETECTION TEST")
    print("="*60)
    
    info = PlatformDetector.get_platform_info()
    for key, value in info.items():
        print(f"{key.capitalize()}: {value}")
    
    print("="*60)
    return info['platform']

def test_config_loading():
    """Test configuration loading."""
    print("\n" + "="*60)
    print("CONFIGURATION TEST")
    print("="*60)
    
    try:
        with open('config.json', 'r') as f:
            base_config = json.load(f)
        
        platform = PlatformDetector.detect_platform()
        config = PlatformDetector.get_platform_config(base_config, platform)
        
        print(f"Platform detected: {platform}")
        print(f"Camera source: {config['camera']['source']}")
        print(f"Camera resolution: {config['camera']['width']}x{config['camera']['height']}")
        print(f"Server host: {config['server']['host']}")
        print(f"Server port: {config['server']['port']}")
        print(f"Simulation mode: {config.get('simulation_mode', False)}")
        
        print("="*60)
        return True
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        print("="*60)
        return False

def test_camera():
    """Test camera initialization."""
    print("\n" + "="*60)
    print("CAMERA TEST")
    print("="*60)
    
    try:
        import cv2
        from camera import Camera
        
        with open('config.json', 'r') as f:
            base_config = json.load(f)
        
        platform = PlatformDetector.detect_platform()
        config = PlatformDetector.get_platform_config(base_config, platform)
        
        camera_config = config['camera']
        simulation_mode = config.get('simulation_mode', False)
        
        print(f"Initializing camera (source: {camera_config['source']}, simulation: {simulation_mode})...")
        
        camera = Camera(
            source=camera_config['source'],
            width=camera_config['width'],
            height=camera_config['height'],
            fps=camera_config['fps'],
            simulation_mode=simulation_mode
        )
        
        camera.start()
        
        import time
        time.sleep(1)
        
        frame = camera.get_frame()
        
        if frame is not None:
            print(f"✓ Camera initialized successfully!")
            print(f"  Frame shape: {frame.shape}")
        else:
            print("❌ Failed to get frame from camera")
            camera.stop()
            print("="*60)
            return False
        
        camera.stop()
        print("✓ Camera test completed successfully!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return False

def main():
    """Run all tests."""
    print("\n🧪 RUNNING PRE-FLIGHT TESTS\n")
    
    # Test 1: Platform detection
    platform = test_platform_detection()
    
    # Test 2: Config loading
    config_ok = test_config_loading()
    if not config_ok:
        print("\n❌ Configuration test failed. Please check config.json")
        sys.exit(1)
    
    # Test 3: Camera
    camera_ok = test_camera()
    if not camera_ok:
        print("\n⚠️  Camera test failed. You may need to:")
        print("  - Check camera permissions")
        print("  - Verify camera source in config.json")
        print("  - Enable simulation_mode for testing without camera")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYou can now run the application:")
    print("  python3 app.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
