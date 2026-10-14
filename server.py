import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Standard initialization without eventlet
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def user_view():
    return render_template('user_chat.html')

@app.route('/operator-secret-dashboard')
def operator_view():
    return render_template('operator.html')

@socketio.on('send_from_user')
def handle_user_message(data):
    user_text = data['message']
    emit('new_prompt_for_operator', {'message': user_text}, broadcast=True)

@socketio.on('send_from_operator')
def handle_operator_message(data):
    operator_text = data['message']
    emit('new_response_to_user', {'message': operator_text}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)