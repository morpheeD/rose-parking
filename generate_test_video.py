"""
3D Perspective video generator for testing parking system.
Creates a test video with vehicles approaching/receding from camera.
"""

import cv2
import numpy as np
from typing import List, Tuple
import random


class Vehicle3D:
    """Represents a simulated vehicle in 3D perspective."""
    
    def __init__(self, direction: str, frame_width: int, frame_height: int):
        """
        Initialize vehicle in 3D perspective.
        
        Args:
            direction: 'approach' (entry) or 'recede' (exit)
            frame_width: Frame width
            frame_height: Frame height
        """
        self.direction = direction
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Base dimensions
        self.base_width = 50
        self.base_height = 70
        
        # Color
        colors = [
            (200, 200, 200),  # Silver
            (50, 50, 50),     # Dark gray
            (255, 255, 255),  # White
            (0, 0, 150),      # Red
            (0, 100, 200),    # Orange
            (150, 0, 0),      # Blue
        ]
        self.color = random.choice(colors)
        
        # Depth (0.0 = far, 1.0 = close to camera)
        if direction == 'approach':
            self.depth = random.uniform(0.1, 0.3)  # Start far
            self.depth_speed = random.uniform(0.015, 0.025)  # Approach speed
        else:  # recede
            self.depth = random.uniform(0.7, 0.9)  # Start close
            self.depth_speed = -random.uniform(0.015, 0.025)  # Recede speed
        
        # Horizontal position (lane)
        self.x_ratio = random.choice([0.35, 0.65])  # Two lanes
        
        self.active = True
    
    def update(self):
        """Update vehicle position (depth)."""
        self.depth += self.depth_speed
        
        # Deactivate if out of bounds
        if self.depth < 0.05 or self.depth > 1.0:
            self.active = False
    
    def get_size(self) -> Tuple[int, int]:
        """Get current size based on depth."""
        # Scale: 0.2 (far) to 1.0 (close)
        scale = 0.2 + (self.depth * 0.8)
        width = int(self.base_width * scale)
        height = int(self.base_height * scale)
        return width, height
    
    def get_position(self) -> Tuple[int, int]:
        """Get current position based on depth."""
        # X position (stays in lane)
        x = int(self.frame_width * self.x_ratio)
        
        # Y position (perspective: far = top, close = bottom)
        # Map depth 0.0-1.0 to Y position top-bottom
        y_ratio = 0.2 + (self.depth * 0.6)  # 20% to 80% of height
        y = int(self.frame_height * y_ratio)
        
        return x, y
    
    def draw(self, frame: np.ndarray):
        """Draw vehicle on frame."""
        width, height = self.get_size()
        x, y = self.get_position()
        
        # Calculate corners
        x1 = x - width // 2
        y1 = y - height // 2
        x2 = x + width // 2
        y2 = y + height // 2
        
        # Draw vehicle body
        cv2.rectangle(frame, (x1, y1), (x2, y2), self.color, -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
        
        # Draw windows (top 40% of vehicle)
        window_color = (100, 150, 200)
        window_margin = max(2, width // 10)
        window_height = int(height * 0.4)
        cv2.rectangle(frame, 
                     (x1 + window_margin, y1 + window_margin),
                     (x2 - window_margin, y1 + window_height),
                     window_color, -1)


def generate_perspective_video(
    output_path: str = "test_perspective.mp4",
    duration_seconds: int = 60,
    width: int = 640,
    height: int = 480,
    fps: int = 30,
    vehicles_per_minute: int = 15
):
    """
    Generate a test video with 3D perspective (vehicles approaching/receding).
    
    Args:
        output_path: Output video file path
        duration_seconds: Video duration in seconds
        width, height: Video dimensions
        fps: Frames per second
        vehicles_per_minute: Average number of vehicles per minute
    """
    print(f"🎬 Generating 3D perspective test video: {output_path}")
    print(f"   Duration: {duration_seconds}s, Resolution: {width}x{height}, FPS: {fps}")
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise RuntimeError(f"Failed to create video writer for {output_path}")
    
    vehicles: List[Vehicle3D] = []
    total_frames = duration_seconds * fps
    frames_between_vehicles = int((60 * fps) / vehicles_per_minute)
    
    vehicles_created = 0
    entries = 0
    exits = 0
    
    print(f"   Generating {total_frames} frames...")
    
    for frame_num in range(total_frames):
        # Create background (road with perspective)
        frame = np.ones((height, width, 3), dtype=np.uint8) * 80  # Dark gray
        
        # Draw road with perspective (trapezoid shape)
        # Far end (top)
        far_left = int(width * 0.35)
        far_right = int(width * 0.65)
        far_y = int(height * 0.15)
        
        # Near end (bottom)
        near_left = 0
        near_right = width
        near_y = height
        
        # Draw road surface
        road_pts = np.array([
            [far_left, far_y],
            [far_right, far_y],
            [near_right, near_y],
            [near_left, near_y]
        ], np.int32)
        cv2.fillPoly(frame, [road_pts], (60, 60, 60))
        
        # Draw center line (dashed, with perspective)
        for i in range(10):
            y_start = far_y + int((near_y - far_y) * i / 10)
            y_end = far_y + int((near_y - far_y) * (i + 0.5) / 10)
            
            # X position narrows towards top
            depth_ratio = (y_start - far_y) / (near_y - far_y)
            x_pos = int(width / 2)
            
            line_width = max(1, int(2 + depth_ratio * 3))
            cv2.line(frame, (x_pos, y_start), (x_pos, y_end), (255, 255, 255), line_width)
        
        # Draw lane markers
        for lane_x in [0.35, 0.65]:
            for i in range(10):
                y_start = far_y + int((near_y - far_y) * i / 10)
                y_end = far_y + int((near_y - far_y) * (i + 0.5) / 10)
                
                depth_ratio = (y_start - far_y) / (near_y - far_y)
                x_left = far_left + int((near_left - far_left) * depth_ratio)
                x_right = far_right + int((near_right - far_right) * depth_ratio)
                x_pos = int(x_left + (x_right - x_left) * lane_x)
                
                cv2.line(frame, (x_pos, y_start), (x_pos, y_end), (200, 200, 200), 1)
        
        # Spawn new vehicles
        if frame_num % frames_between_vehicles == 0 and frame_num > 0:
            # 60% entries (approaching), 40% exits (receding)
            direction = 'approach' if random.random() < 0.6 else 'recede'
            
            vehicle = Vehicle3D(direction, width, height)
            vehicles.append(vehicle)
            vehicles_created += 1
            
            if direction == 'approach':
                entries += 1
            else:
                exits += 1
        
        # Update and draw vehicles (back to front for proper layering)
        active_vehicles = []
        for vehicle in vehicles:
            vehicle.update()
            if vehicle.active:
                active_vehicles.append(vehicle)
        
        # Sort by depth (far to near) for proper rendering
        active_vehicles.sort(key=lambda v: v.depth)
        
        for vehicle in active_vehicles:
            vehicle.draw(frame)
        
        vehicles = active_vehicles
        
        # Add info overlay
        cv2.putText(frame, f"3D PERSPECTIVE VIEW", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_num}/{total_frames}", (10, height - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Vehicles: {vehicles_created} (E:{entries} / X:{exits})", (10, height - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Active: {len(vehicles)}", (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Write frame
        out.write(frame)
        
        # Progress
        if frame_num % (fps * 5) == 0:  # Every 5 seconds
            progress = (frame_num / total_frames) * 100
            print(f"   Progress: {progress:.1f}% ({frame_num}/{total_frames} frames)")
    
    out.release()
    print(f"✅ Video generated successfully!")
    print(f"   Total vehicles: {vehicles_created} (Entries: {entries}, Exits: {exits})")
    print(f"   File: {output_path}")
    print(f"\nTo use this video:")
    print(f"1. Config already set to: tracking.mode = \"perspective_3d\"")
    print(f"2. Update config.json: camera.source = \"{output_path}\"")
    print(f"3. Run: python3 app.py")


if __name__ == "__main__":
    import sys
    
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    output = sys.argv[2] if len(sys.argv) > 2 else "test_perspective.mp4"
    
    print("=" * 60)
    print("🚗 3D PERSPECTIVE TEST VIDEO GENERATOR")
    print("=" * 60)
    
    generate_perspective_video(
        output_path=output,
        duration_seconds=duration,
        width=640,
        height=480,
        fps=30,
        vehicles_per_minute=15
    )
    
    print("=" * 60)
