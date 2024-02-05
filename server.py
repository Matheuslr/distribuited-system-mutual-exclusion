import socket
import os
import logging

from typing import BinaryIO, Tuple

logging.basicConfig(level=logging.INFO)


class Server:
    def __init__(self, server_host: str = 'server', server_port: str = 80) -> None:
        self._hostname: str = socket.gethostname()
        self._IPAddr: str = socket.gethostbyname(self._hostname)

        self.server_host: str = server_host
        self.server_port: int = server_port
        self.server_address: Tuple(str,int) = (self.server_host, self.server_port)

        self.folder: str = "files"
        self.file: str = "logs.txt"
        self.path: str = os.path.join(self.folder, self.file)

        self._create_file()

    def _create_file(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        with open(self.path, 'w') as _:
            pass

    def _write_on_logs(self, data:BinaryIO):
        with open(self.path, '+a') as file:
            file.write(f"{data.decode('utf-8')}\n")
        logging.info('data saved on log file')

    def init_server(self):

        data_payload = 2048  # The maximum amount of data to be received at once
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        # Enable reuse address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        logging.info(
            f"Starting up echo server  on {self._IPAddr} port {self.server_port}")
        sock.bind(self.server_address)
        # Listen to clients, argument specifies the max no. of queued connections
        sock.listen(5)
        while True:
            logging.info("Waiting to receive message from client")
            client, _ = sock.accept()
            data = client.recv(data_payload)
            if data:
                self._write_on_logs(data)
                client.send(data)
                client.close()


# server = Server('localhost', 8000)
server = Server()
server.init_server()
