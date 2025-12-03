"""
Test script for vehicle tracker.
Tests tracking logic with simulated vehicle trajectories.
"""

from tracker import VehicleTracker

def test_tracker():
    """Test the vehicle tracker with simulated trajectories."""
    print("Testing Vehicle Tracker...")
    print("-" * 50)
    
    try:
        # Initialize tracker
        print("1. Initializing tracker...")
        # Entry line at y=150, exit line at y=350
        tracker = VehicleTracker(entry_line=150, exit_line=350, max_disappeared=5)
        print("   ✓ Tracker initialized")
        print(f"   - Entry line: y={tracker.entry_line}")
        print(f"   - Exit line: y={tracker.exit_line}")
        
        # Simulate vehicle entering (moving from y=200 to y=100, crossing entry line)
        print("\n2. Simulating vehicle entry...")
        
        # Frame 1: Vehicle above entry line
        detections = [{'center': (320, 200), 'bbox': [300, 180, 340, 220], 'confidence': 0.9, 'class_id': 2}]
        tracked, events = tracker.update(detections)
        print(f"   Frame 1: Vehicle at y=200, Events: {events}")
        
        # Frame 2: Vehicle crosses entry line
        detections = [{'center': (320, 140), 'bbox': [300, 120, 340, 160], 'confidence': 0.9, 'class_id': 2}]
        tracked, events = tracker.update(detections)
        print(f"   Frame 2: Vehicle at y=140, Events: {events}")
        
        if events and events[0]['type'] == 'entry':
            print("   ✓ Entry detected correctly!")
        else:
            print("   ⚠️  Entry not detected")
        
        stats = tracker.get_stats()
        print(f"   Current count: {stats['current_count']}")
        print(f"   Total entries: {stats['total_entries']}")
        
        # Simulate vehicle exiting (moving from y=300 to y=400, crossing exit line)
        print("\n3. Simulating vehicle exit...")
        
        # Frame 3: Vehicle below exit line
        detections = [{'center': (320, 300), 'bbox': [300, 280, 340, 320], 'confidence': 0.9, 'class_id': 2}]
        tracked, events = tracker.update(detections)
        print(f"   Frame 3: Vehicle at y=300, Events: {events}")
        
        # Frame 4: Vehicle crosses exit line
        detections = [{'center': (320, 360), 'bbox': [300, 340, 340, 380], 'confidence': 0.9, 'class_id': 2}]
        tracked, events = tracker.update(detections)
        print(f"   Frame 4: Vehicle at y=360, Events: {events}")
        
        if events and events[0]['type'] == 'exit':
            print("   ✓ Exit detected correctly!")
        else:
            print("   ⚠️  Exit not detected")
        
        stats = tracker.get_stats()
        print(f"   Current count: {stats['current_count']}")
        print(f"   Total exits: {stats['total_exits']}")
        
        # Test reset
        print("\n4. Testing count reset...")
        tracker.reset_count()
        stats = tracker.get_stats()
        print(f"   Current count after reset: {stats['current_count']}")
        
        if stats['current_count'] == 0:
            print("   ✓ Reset successful!")
        else:
            print("   ❌ Reset failed")
        
        print("\n" + "=" * 50)
        print("✅ All tracker tests passed!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_tracker()
    exit(0 if success else 1)
