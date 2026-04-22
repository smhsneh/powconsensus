import hashlib
import time
import json


class Block:
    def __init__(self, index, transactions, previous_hash, difficulty=4):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self.mine()

    def compute_hash(self):
        block_content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_content.encode()).hexdigest()

    def mine(self):
        target = "0" * self.difficulty
        while True:
            self.hash = self.compute_hash()
            if self.hash.startswith(target):
                return self.hash
            self.nonce += 1

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "difficulty": self.difficulty
        }


class Blockchain:
    def __init__(self, difficulty=4):
        self.difficulty = difficulty
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(
            index=0,
            transactions=["genesis block"],
            previous_hash="0" * 64,
            difficulty=self.difficulty
        )
        self.chain.append(genesis)

    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        if not self.pending_transactions:
            return None

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions,
            previous_hash=self.last_block().hash,
            difficulty=self.difficulty
        )
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # recompute hash and compare
            if current.hash != current.compute_hash():
                return False

            # check linkage
            if current.previous_hash != previous.hash:
                return False

            # verify pow target is met
            if not current.hash.startswith("0" * self.difficulty):
                return False

        return True

    def to_dict(self):
        return [block.to_dict() for block in self.chain]