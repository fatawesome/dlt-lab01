import requests
import time
import json

from flask import Flask, request

from blockchain import Blockchain, Block

app = Flask(__name__)
blockchain = Blockchain()


@app.route('/create-transaction', methods=['POST'])
def create_transaction():
    data = request.get_json()
    fields = ['author', 'content']

    for field in fields:
        if not data.get(field):
            return 'Invalid transaction data', 404

    data['timestamp'] = time.time()
    blockchain.add_new_transaction(data)
    return 'Success', 201


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({
        'length': len(chain_data),
        'chain': chain_data,
        'peers': list(peers)
    })


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return 'No transactions to mine'
    else:
        # before telling to the network it is needed to check
        # if chain is the longest one
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            announce_new_block(blockchain.last_block)  # announce
        return f'Block #{blockchain.last_block.index} is mined.'


@app.route('/pending')
def get_pending_transactions():
    return json.dumps(blockchain.unconfirmed_transactions)


# set of hosts which are connected to the network
peers = set()


@app.route('/register-peer', methods=['POST'])
def register_peer():
    """
    Add new peer to the network.
    """
    peer_address = request.get_json()['peer_address']
    if not peer_address:
        return 'Peer address is required', 400

    # add peer to the set of hosts
    peers.add(peer_address)

    # return the blockchain to new peer
    return get_chain()


@app.route('/sync-with', methods=['POST'])
def sync_with_peer():
    """
    POST here to sync the chain with this node.
    """
    peer_address = request.get_json()['peer_address']
    if not peer_address:
        return 'Peer address is required', 400

    data = {'peer_address': request.host_url}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(peer_address + '/register-peer',
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        print('---------')
        print(response.json())
        print('---------')
        # update chain and peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return 'Sync successful', 200
    else:
        # if goes wrong, pass it on to the API response
        return response.content, response.status_code


@app.route('/add_block', methods=['POST'])
def add_block():
    """
    Add a block mined by other peer to this peers' chain.
    """
    data = request.get_json()
    block = Block(data['index'],
                  data['transactions'],
                  data['timestamp'],
                  data['pred_hash'],
                  data['nonce'])

    proof = data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return 'The block was discarded by the peer', 400
    return 'Block was added to the peers\' chain', 201


def announce_new_block(block):
    """
    Function to say to all the network that another block was mined.
    """
    for peer in peers:
        url = f'{peer}add_block'
        requests.post(
            url,
            data=json.dumps(block.__dict__, sort_keys=True),
            headers={'Content-Type': 'application/json'}
        )


def create_chain_from_dump(dump):
    """
    Construct chain from json dump.
    """
    new_blockchain = Blockchain()
    for idx, data in enumerate(dump):
        if idx == 0:
            continue
        block = Block(
            data['index'],
            data['transactions'],
            data['timestamp'],
            data['pred_hash'],
            data['nonce']
        )
        proof = data['hash']
        added = new_blockchain.add_block(block, proof)
        if not added:
            raise Exception('The chain dump was tampered!')
    return new_blockchain


def consensus():
    """
    If longer chain is found, replace current chain with it.
    """
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for peer in peers:
        response = requests.get(f'{peer}chain')
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.is_chain_valid(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True
    return False
