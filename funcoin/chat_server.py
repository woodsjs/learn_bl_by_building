import asyncio
from email import message
from textwrap import dedent


class ConnectionPool:
    def __init__(self) -> None:
        self.connection_pool = set()

    def send_welcome_message(self, writer):
        """
        sends welcome message to newely connected client
        """
        message = dedent(
            f"""
        ===
        Welcome {writer.nickname}!
        
        There are {len(self.connection_pool) - 1 } user(s) here beside you
        
        Help:
        - Type anything to chat
        - /list will list the connected users
        - /quit will disconnect you
        ===
        """)

        writer.write(f"{message}\r\n".encode())

    def broadcast(self, writer, message):
        """
        Broadcasts message to entire pool
        """

        for user in self.connection_pool:
            if user != writer:
                # don't broadcast the message to self
                user.write(f"{message}\r\n".encode())

    def broadcast_user_join(self, writer):
        """
        calls broadcast method with a user joining message
        """
        self.broadcast(writer, f"{writer.nickname} just joined.")

    def broadcast_user_quit(self, writer):
        """
        calls broadcast method with a user quitting message
        """
        self.broadcast(writer, f"{writer.nickname} just quit.")

    def broadcast_new_message(self, writer, message):
        """
        calls broadcast method with user chat message
        """
        self.broadcast(writer, f"[{writer.nickname}] {message}")

    def list_users(self, writer):
        """
        list all users in pool
        """
        message = "===\r\n"
        message += "Currently connected users: "
        for user in self.connection_pool:
            if user == writer:
                message += f"\r\n - {user.nickname} (you)"
            else:
                message += f"\r\n - {user.nickname}"

        message += "\r\n==="
        writer.write(f"{message}\r\n".encode())

    def add_new_user_to_pool(self, writer):
        """
        adds user to existing pool
        """
        self.connection_pool.add(writer)

    def remove_user_from_pool(self, writer):
        """
        removes exiting user from pool
        """
        self.connection_pool.remove(writer)


async def handle_connection(reader, writer):
    writer.write("> Choose your nickname: ".encode())

    response = await reader.readuntil(b"\r\n")
    writer.nickname = response.decode('utf-8', 'ignore').strip()

    connection_pool.add_new_user_to_pool(writer)
    connection_pool.send_welcome_message(writer)

    connection_pool.broadcast_user_join(writer)

    while True:
        try:
            data = await reader.readuntil(b"\r\n")
        except asyncio.exceptions.IncompleteReadError:
            connection_pool.broadcast_user_quit(writer)
            break

        message = data.decode().strip()
        if message == "/quit":
            connection_pool.broadcast_user_quit(writer)
            break
        elif message == "/list":
            connection_pool.list_users(writer)
        else:

            connection_pool.broadcast_new_message(writer, message)

        await writer.drain()

        if writer.is_closing():
            break

    writer.close()
    await writer.wait_closed()

    connection_pool.remove_user_from_pool(writer)


async def main():
    server = await asyncio.start_server(handle_connection, "0.0.0.0", 8888)

    async with server:
        await server.serve_forever()

connection_pool = ConnectionPool()

asyncio.run(main())
