import logging
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from engineio.payload import Payload

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
Payload.max_decode_packets = 500
socketio = SocketIO(app, async_mode='eventlet')

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@socketio.on('data_client')
def get_data_from_client(data):
    socketio.emit('data', data)

@app.route('/')
def index():
    return render_template('index.html', async_mode='eventlet')

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=2121, debug=False)