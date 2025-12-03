"""
Test script for database operations.
"""

from database import Database
import os

def test_database():
    """Test database operations."""
    print("Testing Database...")
    print("-" * 50)
    
    # Use a test database
    test_db_path = "test_parking.db"
    
    try:
        # Remove existing test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Initialize database
        print("1. Initializing database...")
        db = Database(db_path=test_db_path)
        print("   ✓ Database initialized")
        
        # Test default config
        print("\n2. Testing default configuration...")
        max_capacity = db.get_max_capacity()
        print(f"   Default max capacity: {max_capacity}")
        assert max_capacity == 100, "Default capacity should be 100"
        print("   ✓ Default config correct")
        
        # Test setting config
        print("\n3. Testing config update...")
        db.set_max_capacity(150)
        new_capacity = db.get_max_capacity()
        print(f"   Updated max capacity: {new_capacity}")
        assert new_capacity == 150, "Capacity should be 150"
        print("   ✓ Config update successful")
        
        # Test logging events
        print("\n4. Testing event logging...")
        db.log_event('entry', 1, 1)
        db.log_event('entry', 2, 2)
        db.log_event('exit', 1, 1)
        print("   ✓ Events logged")
        
        # Test retrieving events
        print("\n5. Testing event retrieval...")
        events = db.get_recent_events(limit=10)
        print(f"   Retrieved {len(events)} events")
        assert len(events) == 3, "Should have 3 events"
        print("   ✓ Event retrieval successful")
        
        # Test stats
        print("\n6. Testing statistics...")
        stats = db.get_stats_today()
        print(f"   Today's stats: {stats}")
        print("   ✓ Stats retrieval successful")
        
        # Cleanup
        print("\n7. Cleaning up...")
        os.remove(test_db_path)
        print("   ✓ Test database removed")
        
        print("\n" + "=" * 50)
        print("✅ All database tests passed!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return False

if __name__ == '__main__':
    success = test_database()
    exit(0 if success else 1)
