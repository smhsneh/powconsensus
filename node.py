from flask import Flask, jsonify, request
from blockchain import Blockchain
import requests
import sys

app = Flask(__name__)

blockchain = Blockchain(difficulty=4)
peer_nodes = set()


# ── transactions ────────────────────────────────────────────

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    if not data or 'transaction' not in data:
        return jsonify({'error': 'transaction field is required'}), 400

    blockchain.add_transaction(data['transaction'])
    return jsonify({
        'message': 'transaction added to pending pool',
        'pending': blockchain.pending_transactions
    }), 201


# ── mining ───────────────────────────────────────────────────

@app.route('/mine', methods=['GET'])
def mine():
    if not blockchain.pending_transactions:
        return jsonify({'message': 'no pending transactions to mine'}), 400

    block = blockchain.mine_pending_transactions()

    broadcast_block(block.to_dict())

    return jsonify({
        'message': 'block mined successfully',
        'block': block.to_dict()
    }), 200


# ── chain ────────────────────────────────────────────────────

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({
        'chain': blockchain.to_dict(),
        'length': len(blockchain.chain),
        'is_valid': blockchain.is_chain_valid(),
        'pending_transactions': blockchain.pending_transactions
    }), 200


# ── peer nodes ───────────────────────────────────────────────

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    data = request.get_json()
    if not data or 'nodes' not in data:
        return jsonify({'error': 'nodes list is required'}), 400

    for node in data['nodes']:
        peer_nodes.add(node)

    return jsonify({
        'message': 'nodes registered',
        'total_nodes': list(peer_nodes)
    }), 201


# ── consensus ────────────────────────────────────────────────

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced, new_length = resolve_conflicts()

    if replaced:
        return jsonify({
            'message': 'chain replaced with longer valid chain',
            'new_length': new_length
        }), 200
    else:
        return jsonify({
            'message': 'our chain is authoritative',
            'length': len(blockchain.chain)
        }), 200


# ── helpers ──────────────────────────────────────────────────

def broadcast_block(block_dict):
    for node in peer_nodes:
        try:
            requests.post(
                f'http://{node}/blocks/receive',
                json=block_dict,
                timeout=3
            )
        except requests.exceptions.RequestException:
            pass


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    block_data = request.get_json()
    if not block_data:
        return jsonify({'error': 'no block data received'}), 400

    resolve_conflicts()
    return jsonify({'message': 'block received, chain synced'}), 200


def resolve_conflicts():
    global blockchain
    longest_chain = None
    max_length = len(blockchain.chain)

    for node in peer_nodes:
        try:
            response = requests.get(f'http://{node}/chain', timeout=3)
            if response.status_code == 200:
                data = response.json()
                peer_length = data['length']
                peer_chain = data['chain']

                if peer_length > max_length and is_valid_chain(peer_chain):
                    max_length = peer_length
                    longest_chain = peer_chain
        except requests.exceptions.RequestException:
            pass

    if longest_chain:
        rebuild_chain(longest_chain)
        return True, max_length

    return False, len(blockchain.chain)


def is_valid_chain(chain_data):
    if not chain_data:
        return False

    target = "0" * blockchain.difficulty

    for i in range(1, len(chain_data)):
        current = chain_data[i]
        previous = chain_data[i - 1]

        if current['previous_hash'] != previous['hash']:
            return False

        if not current['hash'].startswith(target):
            return False

    return True


def rebuild_chain(chain_data):
    import hashlib, json
    from blockchain import Block

    new_chain = []
    for block_data in chain_data:
        block = Block.__new__(Block)
        block.index = block_data['index']
        block.timestamp = block_data['timestamp']
        block.transactions = block_data['transactions']
        block.previous_hash = block_data['previous_hash']
        block.nonce = block_data['nonce']
        block.hash = block_data['hash']
        block.difficulty = block_data['difficulty']
        new_chain.append(block)

    blockchain.chain = new_chain


# ── run ──────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    print(f'starting node on port {port}')
    app.run(host='0.0.0.0', port=port, debug=False)