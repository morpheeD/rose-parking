"""
Platform detection module.
Automatically detects the platform (Mac, Raspberry Pi, Linux) and loads appropriate configuration.
"""

import platform
import os
from typing import Dict, Any


class PlatformDetector:
    """Detects the current platform and provides platform-specific configurations."""
    
    PLATFORM_MAC = "mac"
    PLATFORM_RASPBERRY_PI = "raspberry_pi"
    PLATFORM_LINUX = "linux"
    PLATFORM_WINDOWS = "windows"
    PLATFORM_UNKNOWN = "unknown"
    
    @staticmethod
    def detect_platform() -> str:
        """
        Detect the current platform.
        
        Returns:
            Platform identifier string
        """
        system = platform.system()
        
        # Mac/Darwin
        if system == "Darwin":
            return PlatformDetector.PLATFORM_MAC
        
        # Windows
        if system == "Windows":
            return PlatformDetector.PLATFORM_WINDOWS
        
        # Linux-based systems
        if system == "Linux":
            # Check if it's a Raspberry Pi
            if PlatformDetector._is_raspberry_pi():
                return PlatformDetector.PLATFORM_RASPBERRY_PI
            return PlatformDetector.PLATFORM_LINUX
        
        return PlatformDetector.PLATFORM_UNKNOWN
    
    @staticmethod
    def _is_raspberry_pi() -> bool:
        """
        Check if running on Raspberry Pi.
        
        Returns:
            True if Raspberry Pi, False otherwise
        """
        # Check for Raspberry Pi specific files
        pi_indicators = [
            "/proc/device-tree/model",  # Contains "Raspberry Pi" on Pi
            "/sys/firmware/devicetree/base/model"
        ]
        
        for indicator in pi_indicators:
            if os.path.exists(indicator):
                try:
                    with open(indicator, 'r') as f:
                        content = f.read().lower()
                        if 'raspberry pi' in content:
                            return True
                except:
                    pass
        
        # Check /proc/cpuinfo for BCM (Broadcom - Raspberry Pi chip)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                if 'bcm' in cpuinfo or 'raspberry' in cpuinfo:
                    return True
        except:
            pass
        
        return False
    
    @staticmethod
    def get_platform_config(base_config: Dict[str, Any], platform: str = None) -> Dict[str, Any]:
        """
        Get platform-specific configuration.
        
        Args:
            base_config: Base configuration dictionary
            platform: Platform identifier (auto-detected if None)
            
        Returns:
            Merged configuration with platform-specific overrides
        """
        if platform is None:
            platform = PlatformDetector.detect_platform()
        
        # Get platform-specific configs if available
        platform_configs = base_config.get('platform_configs', {})
        platform_override = platform_configs.get(platform, {})
        
        # Merge configurations (platform-specific overrides base)
        merged_config = base_config.copy()
        
        # Apply platform-specific camera settings
        if 'camera' in platform_override:
            if 'camera' not in merged_config:
                merged_config['camera'] = {}
            merged_config['camera'].update(platform_override['camera'])
        
        # Apply other platform-specific settings
        for key in ['detection', 'tracking', 'server']:
            if key in platform_override:
                if key not in merged_config:
                    merged_config[key] = {}
                merged_config[key].update(platform_override[key])
        
        return merged_config
    
    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """
        Get detailed platform information.
        
        Returns:
            Dictionary with platform details
        """
        detected_platform = PlatformDetector.detect_platform()
        
        return {
            'platform': detected_platform,
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }


def detect_platform() -> str:
    """Convenience function to detect platform."""
    return PlatformDetector.detect_platform()


def get_platform_config(base_config: Dict[str, Any], platform: str = None) -> Dict[str, Any]:
    """Convenience function to get platform-specific config."""
    return PlatformDetector.get_platform_config(base_config, platform)


def print_platform_info():
    """Print platform information (for debugging)."""
    info = PlatformDetector.get_platform_info()
    print("=" * 50)
    print("Platform Information:")
    print("=" * 50)
    for key, value in info.items():
        print(f"{key.capitalize()}: {value}")
    print("=" * 50)


if __name__ == "__main__":
    # Test platform detection
    print_platform_info()
