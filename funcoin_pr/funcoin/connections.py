import structlog
from more_itertools import take

logger = structlog.getLogger(__name__)

class ConnectionPool:
    def __init__(self) -> None:
        self.connection_pool = dict()

    def broadcast(self, message):
        for user in self.connection_pool:
            user.write(f"{message}".encode())

    @staticmethod
    def get_address_string(writer):
        ip = writer.address["ip"]
        port = writer.address["port"]
        return f"{ip}:{port}"

    def add_peer(self, writer):
        address = self.get_address_string(writer)

        self.connection_pool[address] = writer

        logger.info("Added peer to pool", address=address)

    def remove_peer(self, writer):
        address = self.get_address_string(writer)
        self.connection_pool.pop(address)

        logger.info("Removed peer from pool", address=address)

    def get_live_peers(self, count):
        return take(count, self.connection_pool.items())