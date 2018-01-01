import json
from hashlib import sha256
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import jsonify, request

from wsgi import app


class Blockchain(object):
    def __init__(self, genesis_proof=100, genesis_hash='1'):
        self.chain = []  # ledger
        self.current_transactions = []
        self.nodes = set()

        # create the genesis block
        self.new_block(genesis_proof, genesis_hash)

    def new_block(self, proof, previous_hash=None):
        # reset the current transaction list
        self.current_transactions = []

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1

        return proof

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            # check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        # looking for chains longer than ours
        max_length = len(self.chain)

        # grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))
            if response.status_code == 200:
                data = response.json()
                length = data['length']
                chain = data['chain']

                # check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = '{}{}'.format(last_proof, proof).encode()
        round1 = sha256(guess).digest()
        round2 = sha256(round1).hexdigest()
        return round2[:4] == '0000'

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()


blockchain = Blockchain()
node_identifier = uuid4().hex


@app.route('/mine')
def mine():
    # run the proof of work algorithm
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(sender='0', recipient=node_identifier, amount=1)
    block = blockchain.new_block(proof)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response)


@app.route('/chain')
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response)


@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    # check required fields
    values = request.get_json()
    required = ('sender', 'recipient', 'amount')
    if not all(k in values for k in required):
        return 'Missing values', 400

    # run the proof of work algorithm
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    blockchain.new_block(proof)

    response = {'message': 'Transaction will be added to Block {}'.format(index)}
    return jsonify(response), 201


@app.route('/nodes/register', methods=['GET', 'POST'])
def register_nodes():
    if request.method == 'GET':
        response = {
            'nodes': list(blockchain.nodes)
        }
        return jsonify(response)
    else:
        values = request.get_json()
        nodes = values.get('nodes')
        if nodes is None:
            return 'Error: Please supply a valid list of nodes', 400

        for node in nodes:
            blockchain.register_node(node)

        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(blockchain.nodes)
        }
        return jsonify(response), 201


@app.route('/nodes/resolve')
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response)
