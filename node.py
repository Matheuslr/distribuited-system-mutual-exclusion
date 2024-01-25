import socket
import sys
import logging

from random import randrange
from time import sleep
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class Node:
    def __init__(self, server_host: str = 'server', server_port: str = 80) -> None:
        self._device_id = sys.argv[1]
        self._hostname = socket.gethostname()
        self._IPAddr = socket.gethostbyname(self._hostname)
        self.server_host = server_host
        self.server_port = server_port
        self.server_address = (self.server_host, self.server_port)

        self.node_election_id = 0
        self.node_election_ip = f"node-{self.node_election_id}"
        self.node_neighbors = []

        self.message_list = []
        self.is_elected = False

    def _set_elected_node(self):
        if self.node_election_id == self._device_id:
            self.is_elected = True
        self.node_election_ip = f"node-{self.node_election_id}"

    # TODO server for leader

    def send_message(self):
        logging.info("starting send message process")
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the server
        logging.info(
            f"Starting up echo server  on {self._IPAddr} port {self.server_port}")
        sock.connect(self.server_address)
        # Send data
        try:
            # Send data
            message = f"device_id = {self._device_id} | hostname = {self._hostname} | ip = {self._IPAddr} | timestamp = {datetime.now()}"
            logging.info(f"Sending {message}")
            sock.sendall(message.encode('utf-8'))
            # Look for the response
            amount_received = 0
            amount_expected = len(message)
            while amount_received < amount_expected:
                data = sock.recv(16)
                amount_received += len(data)
        except socket.error as err:
            logging.error(f"Socket error: {str(err)}")
        except Exception as err:
            logging.error(f"Other exception: {str(err)}")
        finally:
            logging.info("Closing connection to the server")
            sock.close()
            sleep(randrange(1, 5))


node = Node()
for _ in range(100):
    while True:
        try:
            node.send_message()
        except:
            logging.info(f"retrying node {node._device_id}")
            continue
        break
