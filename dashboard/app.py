import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dashboard-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global configuration
CONFIG = {}

def load_config():
    """Load configuration from config.json."""
    global CONFIG
    try:
        with open('config.json', 'r') as f:
            CONFIG = json.load(f)
        print("Configuration loaded successfully")
    except Exception as e:
        print(f"Error loading config: {e}")
        CONFIG = {"parking_lots": [], "server": {"port": 5001, "host": "0.0.0.0"}}

load_config()

def fetch_parking_data(lot_config):
    """Fetch data from a single parking lot."""
    try:
        # Get stats
        stats_url = f"{lot_config['url']}/api/stats"
        response = requests.get(stats_url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return {
                "id": lot_config['id'],
                "name": lot_config['name'],
                "url": lot_config['url'],
                "status": "online",
                "data": data
            }
    except Exception as e:
        pass
    
    return {
        "id": lot_config['id'],
        "name": lot_config['name'],
        "url": lot_config['url'],
        "status": "offline",
        "error": "Connection failed"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get aggregated stats from all parking lots."""
    results = []
    # In a real production app, this should be done asynchronously/parallel
    for lot in CONFIG.get('parking_lots', []):
        results.append(fetch_parking_data(lot))
    
    return jsonify(results)

@app.route('/api/dashboard/update_capacity', methods=['POST'])
def update_capacity():
    """Update capacity for a specific parking lot."""
    data = request.get_json()
    lot_id = data.get('id')
    new_capacity = data.get('capacity')
    
    if not lot_id or new_capacity is None:
        return jsonify({'error': 'Missing parameters'}), 400
        
    # Find the lot URL
    target_lot = next((lot for lot in CONFIG.get('parking_lots', []) if lot['id'] == lot_id), None)
    
    if not target_lot:
        return jsonify({'error': 'Parking lot not found'}), 404
        
    try:
        # Forward request to the parking app
        url = f"{target_lot['url']}/api/config"
        response = requests.post(url, json={'max_capacity': int(new_capacity)}, timeout=5)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Capacity updated'})
        else:
            return jsonify({'error': 'Failed to update remote capacity'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    server_config = CONFIG.get('server', {})
    port = server_config.get('port', 5005)
    host = server_config.get('host', '0.0.0.0')
    debug = server_config.get('debug', True)
    
    print(f"Dashboard running on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)
