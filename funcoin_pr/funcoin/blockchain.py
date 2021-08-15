import asyncio
import json
import math
# yuk, use secrets
import random

from datetime import datetime, time
from hashlib import sha256

import structlog
logger = structlog.getLogger("blockchain")

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.target = "000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        # if we're creating a new blockchain object, we're creating a new blockchain
        # In this case, we want to create the genesis block
        logger.info('Creating genesis block.')
        self.chain.append(self.new_block())

    def new_block(self):
        # gathers data for new block, and sends call to create_block to get the actual block back
        # do we have to process the pending transactions in any way before they are added?
        # assuming that this is where the Merkel tree comes in later

        previous_block = self.last_block()
        block = self.create_block(
            height=len(self.chain),
            transactions = self.pending_transactions,
            previous_hash=previous_block["hash"] if previous_block else None,
            nonce=format(random.getrandbits(64), "x"),
            target = self.target,
            timestamp = datetime.utcnow().isoformat()
        )
            # 'index': len(self.chain),
            # 'timestamp': datetime.utcnow().isoformat(),
            # 'transactions': self.pending_transactions,
            # 'previous_hash': previous_block["hash"] if previous_block else None,
            # 'nonce': format(random.getrandbits(64), "x"),


        # let's hash this new block, and add the hash to the block
        # block_hash = self.hash(block)
        # block["hash"] = block_hash
        # print(block["hash"])
        # clear out the list of pending transactiions
        # is there processing that needs to go on here before we clear these out?
        # self.pending_transactions = []

        #add this block to the chain
        # self.chain.append(block)
        # print(block["nonce"])
        return block

    @staticmethod
    def create_block(height, transactions, previous_hash, nonce, target, timestamp=None):
        # all this does is add the hash to our block, which was actually created in new_block

        block = {
            "height": height,
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce,
            "target": target,
            "timestamp": timestamp or time(),
        }

        # block_string = json.dumps(block, sort_keys=True).encode()
        # block["hash"] = sha256(block_string).hexdigest()
        block["hash"] = hash(block)

        return block

    def add_block(self, block):
        self.chain.append(block)

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
    
    def validate_block_hash(self, block):
        return block["hash"] < self.target

    def recalculate_target(self, block_index):
        # "At a certain threshold, the block target needs to change to get a new difficulty"
        # we need to understand this more, but it's not well explained in the text
        # like the ratio part. How did we come up with those values and how does that work?

        if block_index % 10 == 0:

            # 10 block timespan. But why are we multiplying it by 10?
            # is it 10 blocks, with each block 10 minutes?
            expected_timespan = 10 * 10

            # calculate the diff of the time of the last block compared to the time of the block 10 blocks ago
            actual_timespan = self.chain[-1]["timestamp"] - self.chain[-10]["timestamp"]

            # if we're on target, that is it's taking as much time to calculate 10 blocks as we would like,
            # our ratio will be 1. If that ratio is under 1, then it's moving too quickly.
            # if that ratio is greater than 1, then it's moving too slowly
            #
            # down the line, we take that ratio and , since we want the block to be UNDER the target, if it's 
            # too slow (ratio greater than 1), we increase the target to make it easier to hit the target.
            # by increasing the target, we create a LARGER EASIER TO HIT TARGET that should speed things up.

            ratio = actual_timespan / expected_timespan

            # We don't want to make the target too small or our difficulty will be off the hook. 
            # So if our ratio is under 0.25, in the case of a 100 minute target for 10 blocks that would be under 25 minutes,
            # we adjust up to 0.25 but go no lower. 
            # this effectively shrinks the target from say 1000 digits to 250 digits.
            ratio = max(0.25, ratio)

            # coversly, we don't want the target too large or it will become so easy to mine that we would have a gold rush,
            # so if our ratio is over 4.0, in the case of a 100 minute target for 10 blocks taht would be over 400 minutes,
            # we adjust down to 4.0 but go no higher.
            # this effectively increases the target from 1000 digits to 4000 digits.
            ratio = min(4.00, ratio)

            # the above ratios make sure that we only change our target by at most 25%-400%. Going under 100% makes the 
            # target harder to hit since it will be smaller.  Going over 100% makes the target easier to hit since it will
            # be larger
            new_target = int(self.target, 16) * ratio

            self.target = format(math.floor(new_target), "x").zfill(64)
            logger.info(f"Calculated new target: {self.target}")

        return self.target

    async def get_blocks_after_timestamp(self, timestamp):
        for index, block in enumerate(self.chain):
            if timestamp < block["timestamp"]:
                return self.chain[index:]

    async def mine_new_block(self):
        # it looks like we want to recalculate the target if the NEXT
        # block is a multiple of 10.  This code does not make that obvious
        # unless we read the code for recalculate_target.  This is ugly.
        # We should just pass in the last blocks index and let recalculate target
        # worry about that detail.
        last_block = self.last_block()
        last_block_index = last_block["index"] if last_block else None
        self.recalculate_target(last_block_index + 1)

        while True:
            new_block = self.new_block()

            # maybe this function should be validate_block or validate_block_hash_meets_target or something?
            if self.validate_block_hash(new_block):
                break
            else: 
                # allow other waiting tasks to run before we try again
                await asyncio.sleep(0)

        # the correct way to clear out pending transactions
        self.pending_transactions = []

        # why don't we do this in the while loop above?  We have a valid block, append it and break?
        self.chain.append(new_block)
        logger.info("Found new valid block at: ", new_block)
