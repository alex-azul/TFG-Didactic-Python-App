async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
        eventlet.monkey_patch()
    except ImportError:
        async_mode = 'threading'

print('async_mode is ' + async_mode)

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from threading import Thread
import time
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
#socketio.init_app(app, cors_allowed_origins=["http://localhost:3000", "https://your-production-domain.com"])


class Bootnode:
    def __init__(self):
        self.regular_nodes_connected = []
        self.webapps_connected = []
        self.purge_interval = 1
        Thread(target=self.purge_inactive_regular_nodes, args=(self.purge_interval,), daemon=True).start()

    def add_regular_node(self, ip):
        if not ip in self.regular_nodes_connected:
            self.regular_nodes_connected.append(ip)
            success = True
            send_webapps_regular_nodes_update()

    def remove_regular_node(self, ip):
        success = False
        if ip in self.regular_nodes_connected:
            self.regular_nodes_connected.remove(ip)
            success = True
            send_webapps_regular_nodes_update()
        return success

    def add_webapp(self, ip):
        if not ip in self.webapps_connected:
            self.webapps_connected.append(ip)
            success = True
            send_webapps_webapps_update()

    def remove_webapp(self, ip):
        success = False
        if ip in self.webapps_connected:
            self.webapps_connected.remove(ip)
            success = True
            send_webapps_webapps_update()
        return success

    def purge_inactive_regular_nodes(self, purge_interval):
        while True:
            print(self.regular_nodes_connected);
            for regular_node in self.regular_nodes_connected:
                try:
                    requests.get("http://{}/alive".format(regular_node))
                except:
                    self.remove_regular_node(regular_node)

            time.sleep(purge_interval)
        


bootnode = Bootnode()

def json_response(success, infotext, data={}):
    response = {
        'success': success,
        'infotext': infotext,
        'data': data
    }
    return jsonify(response)

@app.route("/join-regular", methods=["POST"])
def join_bootnode_regular_node():
    regular_node_ip = request.remote_addr
    regular_node_port = str(request.json["port"]);
    regular_nodes_connected = bootnode.regular_nodes_connected.copy()
    bootnode.add_regular_node(regular_node_ip + ":" + regular_node_port)

    return json_response(True, "Node joined successfully", {"peers":regular_nodes_connected})

def send_webapps_regular_nodes_update():
    regular_nodes = bootnode.regular_nodes_connected
    socketio.emit('updated_active_regular_nodes_list', {'active_regular_node_ip_list': regular_nodes}, broadcast=True)

def send_webapps_webapps_update():
    webapps = bootnode.webapps_connected
    
    socketio.emit('updated_active_webapps_list', {'active_webapp_ip_list': webapps}, broadcast=True)


@socketio.on('connect')
def webapp_connected_socket_handler():
    webapp_ip = request.remote_addr
    bootnode.add_webapp(webapp_ip)
    send_webapps_regular_nodes_update()
    send_webapps_webapps_update()

@socketio.on('disconnect')
def webapp_disconnected_socket_handler():
    webapp_ip = request.remote_addr
    bootnode.remove_webapp(webapp_ip)
    send_webapps_regular_nodes_update()
    send_webapps_webapps_update()



if __name__ == "__main__":
    socketio.run(app)