"""
Flask application for parking management system.
Provides REST API and WebSocket for real-time updates.
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import json
from datetime import datetime

from database import Database
from detector import VehicleDetector
from tracker import VehicleTracker
from camera import Camera
from platform_detector import PlatformDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'parking-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global instances
db = Database()
detector = None
tracker = None
camera = None
processing_thread = None
running = False

# Load configuration from file
def load_config():
    """Load configuration from config.json with platform-specific overrides."""
    with open('config.json', 'r') as f:
        base_config = json.load(f)
    
    # Detect platform and get platform-specific config
    platform = PlatformDetector.detect_platform()
    config = PlatformDetector.get_platform_config(base_config, platform)
    
    print("\n" + "="*60)
    print("PLATFORM DETECTION")
    print("="*60)
    platform_info = PlatformDetector.get_platform_info()
    for key, value in platform_info.items():
        print(f"{key.capitalize()}: {value}")
    print("="*60 + "\n")
    
    return config, platform

CONFIG, DETECTED_PLATFORM = load_config()

def init_system():
    """Initialize detection system."""
    global detector, tracker, camera, running
    
    print("Initializing parking management system...")
    
    # Get configuration
    camera_config = CONFIG.get('camera', {})
    detection_config = CONFIG.get('detection', {})
    tracking_config = CONFIG.get('tracking', {})
    simulation_mode = CONFIG.get('simulation_mode', False)
    
    # Initialize detector
    print("Loading YOLO model...")
    model_name = detection_config.get('model', 'yolov8n.pt')
    conf_threshold = detection_config.get('confidence_threshold', 0.5)
    detector = VehicleDetector(model_name=model_name, conf_threshold=conf_threshold)
    
    # Initialize camera
    camera_source = camera_config.get('source', 0)
    camera_width = camera_config.get('width', 640)
    camera_height = camera_config.get('height', 480)
    camera_fps = camera_config.get('fps', 10)
    
    if simulation_mode:
        print("⚠️  SIMULATION MODE ENABLED - No camera required")
    else:
        print(f"Starting camera (source: {camera_source})...")
    
    camera = Camera(
        source=camera_source,
        width=camera_width,
        height=camera_height,
        fps=camera_fps,
        simulation_mode=simulation_mode
    )
    camera.start()
    
    # Initialize tracker with configuration
    entry_line_ratio = tracking_config.get('entry_line_ratio', 0.3)
    exit_line_ratio = tracking_config.get('exit_line_ratio', 0.7)
    entry_line = int(camera_height * entry_line_ratio)
    exit_line = int(camera_height * exit_line_ratio)
    
    # Get tracking mode and parameters
    tracking_mode = tracking_config.get('mode', 'line_crossing')
    max_disappeared = tracking_config.get('max_disappeared_frames', 30)
    
    # Perspective 3D parameters
    size_threshold_entry = tracking_config.get('size_threshold_entry', 5000)
    size_threshold_exit = tracking_config.get('size_threshold_exit', 2000)
    size_trend_frames = tracking_config.get('size_trend_frames', 5)
    size_change_threshold_pct = tracking_config.get('size_change_threshold_pct', 30.0)
    
    # Calculate initial count based on occupancy percentage
    initial_occupancy_pct = CONFIG.get('parking', {}).get('initial_occupancy_percent', 0)
    max_capacity = db.get_max_capacity()
    initial_count = int(max_capacity * initial_occupancy_pct / 100)
    
    tracker = VehicleTracker(
        entry_line=entry_line,
        exit_line=exit_line,
        max_disappeared=max_disappeared,
        tracking_mode=tracking_mode,
        size_threshold_entry=size_threshold_entry,
        size_threshold_exit=size_threshold_exit,
        size_trend_frames=size_trend_frames,
        size_change_threshold_pct=size_change_threshold_pct,
        initial_count=initial_count
    )
    
    print(f"✓ Tracking mode: {tracking_mode}")
    print("✓ System initialized successfully!")
    running = True

def process_frames():
    """Main processing loop (runs in thread)."""
    global detector, tracker, camera, running
    
    while running:
        try:
            # Get frame from camera
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Detect vehicles
            detections = detector.detect(frame)
            
            # Update tracker
            tracked_objects, events = tracker.update(detections)
            
            # Process events (entry/exit)
            for event in events:
                event_type = event['type']
                vehicle_id = event['vehicle_id']
                current_count = event['count']
                
                # Log to database
                db.log_event(event_type, vehicle_id, current_count)
                
                # Emit to web clients
                stats = get_current_stats()
                socketio.emit('parking_update', stats, namespace='/')
                
                print(f"Event: {event_type.upper()} - Vehicle ID: {vehicle_id} - Current count: {current_count}")
            
            # Small delay to prevent CPU overload
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Error in processing loop: {e}")
            time.sleep(1)

def get_current_stats():
    """Get current parking statistics."""
    max_capacity = db.get_max_capacity()
    tracker_stats = tracker.get_stats()
    current_count = tracker_stats['current_count']
    
    occupied = current_count
    available = max(0, max_capacity - occupied)
    occupancy_percent = (occupied / max_capacity * 100) if max_capacity > 0 else 0
    
    return {
        'max_capacity': max_capacity,
        'occupied': occupied,
        'available': available,
        'occupancy_percent': round(occupancy_percent, 1),
        'total_entries': tracker_stats['total_entries'],
        'total_exits': tracker_stats['total_exits'],
        'timestamp': datetime.now().isoformat()
    }

# REST API Routes

@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get current parking statistics."""
    stats = get_current_stats()
    return jsonify(stats)

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current configuration."""
    return jsonify({
        'max_capacity': db.get_max_capacity()
    })

@app.route('/api/config', methods=['POST'])
def api_set_config():
    """Update configuration."""
    data = request.get_json()
    
    if 'max_capacity' in data:
        max_capacity = int(data['max_capacity'])
        if max_capacity < 1:
            return jsonify({'error': 'Max capacity must be at least 1'}), 400
        
        db.set_max_capacity(max_capacity)
        
        # Emit update to all clients
        stats = get_current_stats()
        socketio.emit('parking_update', stats, namespace='/')
        
        return jsonify({'success': True, 'max_capacity': max_capacity})
    
    return jsonify({'error': 'No valid configuration provided'}), 400

@app.route('/api/reset', methods=['POST'])
def api_reset_count():
    """Reset current vehicle count to 0."""
    tracker.reset_count()
    
    stats = get_current_stats()
    socketio.emit('parking_update', stats, namespace='/')
    
    return jsonify({'success': True, 'message': 'Count reset to 0'})

@app.route('/api/events', methods=['GET'])
def api_events():
    """Get recent events."""
    limit = request.args.get('limit', 100, type=int)
    events = db.get_recent_events(limit)
    return jsonify(events)

# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    # Send current stats to newly connected client
    stats = get_current_stats()
    emit('parking_update', stats)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('request_update')
def handle_request_update():
    """Handle manual update request from client."""
    stats = get_current_stats()
    emit('parking_update', stats)

def start_processing():
    """Start the processing thread."""
    global processing_thread
    processing_thread = threading.Thread(target=process_frames, daemon=True)
    processing_thread.start()

if __name__ == '__main__':
    try:
        # Initialize system
        init_system()
        
        # Start processing thread
        start_processing()
        
        # Get server configuration
        server_config = CONFIG.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 5000)
        debug = server_config.get('debug', False)
        
        # Run Flask app
        print("\n" + "="*60)
        print("🚗 PARKING MANAGEMENT SYSTEM STARTED")
        print("="*60)
        print(f"Platform: {DETECTED_PLATFORM}")
        print(f"Web interface: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print(f"Max capacity: {db.get_max_capacity()} spaces")
        if CONFIG.get('simulation_mode', False):
            print("Mode: SIMULATION (no camera)")
        print("="*60 + "\n")
        
        socketio.run(app, host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        running = False
        if camera:
            camera.stop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        if camera:
            camera.stop()
