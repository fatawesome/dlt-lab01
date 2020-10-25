from hashlib import sha256
import json
import time


class Block:
    def __init__(self, index, transactions, timestamp, pred_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.pred_hash = pred_hash
        self.hash = None  # to be calculated in add_block
        self.nonce = nonce  # to be calculated in proof_of_work

    def compute_hash(self):
        block_serialized = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_serialized.encode()).hexdigest()


class Blockchain:
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def __str__(self):
        return str(self.chain)

    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @staticmethod
    def pow(block):
        block.nonce = 0
        block_hash = block.compute_hash()
        while not block_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            block_hash = block.compute_hash()
        return block_hash

    def add_block(self, block, proof):
        pred_hash = self.last_block.hash

        if pred_hash != block.pred_hash:
            return False
        if not Blockchain.is_proof_valid(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @classmethod
    def is_proof_valid(cls, block, block_hash):
        """
        Check that hash is valid and satisfies difficulty criterion.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          pred_hash=last_block.hash)

        proof = self.pow(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

    @classmethod
    def is_chain_valid(cls, chain):
        """
        Check if the entire blockchain is valid.
        """
        res = True
        pred_hash = '0'

        for block in chain:
            block_hash = block.hash
            delattr(block, 'hash')

            if not cls.is_proof_valid(block, block.hash) or \
                    pred_hash != block.pred_hash:
                res = False
                break

            block.hash, pred_hash = block_hash, block_hash

        return res
