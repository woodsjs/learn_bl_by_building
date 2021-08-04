import json
# yuk, use secrets
import random

from datetime import datetime
from hashlib import sha256

class Blockchain(object):
    def __init__ (self):
        self.chain = []
        self.pending_transactions =  []

        # if we're creating a new blockchain object, we're creating a new blockchain
        # In this case, we want to create the genesis block
        print('Creating genesis block.')
        self.chain.append(self.new_block())

    def new_block(self):
        #generates new block and adds it to the chain
        # do we have to process the pending transactions in any way before they are added?
        # assuming that this is where the Merkel tree comes in later

        previous_block = self.last_block()
        block = {
            'index': len(self.chain),
            'timestamp': datetime.utcnow().isoformat(),
            'transactions': self.pending_transactions,
            'previous_hash': previous_block["hash"] if previous_block else None,
            'nonce': format(random.getrandbits(64), "x"),
        }

        # let's hash this new block, and add the hash to the block
        block_hash = self.hash(block)
        block["hash"] = block_hash
        # print(block["hash"])
        # clear out the list of pending transactiions
        # is there processing that needs to go on here before we clear these out?
        # self.pending_transactions = []

        #add this block to the chain
        # self.chain.append(block)
        # print(block["nonce"])
        return block

    @staticmethod
    def hash(block):
        # hashes the block
        # we need to sort the dictionary, otherwise  we'll have inconsistant hashes
        block_string = json.dumps(block, sort_keys=True).encode()

        return sha256(block_string).hexdigest()

    def last_block(self):
        #gets the latest block in the chain
        return self.chain[-1] if self.chain else None

    def new_transaction(self, sender, recipient, amount):
        # adds a new transaction to the list of pending transactions
        self.pending_transactions.append({
            "recipient": recipient,
            "sender": sender,
            "amount": amount,
        })

    @staticmethod
    def valid_block_hash(block):
        return block["hash"].startswith("0000")

    def proof_of_work(self):
        while True:
            new_block = self.new_block()
            if self.valid_block_hash(new_block):
                break
        
        self.pending_transactions = []

        self.chain.append(new_block)
        print("Found new valid block at: ", new_block)
    

        
