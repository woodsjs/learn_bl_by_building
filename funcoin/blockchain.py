class Blockchain(object):
    def __init__ (self):
        self.chain = []
        self.pending_transactions =  []

    def new_block(self):
        #generates new block and adds it to the chain
        pass

    @staticmethod
    def hash(block):
        # hashes the block
        pass

    def last_block(self):
        #gets the latest block in the chain
        pass

    def new_transaction(self, sender, recipient, amount):
        # adds a new transaction to the list of pending transactions
        self.pending_transactions.append({
            "recipient": recipient,
            "sender": sender,
            "amount": amount,
        })