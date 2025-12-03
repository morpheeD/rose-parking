"""
Vehicle tracking and counting module.
Implements simple tracking with virtual line crossing detection.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import cv2

class VehicleTracker:
    def __init__(self, entry_line: int, exit_line: int, max_disappeared: int = 30,
                 tracking_mode: str = 'line_crossing', 
                 size_threshold_entry: int = 5000,
                 size_threshold_exit: int = 2000,
                 size_trend_frames: int = 5,
                 size_change_threshold_pct: float = 30.0,
                 initial_count: int = 0):
        """
        Initialize vehicle tracker.
        
        Args:
            entry_line: Y-coordinate of entry line (for line_crossing mode)
            exit_line: Y-coordinate of exit line (for line_crossing mode)
            max_disappeared: Max frames before removing a tracked object
            tracking_mode: 'line_crossing' or 'perspective_3d'
            size_threshold_entry: Min area (pixels²) to count as entry (perspective_3d)
            size_threshold_exit: Max area (pixels²) to count as exit (perspective_3d)
            size_trend_frames: Number of frames to analyze for size trend
            size_change_threshold_pct: Min % change in size to trigger event
            initial_count: Initial number of vehicles in the parking lot
        """
        self.entry_line = entry_line
        self.exit_line = exit_line
        self.max_disappeared = max_disappeared
        self.tracking_mode = tracking_mode
        
        # Perspective 3D parameters
        self.size_threshold_entry = size_threshold_entry
        self.size_threshold_exit = size_threshold_exit
        self.size_trend_frames = size_trend_frames
        self.size_change_threshold_pct = size_change_threshold_pct
        
        # Tracking state
        self.next_object_id = 0
        self.objects = {}  # {id: center_point}
        self.disappeared = defaultdict(int)
        self.previous_positions = {}  # {id: [previous centers]}
        self.object_sizes = {}  # {id: [historical sizes]} - for perspective_3d
        self.counted_ids = set()  # IDs that have been counted
        
        # Counting state
        self.entry_count = 0
        self.exit_count = 0
        self.current_count = initial_count
        
    def update(self, detections: List[Dict]) -> Tuple[Dict, List[Dict]]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of detections from detector
            
        Returns:
            Tuple of (tracking_info, events)
            - tracking_info: {id: center} for all tracked objects
            - events: List of events (entry/exit) that occurred
        """
        events = []
        
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                # Remove if disappeared too long
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            
            return self.objects.copy(), events
        
        # Get centers from detections
        input_centers = [det['center'] for det in detections]
        
        # If no tracked objects, register all
        if len(self.objects) == 0:
            for center in input_centers:
                self._register(center)
        else:
            # Match detections to existing objects
            object_ids = list(self.objects.keys())
            object_centers = list(self.objects.values())
            
            # Compute distance matrix
            D = np.zeros((len(object_centers), len(input_centers)))
            for i, obj_center in enumerate(object_centers):
                for j, input_center in enumerate(input_centers):
                    D[i, j] = self._distance(obj_center, input_center)
            
            # Find minimum distance matches
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            used_rows = set()
            used_cols = set()
            
            # Update matched objects
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                # Only match if distance is reasonable (< 100 pixels)
                if D[row, col] > 100:
                    continue
                
                object_id = object_ids[row]
                old_center = self.objects[object_id]
                new_center = input_centers[col]
                new_area = detections[col].get('area', 0)  # Get area from detection
                
                # Update object
                self.objects[object_id] = new_center
                self.disappeared[object_id] = 0
                
                # Track previous positions
                if object_id not in self.previous_positions:
                    self.previous_positions[object_id] = []
                self.previous_positions[object_id].append(old_center)
                
                # Keep only last 10 positions
                if len(self.previous_positions[object_id]) > 10:
                    self.previous_positions[object_id].pop(0)
                
                # Check for line crossing or size change (depending on mode)
                event = self._check_event(object_id, old_center, new_center, new_area)
                if event:
                    events.append(event)
                
                used_rows.add(row)
                used_cols.add(col)
            
            # Mark unused objects as disappeared
            unused_rows = set(range(len(object_centers))) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            
            # Register new objects
            unused_cols = set(range(len(input_centers))) - used_cols
            for col in unused_cols:
                self._register(input_centers[col])
        
        return self.objects.copy(), events
    
    def _register(self, center: Tuple[int, int]):
        """Register a new object."""
        self.objects[self.next_object_id] = center
        self.disappeared[self.next_object_id] = 0
        self.previous_positions[self.next_object_id] = []
        self.next_object_id += 1
    
    def _deregister(self, object_id: int):
        """Remove an object from tracking."""
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.previous_positions:
            del self.previous_positions[object_id]
        if object_id in self.object_sizes:
            del self.object_sizes[object_id]
        if object_id in self.counted_ids:
            self.counted_ids.remove(object_id)
    
    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _check_event(self, object_id: int, old_center: Tuple[int, int], 
                     new_center: Tuple[int, int], area: int) -> Optional[Dict]:
        """
        Check if object triggered an event (entry/exit).
        Uses line crossing or size change depending on tracking_mode.
        
        Returns:
            Event dict if event detected, None otherwise
        """
        if self.tracking_mode == 'perspective_3d':
            return self._check_size_change(object_id, area)
        else:
            return self._check_line_crossing(object_id, old_center, new_center)
    
    def _check_size_change(self, object_id: int, area: int) -> Optional[Dict]:
        """
        Check if object crossed entry or exit threshold based on size change.
        For 3D perspective: approaching vehicles grow, receding vehicles shrink.
        
        Returns:
            Event dict if crossing detected, None otherwise
        """
        # Avoid counting the same object twice
        if object_id in self.counted_ids:
            return None
        
        # Initialize size history for this object
        if object_id not in self.object_sizes:
            self.object_sizes[object_id] = []
        
        # Add current size
        self.object_sizes[object_id].append(area)
        
        # Keep only last N sizes
        if len(self.object_sizes[object_id]) > self.size_trend_frames:
            self.object_sizes[object_id].pop(0)
        
        # Need at least 3 measurements for trend
        if len(self.object_sizes[object_id]) < 3:
            return None
        
        sizes = self.object_sizes[object_id]
        first_size = sizes[0]
        last_size = sizes[-1]
        
        # Avoid division by zero
        if first_size == 0:
            return None
        
        # Calculate size change percentage
        size_change_pct = (last_size - first_size) / first_size * 100
        
        # Entry: size increases significantly AND exceeds threshold
        # (vehicle approaching camera)
        if size_change_pct > self.size_change_threshold_pct and last_size > self.size_threshold_entry:
            self.entry_count += 1
            self.current_count += 1
            self.counted_ids.add(object_id)
            return {
                'type': 'entry',
                'vehicle_id': object_id,
                'count': self.current_count,
                'size': last_size,
                'size_change_pct': round(size_change_pct, 1)
            }
        
        # Exit: size decreases significantly AND falls below threshold
        # (vehicle receding from camera)
        if size_change_pct < -self.size_change_threshold_pct and last_size < self.size_threshold_exit:
            self.exit_count += 1
            self.current_count = max(0, self.current_count - 1)
            self.counted_ids.add(object_id)
            return {
                'type': 'exit',
                'vehicle_id': object_id,
                'count': self.current_count,
                'size': last_size,
                'size_change_pct': round(size_change_pct, 1)
            }
        
        return None
    
    def _check_line_crossing(self, object_id: int, old_center: Tuple[int, int], 
                            new_center: Tuple[int, int]) -> Optional[Dict]:
        """
        Check if object crossed entry or exit line.
        For line crossing mode (top-down view).
        
        Returns:
            Event dict if crossing detected, None otherwise
        """
        # Avoid counting the same object twice
        if object_id in self.counted_ids:
            return None
        
        old_y = old_center[1]
        new_y = new_center[1]
        
        # Check entry line crossing (moving downward, y increasing)
        if old_y < self.entry_line and new_y >= self.entry_line:
            self.entry_count += 1
            self.current_count += 1
            self.counted_ids.add(object_id)
            return {
                'type': 'entry',
                'vehicle_id': object_id,
                'count': self.current_count
            }
        
        # Check exit line crossing (moving upward, y decreasing)
        if old_y > self.exit_line and new_y <= self.exit_line:
            self.exit_count += 1
            self.current_count = max(0, self.current_count - 1)
            self.counted_ids.add(object_id)
            return {
                'type': 'exit',
                'vehicle_id': object_id,
                'count': self.current_count
            }
        
        return None
    
    def draw_lines(self, frame: np.ndarray) -> np.ndarray:
        """Draw entry/exit lines on frame (for debugging)."""
        output = frame.copy()
        height, width = frame.shape[:2]
        
        # Draw entry line (green)
        cv2.line(output, (0, self.entry_line), (width, self.entry_line), 
                (0, 255, 0), 2)
        cv2.putText(output, "ENTRY", (10, self.entry_line - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw exit line (red)
        cv2.line(output, (0, self.exit_line), (width, self.exit_line), 
                (0, 0, 255), 2)
        cv2.putText(output, "EXIT", (10, self.exit_line + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return output
    
    def draw_tracked_objects(self, frame: np.ndarray, tracked_objects: Dict) -> np.ndarray:
        """Draw tracked objects with IDs."""
        output = frame.copy()
        
        for object_id, center in tracked_objects.items():
            # Draw center point
            cv2.circle(output, center, 5, (255, 0, 0), -1)
            
            # Draw ID
            cv2.putText(output, f"ID:{object_id}", (center[0] - 20, center[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Draw trajectory if available
            if object_id in self.previous_positions:
                points = self.previous_positions[object_id] + [center]
                for i in range(1, len(points)):
                    cv2.line(output, points[i-1], points[i], (255, 0, 0), 2)
        
        return output
    
    def reset_count(self):
        """Reset the current count to 0."""
        self.current_count = 0
        self.counted_ids.clear()
    
    def get_stats(self) -> Dict:
        """Get current tracking statistics."""
        return {
            'current_count': self.current_count,
            'total_entries': self.entry_count,
            'total_exits': self.exit_count,
            'tracked_objects': len(self.objects)
        }
