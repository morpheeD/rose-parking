"""
Test script for vehicle detector.
Tests YOLO detection on a sample image.
"""

import cv2
import numpy as np
from detector import VehicleDetector

def create_test_image():
    """Create a simple test image with a rectangle (simulating a car)."""
    # Create a blank image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 100
    
    # Draw a rectangle to simulate a car
    cv2.rectangle(img, (200, 200), (400, 350), (0, 0, 255), -1)
    cv2.putText(img, "Test Vehicle", (220, 270), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return img

def test_detector():
    """Test the vehicle detector."""
    print("Testing Vehicle Detector...")
    print("-" * 50)
    
    try:
        # Initialize detector
        print("1. Initializing YOLO detector...")
        detector = VehicleDetector(model_name='yolov8n.pt', conf_threshold=0.3)
        print("   ✓ Detector initialized successfully")
        
        # Create test image
        print("\n2. Creating test image...")
        test_img = create_test_image()
        print("   ✓ Test image created")
        
        # Run detection
        print("\n3. Running detection...")
        detections = detector.detect(test_img)
        print(f"   ✓ Detection complete: {len(detections)} object(s) detected")
        
        # Display results
        if len(detections) > 0:
            print("\n4. Detection results:")
            for i, det in enumerate(detections):
                print(f"   Object {i+1}:")
                print(f"     - Bounding box: {det['bbox']}")
                print(f"     - Confidence: {det['confidence']:.2f}")
                print(f"     - Class ID: {det['class_id']}")
                print(f"     - Center: {det['center']}")
        else:
            print("\n4. No vehicles detected in test image")
            print("   Note: This is expected as the test image is synthetic")
        
        # Test with drawing
        print("\n5. Testing visualization...")
        output_img = detector.draw_detections(test_img, detections)
        print("   ✓ Visualization successful")
        
        # Save output
        cv2.imwrite('test_output.jpg', output_img)
        print("   ✓ Output saved to test_output.jpg")
        
        print("\n" + "=" * 50)
        print("✅ All detector tests passed!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_detector()
    exit(0 if success else 1)
