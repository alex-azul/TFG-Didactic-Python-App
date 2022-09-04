async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
        eventlet.monkey_patch()
    except ImportError:
        async_mode = 'threading'

print('async_mode is ' + async_mode)

from hashlib import sha256
import json
import time
from threading import Thread
import socket

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import requests

class Message:
    def __init__(self, author, content, timestamp):
        self.author = author
        self.content = content
        self.timestamp = timestamp

class Block:
    def __init__(self, block_num, message, timestamp, previous_hash, nonce=0):
        self.block_num = block_num
        self.message = message
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, default=lambda o: o.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    @staticmethod
    def confirm_hash(block):
        is_correct_hash = False

        if hasattr(block, "hash"):
            block_hash = block.hash
            delattr(block, "hash")
            if block.compute_hash() == block_hash:
                is_correct_hash = True
            block.hash = block_hash

        return is_correct_hash
            


class Blockchain:
    difficulty = 2

    def __init__(self):
        m = Message("Alex Moreno Gil", "Bloque origen", 1660578600310)
        self._unmined_messages = []

        origin_block = Block(0, m, 0, "0")
        proof = self.proof_of_work(origin_block)
        origin_block.hash = proof

        self._chain = [origin_block]

    @property
    def chain(self):
        return self._chain.copy()

    @property
    def last_block(self):
        return self._chain[-1]

    @chain.setter
    def chain(self, new_chain):
        self._chain = new_chain
        send_webapps_chain_update()

    def add_block(self, block, proof):
        if not self.is_valid_block(block, proof):
            return False

        block.hash = proof
        self._chain.append(block)
        send_webapps_chain_update()
        return True
    
    @property
    def unmined_messages(self):
        return self._unmined_messages.copy()

    def fifo_add_unmined_message(self, message):
        self._unmined_messages.append(message)
        send_webapps_unmined_messages_update()

    def fifo_pop_unmined_message(self):
        popped_message = self._unmined_messages.pop(0)
        send_webapps_unmined_messages_update()
        return popped_message

    def is_valid_block(self, block, proof):
        is_valid_proof = Blockchain.is_valid_proof(block, proof)
        is_valid_previous_hash = self.last_block.hash == block.previous_hash

        return is_valid_proof and is_valid_previous_hash
                

    @classmethod
    def is_valid_proof(cls, block, proof):
        meets_expected_difficulty_proof = proof.startswith('0' * cls.difficulty)
        is_computed_correctly_proof = proof == block.compute_hash()

        return meets_expected_difficulty_proof and is_computed_correctly_proof

    @staticmethod
    def proof_of_work(block):
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    @staticmethod
    def init_chain_from_json(json_chain):
        chain = []
        for block in json_chain:
            object_message = Message(
                block["message"]["author"],
                block["message"]["content"],
                block["message"]["timestamp"]
                )
            object_block = Block(
                block_num=block["block_num"],
                message=object_message,
                timestamp=block["timestamp"],
                previous_hash=block["previous_hash"],
                nonce=block["nonce"]
                )
            object_block.hash = block["hash"]
            chain.append(object_block)

        return chain

    @staticmethod
    def check_chain_validity(chain):
        result = True
        previous_hash = "0"

        for block in chain:
            is_correct_hash = block.confirm_hash(block)
            is_correct_previous_hash = block.previous_hash == previous_hash

            if not is_correct_hash or not is_correct_previous_hash:
                result = False
                break

            previous_hash = block.hash

        return result

    def mine(self):
        if not self.unmined_messages:
            return False

        last_block = self.last_block

        message = self.fifo_pop_unmined_message()

        new_block = Block(block_num=last_block.block_num + 1,
                          message=message,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        return True

def consensus(blockchain, peers):
    longest_chain = None
    current_len = len(blockchain.chain)

    for peer in peers:
        try:
            response = requests.get('http://{}/chain'.format(peer))
            json_chain = response.json()['chain']
            length = len(json_chain)
            if length > current_len:
                chain = blockchain.init_chain_from_json(json_chain)
                if blockchain.check_chain_validity(chain):
                    current_len = length
                    longest_chain = chain
        except:
            peers.remove(peer)

    if longest_chain:
        blockchain.chain = longest_chain

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('localhost', 0))
regular_node_port = sock.getsockname()[1]
regular_node_port_json = {"port": regular_node_port}

def send_webapps_chain_update():
    chain_json = json.dumps(blockchain.chain, default=lambda o: o.__dict__)
    state = {
        "chain": json.loads(chain_json),
    }
    socketio.emit('updated_chain', state, broadcast=True)

def send_webapps_unmined_messages_update():
    unmined_messages_json = json.dumps(blockchain.unmined_messages, default=lambda o: o.__dict__)
    state = {
        "unmined_messages": json.loads(unmined_messages_json)
    }
    socketio.emit('updated_unmined_messages', state, broadcast=True)

def getPeersFromBootnodes(bootnodes, blockchain, peers):
    while True:
        for bootnode in bootnodes:
            try:
                regular_node_port_json = {"port": regular_node_port}
                response = requests.post("http://{}/join-regular".format(bootnode), json=regular_node_port_json)
                if response.ok:
                    response_data = response.json()
                    if response_data["success"] == True:
                        print("Connected!")
                        for peer in response_data["data"]["peers"]:
                            try:
                                requests.post("http://{}/register-new-peer".format(peer), json={'port':regular_node_port})
                                peers.append(peer)
                            except:
                                print("Error adding regular node {} to peers, skipping...".format(peer))
                        consensus(blockchain, peers)
                        return
                else:
                    print("Error connecting to bootnode {}, skipping...".format(bootnode))
                    time.sleep(1)
            except:
                    print("Waiting for bootnodes...")
                    time.sleep(1)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

blockchain = Blockchain()

bootnodes = ["127.0.0.1:5000"]
peers = []

peer_discovery_thread = Thread(target=getPeersFromBootnodes, args=(bootnodes, blockchain, peers,), daemon=True)
peer_discovery_thread.start()
peer_discovery_thread.join()

webapps = []

def json_response(success, infotext, data=[]):
    response = {
        'success': success,
        'infotext': infotext,
        'data': data
    }
    return jsonify(response)

@app.route('/alive', methods=['GET'])
def alive_beacon():
    return json_response(True, "Connection still alive")

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_json = json.dumps(blockchain.chain, default=lambda o: o.__dict__)
    return json.dumps({"chain": json.loads(chain_json)})

def announce_new_block(block):
    for peer in peers:
        try:
            url = "http://{}/add-block".format(peer)
            requests.post(url, json=json.dumps(block.__dict__, default=lambda o: o.__dict__))
        except:
            peers.remove(peer)

@app.route('/add-block', methods=['POST'])
def network_add_block():
    block_data = json.loads(request.get_json())
    new_block = Block(block_num=block_data["block_num"],
                        message=block_data["message"],
                        timestamp=block_data["timestamp"],
                        previous_hash=block_data["previous_hash"],
                        nonce = block_data["nonce"])
 
    proof = block_data['hash']
    added = blockchain.add_block(new_block, proof)

    if not added:
        return "The block was discarded by the node", 400
 
    return "Block added to the chain", 201

@app.route('/register-new-peer', methods=['POST'])
def add_new_regular_node_to_peers():
    peer_port = request.get_json()['port']
    peer_address = request.remote_addr + ":" + str(peer_port)
    if peer_address not in peers:
        peers.append(peer_address)
        return "Regular node registered successfully", 200
    else:
        return "Regular node already registered", 200

regular_nodes_connected = []
webapps_connected = []

def add_regular_node(ip):
    success = False
    if not ip in regular_nodes_connected:
        regular_nodes_connected.append(ip)
        success = True
    return success

def remove_regular_node(ip):
    success = False
    if ip in regular_nodes_connected:
        regular_nodes_connected.remove(ip)
        success = True
    return success

def add_webapp(ip):
    success = False
    if not ip in webapps_connected:
        webapps_connected.append(ip)
        success = True
    return success

def remove_webapp(ip):
    success = False
    if ip in webapps_connected:
        webapps_connected.remove(ip)
        success = True
    return success


@socketio.on('connect')
def webapp_connected_socket_handler():
    webapp_ip = request.remote_addr
    add_webapp(webapp_ip)

@socketio.on('initialized')
def webapp_initialized_socker_hanlder():
    send_webapps_chain_update()
    send_webapps_unmined_messages_update()

@socketio.on('disconnect')
def webapp_disconnected_socket_handler():
    webapp_ip = request.remote_addr
    remove_webapp(webapp_ip)

@socketio.on('new_unmined_message')
def webapp_new_message(data):
    json_message = data

    required_fields = ["author", "content"]
    for field in required_fields:
        if not json_message.get(field):
            return

    author = json_message["author"]
    content = json_message["content"]
    timestamp = time.time()
    message = Message(author, content, timestamp)
    
    blockchain.fifo_add_unmined_message(message)

@socketio.on('mine')
def webapp_mine():
    consensus(blockchain, peers)
    blockchain.mine()
    announce_new_block(blockchain.last_block)

@socketio.on('mine-locally')
def webapp_mine_locally():
    blockchain.mine()

@socketio.on('consensus')
def webapp_mine_locally():
    consensus(blockchain, peers)


if __name__ == "__main__":
    sock.close()
    socketio.run(app, port=regular_node_port)