"""
Camera module for video capture and processing.
Handles continuous frame capture and integrates with detector and tracker.
Supports webcams, video files (with looping), and simulation mode.
"""

import cv2
import threading
import time
from typing import Optional, Callable, Union
import numpy as np
import os

class Camera:
    def __init__(self, source: Union[int, str] = 0, width: int = 640, height: int = 480, 
                 fps: int = 10, simulation_mode: bool = False):
        """
        Initialize camera.
        
        Args:
            source: Camera source (0 for default webcam, or video file path)
            width: Frame width
            height: Frame height
            fps: Target frames per second
            simulation_mode: If True, generate blank frames (for testing without camera)
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.simulation_mode = simulation_mode
        
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Video file specific
        self.is_video_file = self._is_video_file(source)
        self.loop_video = True  # Loop video files
        
        # Callbacks
        self.on_frame_callback = None
        
    def _is_video_file(self, source: Union[int, str]) -> bool:
        """Check if source is a video file."""
        if isinstance(source, str):
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
            return any(source.lower().endswith(ext) for ext in video_extensions)
        return False
    
    def start(self):
        """Start camera capture thread."""
        if self.running:
            return
        
        # Simulation mode - no camera needed
        if self.simulation_mode:
            print("Starting in SIMULATION mode (no camera)")
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
            
            # Wait for first frame
            timeout = 2
            start_time = time.time()
            while self.frame is None and time.time() - start_time < timeout:
                time.sleep(0.1)
            return
        
        # Open camera or video file
        if self.is_video_file:
            if not os.path.exists(self.source):
                raise RuntimeError(f"Video file not found: {self.source}")
            print(f"Opening video file: {self.source}")
        else:
            print(f"Opening camera source: {self.source}")
        
        self.cap = cv2.VideoCapture(self.source)
        
        # Try to set camera properties if it's a webcam
        if isinstance(self.source, int):
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera source: {self.source}")
        
        # Get actual properties
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        print(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps} FPS")
        
        # Start capture thread
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        # Wait for first frame
        timeout = 5
        start_time = time.time()
        while self.frame is None and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if self.frame is None:
            raise RuntimeError("Failed to capture first frame")
    
    def stop(self):
        """Stop camera capture."""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _simulation_loop(self):
        """Simulation loop - generates blank frames."""
        frame_time = 1.0 / self.fps
        
        while self.running:
            start = time.time()
            
            # Create a blank frame with some text
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            cv2.putText(frame, "SIMULATION MODE", (50, self.height // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            with self.lock:
                self.frame = frame.copy()
            
            # Call callback if set
            if self.on_frame_callback:
                try:
                    self.on_frame_callback(frame)
                except Exception as e:
                    print(f"Error in frame callback: {e}")
            
            # Maintain target FPS
            elapsed = time.time() - start
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _capture_loop(self):
        """Main capture loop (runs in thread)."""
        frame_time = 1.0 / self.fps
        
        while self.running:
            start = time.time()
            
            ret, frame = self.cap.read()
            
            # If video file ended and looping is enabled, restart
            if not ret and self.is_video_file and self.loop_video:
                print("Video ended, restarting...")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            
            if ret:
                # Resize if needed
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                
                with self.lock:
                    self.frame = frame.copy()
                
                # Call callback if set
                if self.on_frame_callback:
                    try:
                        self.on_frame_callback(frame)
                    except Exception as e:
                        print(f"Error in frame callback: {e}")
            else:
                print("Failed to read frame from camera")
            
            # Maintain target FPS
            elapsed = time.time() - start
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame."""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback function to be called on each frame."""
        self.on_frame_callback = callback
    
    def is_running(self) -> bool:
        """Check if camera is running."""
        return self.running
    
    def get_frame_jpeg(self, quality: int = 80) -> Optional[bytes]:
        """
        Get current frame as JPEG bytes (for streaming).
        
        Args:
            quality: JPEG quality (0-100)
            
        Returns:
            JPEG encoded frame or None
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        if ret:
            return buffer.tobytes()
        return None
