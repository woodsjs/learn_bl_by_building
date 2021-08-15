import asyncio

import structlog

from funcoin.messages import (
    create_peers_message,
    create_block_message,
    create_transaction_message,
    create_ping_message
)
from funcoin.transactions import validate_transaction

logger = structlog.getLogger(__name__)

class P2PError(Exception):
    pass

class P2PProtocol:
    def __init__(self, server) -> None:
        self.server = server
        self.blockchain = server.blockchain
        self.connection_pool = server.connection_pool

    @staticmethod
    async def send_message(writer, message):
        writer.write(message.encode() + b"\n")

    async def handle_message(self, message, writer):
        message_handlers = {
            "block": self.handle_block,
            "ping": self.handle_ping,
            "peers": self.handle_peers,
            "transaction": self.handle_transaction,
        }

        handler = message_handlers.get(message["name"])

        if not handler:
            raise P2PError("Missing handler for message")

        await handler(message, writer)

    """
        This is used when a new peer is on the network and pings, like hey I'm here!
        When we see that we send it our top 20 alive peers so it has some more to ping

        We also see if it has all of the blocks we do. If it doesn't we gather them up and 
        send them over

    """
    async def handle_ping(self, message, writer):
        # initial data gathering, we'll use these soon
        block_height = message["payload"]["block_height"]
        writer.is_miner = message["payload"]["is_miner"]

        # let this new peer that's pinging us know who else is out there
        peers = self.connection_pool.get_alive_peers(20)
        peers_message = create_peers_message(self.server.external_ip, self.server.external_port, peers)
        await self.send_message(writer, peers_message)

        # Is this peer all caught up? if not gather all of the blocks they don't have and ship them over
        # TODO: we need to revisit the blockchain.last_block item, it's not built right on our end
        if block_height < self.blockchain.last_block["height"]:
            for block in self.blockchain.chain[block_height + 1:]:
                await self.send_message(writer, create_block_message(self.server.external_ip, self.server.external_port, block))

    """
        Pop that transaction on the stack, if it's good
    """
    async def handle_transaction(self, message, writer):
        logger.info("Received transaction")
        tx = message["payload"]

        if validate_transaction(tx) is True:
            if tx not in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.append(tx)

                for peer in self.connection_pool.get_alive_peers(20):
                    await self.send_message(peer, create_transaction_message(self.server.external_ip, self.server.external_port, tx))
        else:
            logger.warning("Received invalid transaction")

    """
        If we receive a block that we don't have, we're popping it on the stack.

        In addition, we forward this off to other's who might not have it.

        Where's the check for this block though?  We're essentially blindly adding a new block
        without knowing if it's bunk, or if we have it
    """
    async def handle_block(self, message, writer):
        logger.info('Received new block')
        block = message["payload"]

        self.blockchain.add_block(block)

        for peer in self.connection_pool.get_alive_peers(20):
            await self.send_message(peer, create_block_message(self.server.external_ip, self.server.external_port, block))

    """
        We received a peers message, which is just alist of more peers.

        Let's add them to our peers list, and send a ping over to each of them so they know I exist.

        In addition we can send them the peers we have

        I have a feeling this will be noisy if we don't just send to peers we don't have. Because
        when I send my ping out, they're gong to send a peers message back, then I'm going to run this code again,
        ad infinitim

        Ok, so maybe we just update the last_seen in our data, but so far we don't have that?
    """
    async def handle_peers(self, message, writer):
        logger.info("Received new peers")
        peers = message["payload"]

        ping_message = create_ping_message(self.server.external_ip, self.server.external_port, len(self.blockchain.chain), len(self.connection_pool.get_alive_peers(50)), False)

        for peer in peers:
            reader, writer = await asyncio.open_connection(peer["ip"], peer["port"])

            self.connection_pool.add_peer(writer)

            await self.send_message(writer, ping_message)
