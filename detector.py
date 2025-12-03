"""
YOLO detector module for vehicle detection.
Uses YOLOv8 nano model optimized for Raspberry Pi.
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Tuple, Dict

class VehicleDetector:
    # Vehicle classes from COCO dataset
    VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    def __init__(self, model_name: str = 'yolov8n.pt', conf_threshold: float = 0.5):
        """
        Initialize YOLO detector.
        
        Args:
            model_name: YOLO model to use (yolov8n.pt for nano)
            conf_threshold: Confidence threshold for detections
        """
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        
        # Warm up the model
        dummy_frame = np.zeros((416, 416, 3), dtype=np.uint8)
        self.model.predict(dummy_frame, verbose=False)
        
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: Input image (BGR format)
            
        Returns:
            List of detections, each containing:
                - bbox: [x1, y1, x2, y2]
                - confidence: detection confidence
                - class_id: vehicle class ID
                - center: (cx, cy) center point
                - area: bounding box area in pixels²
        """
        # Run inference
        results = self.model.predict(
            frame,
            conf=self.conf_threshold,
            classes=self.VEHICLE_CLASSES,
            verbose=False,
            imgsz=416  # Reduced size for Raspberry Pi performance
        )
        
        detections = []
        
        if len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Calculate center point
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                
                # Calculate bounding box area (for 3D perspective tracking)
                area = (x2 - x1) * (y2 - y1)
                
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': confidence,
                    'class_id': class_id,
                    'center': (cx, cy),
                    'area': int(area)
                })
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes on frame (for debugging).
        
        Args:
            frame: Input image
            detections: List of detections from detect()
            
        Returns:
            Frame with drawn bounding boxes
        """
        output = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            cx, cy = det['center']
            
            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(output, (cx, cy), 5, (0, 0, 255), -1)
            
            # Draw confidence
            label = f"{conf:.2f}"
            cv2.putText(output, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return output
