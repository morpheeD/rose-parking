"""
Parking simulator module.
Generates random entry/exit events for testing without camera.
"""

import random
import time
import threading
from typing import Callable, Optional


class ParkingSimulator:
    """Simulates parking entry/exit events for testing."""
    
    def __init__(self, 
                 min_interval: float = 2.0,
                 max_interval: float = 8.0,
                 entry_probability: float = 0.6):
        """
        Initialize parking simulator.
        
        Args:
            min_interval: Minimum seconds between events
            max_interval: Maximum seconds between events
            entry_probability: Probability of entry vs exit (0.0-1.0)
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.entry_probability = entry_probability
        
        self.running = False
        self.thread = None
        self.on_event_callback = None
        
        self.vehicle_id_counter = 1000
        self.current_count = 0
    
    def start(self):
        """Start generating random events."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        print("🎮 Parking simulator started - generating random events")
    
    def stop(self):
        """Stop generating events."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🎮 Parking simulator stopped")
    
    def set_event_callback(self, callback: Callable[[dict], None]):
        """Set callback function to be called on each event."""
        self.on_event_callback = callback
    
    def _simulation_loop(self):
        """Main simulation loop (runs in thread)."""
        while self.running:
            # Wait random interval
            interval = random.uniform(self.min_interval, self.max_interval)
            time.sleep(interval)
            
            # Decide entry or exit
            # If parking is empty, force entry
            # If parking is full (>95%), force exit
            if self.current_count == 0:
                event_type = 'entry'
            elif self.current_count > 95:
                event_type = 'exit'
            else:
                event_type = 'entry' if random.random() < self.entry_probability else 'exit'
            
            # Don't allow exit if count is 0
            if event_type == 'exit' and self.current_count <= 0:
                event_type = 'entry'
            
            # Generate event
            self._generate_event(event_type)
    
    def _generate_event(self, event_type: str):
        """Generate a single event."""
        # Update count
        if event_type == 'entry':
            self.current_count += 1
        else:
            self.current_count = max(0, self.current_count - 1)
        
        # Generate vehicle ID
        vehicle_id = self.vehicle_id_counter
        self.vehicle_id_counter += 1
        
        # Create event
        event = {
            'type': event_type,
            'vehicle_id': vehicle_id,
            'count': self.current_count,
            'simulated': True
        }
        
        # Log
        emoji = "🚗➡️" if event_type == 'entry' else "🚗⬅️"
        print(f"{emoji} Simulated {event_type.upper()}: Vehicle #{vehicle_id} - Count: {self.current_count}")
        
        # Call callback
        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")
    
    def reset_count(self):
        """Reset vehicle count to 0."""
        self.current_count = 0
    
    def get_current_count(self) -> int:
        """Get current vehicle count."""
        return self.current_count


# Convenience function
def create_simulator(min_interval: float = 2.0, 
                     max_interval: float = 8.0,
                     entry_probability: float = 0.6) -> ParkingSimulator:
    """Create and return a parking simulator instance."""
    return ParkingSimulator(min_interval, max_interval, entry_probability)


if __name__ == "__main__":
    # Test the simulator
    def on_event(event):
        print(f"  → Event received: {event}")
    
    print("Testing Parking Simulator...")
    print("Press Ctrl+C to stop\n")
    
    simulator = create_simulator(min_interval=1.0, max_interval=3.0)
    simulator.set_event_callback(on_event)
    simulator.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        simulator.stop()
