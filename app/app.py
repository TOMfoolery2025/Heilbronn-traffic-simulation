from flask import Flask, render_template, request, jsonify
from simulation_manager import manager

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/start', methods=['POST'])
def start():
    manager.start_simulation()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def stop():
    manager.stop_simulation()
    return jsonify({"status": "stopped"})

@app.route('/api/live_data')
def live_data():
    return jsonify({
        "status": manager.status,
        "data": manager.current_data
    })

@app.route('/api/speed', methods=['POST'])
def set_speed():
    data = request.json
    manager.set_speed(data.get('delay', 0.05))
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)