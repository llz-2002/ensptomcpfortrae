from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import socket
import time
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ensp-mcp'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins='*')

devices = {}
device_names = {}
topology_data = {}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class TelnetConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(1)
        self.sock.connect((self.host, self.port))
        self.sock.send(b'\r\n')
        time.sleep(0.1)
        return True

    def send_cmd(self, cmd):
        self.sock.send(f'{cmd}\r\n'.encode())
        time.sleep(1.5)
        return self.sock.recv(8192).decode('gbk', errors='ignore')

    def close(self):
        if self.sock:
            self.sock.close()


def scan_ports(start=2000, end=2050):
    found = []
    for port in range(start, end + 1):
        try:
            s = socket.socket()
            s.settimeout(0.05)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                found.append({'port': port, 'path': f'127.0.0.1:{port}'})
            s.close()
        except:
            pass
    return found


def scan_devices(start: int = 2000, end: int = 2050):
    result = scan_ports(start, end)
    for device in result:
        device['name'] = device_names.get(device['path'], device['path'])
    return result


def connect_device(port: int):
    path = f'127.0.0.1:{port}'
    if path in devices:
        return {'success': False, 'error': 'Device already connected'}
    try:
        conn = TelnetConnection('127.0.0.1', port)
        conn.connect()
        devices[path] = conn
        name = device_names.get(path, path)
        return {'success': True, 'port': port, 'path': path, 'name': name}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_command(path: str, command: str):
    if path not in devices:
        return {'success': False, 'error': 'Device not connected'}
    try:
        result = devices[path].send_cmd(command)
        return {'success': True, 'path': path, 'output': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def disconnect_device(path: str):
    if path not in devices:
        return {'success': False, 'error': 'Device not connected'}
    try:
        devices[path].close()
        del devices[path]
        return {'success': True, 'path': path}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_connected_devices():
    connected = []
    for path in devices:
        port = int(path.split(':')[1])
        connected.append({
            'port': port,
            'path': path,
            'name': device_names.get(path, path)
        })
    return connected


def rename_device(path: str, name: str):
    device_names[path] = name
    return {'success': True, 'path': path, 'name': name}


def get_topology():
    return topology_data


def save_topology(data):
    global topology_data
    topology_data = data
    return {'success': True, 'topology': topology_data}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/devices/scan')
def api_scan():
    start = request.args.get('start', 2000, type=int)
    end = request.args.get('end', 2050, type=int)
    result = scan_devices(start, end)
    return jsonify(result)


@app.route('/api/devices/connect', methods=['POST'])
def api_connect():
    data = request.get_json()
    port = data.get('port')
    result = connect_device(port)
    if result['success']:
        socketio.emit('device_connected', {'port': port, 'path': result['path'], 'name': result['name']})
    else:
        socketio.emit('device_error', {'port': port, 'error': result['error']})
    return jsonify(result)


@app.route('/api/devices/command', methods=['POST'])
def api_command():
    data = request.get_json()
    path = data.get('path')
    command = data.get('command')
    result = send_command(path, command)
    if result['success']:
        socketio.emit('device_output', {'path': path, 'output': result['output']})
    else:
        socketio.emit('device_error', {'path': path, 'error': result['error']})
    return jsonify(result)


@app.route('/api/devices/disconnect', methods=['POST'])
def api_disconnect():
    data = request.get_json()
    path = data.get('path')
    result = disconnect_device(path)
    if result['success']:
        socketio.emit('device_disconnected', {'path': path})
    return jsonify(result)


@app.route('/api/devices')
def api_get_devices():
    result = get_connected_devices()
    return jsonify(result)


@app.route('/api/devices/rename', methods=['POST'])
def api_rename():
    data = request.get_json()
    path = data.get('path')
    name = data.get('name')
    result = rename_device(path, name)
    socketio.emit('device_renamed', {'path': path, 'name': name})
    return jsonify(result)


@app.route('/api/topology', methods=['GET'])
def api_get_topology():
    return jsonify(get_topology())


@app.route('/api/topology', methods=['POST'])
def api_save_topology():
    data = request.get_json()
    result = save_topology(data)
    socketio.emit('topology_updated', get_topology())
    return jsonify(result)


@app.route('/api/topology/file', methods=['POST'])
def api_upload_topology_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    try:
        content = file.read()
        if file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
        else:
            data = {'filename': file.filename, 'content': content.decode('utf-8', errors='ignore')}
        result = save_topology(data)
        socketio.emit('topology_updated', get_topology())
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('scan')
def on_scan(data):
    start = data.get('start', 2000)
    end = data.get('end', 2050)
    result = scan_devices(start, end)
    emit('scan_result', result)


@socketio.on('get_connected_devices')
def on_get_connected_devices():
    connected = get_connected_devices()
    emit('connected_devices_list', connected)


@socketio.on('connect_device')
def on_connect(data):
    port = data.get('port')
    result = connect_device(port)
    if result['success']:
        emit('device_connected', {'port': port, 'path': result['path'], 'name': result['name']})
    else:
        emit('device_error', {'port': port, 'error': result['error']})


@socketio.on('send_command')
def on_send(data):
    path = data.get('path')
    cmd = data.get('command')
    result = send_command(path, cmd)
    if result['success']:
        emit('device_output', {'path': path, 'output': result['output']})
    else:
        emit('device_error', {'path': path, 'error': result['error']})


@socketio.on('disconnect_device')
def on_disconnect_device(data):
    path = data.get('path')
    result = disconnect_device(path)
    if result['success']:
        emit('device_disconnected', {'path': path})


@socketio.on('rename_device')
def on_rename_device(data):
    path = data.get('path')
    new_name = data.get('name', path)
    result = rename_device(path, new_name)
    emit('device_renamed', {'path': path, 'name': new_name})


if __name__ == '__main__':
    print('eNSP Server starting on http://127.0.0.1:5000')
    socketio.run(app, host='0.0.0.0', port=5000)
