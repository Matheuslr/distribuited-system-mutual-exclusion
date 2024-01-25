import socket
import sys
import logging
import threading
import queue

from random import randrange
from time import sleep
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s'
)

socket.setdefaulttimeout(5)
class Node:
    def __init__(self, server_host: str = 'server', server_port: int = 80) -> None:

        self._device_id = int(sys.argv[1])
        # self._device_id = 2
        self._hostname = socket.gethostname()
        self._IPAddr = socket.gethostbyname(self._hostname)
        self.server_host = server_host
        self.server_port = server_port

        self.server_address = (self.server_host, self.server_port)

        self.node_election_id = 2
   
        # self.node_election_host = "localhost"
        # self.node_election_port = 8081
        self.node_election_host = f"node-{self.node_election_id}"
        self.node_election_port = 80
        self.node_election_address = (self.node_election_host, self.node_election_port)
        self.node_neighbors = []

        self.is_elected = False

        self.message_queue = queue.Queue()

    
        self._set_elected_node()

    def _set_elected_node(self):
        if self.node_election_id == self._device_id:
            self.is_elected = True
        self.node_election_host = f"node-{self.node_election_id}"

    def process_queue(self):
        while True:
            data = self.message_queue.get()
            self.send_message(data)
    def elect_new_leader(self):
        logging.info("Setting new election")
    def _data_format(self,data):
        message_splited = data.split('>')
        return message_splited[0].replace('<','').replace('>', '').replace(' ', ''), message_splited[1]
    def init_leader_server(self):

        data_payload = 2048  # The maximum amount of data to be received at once
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        # Enable reuse address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        logging.info(
            f"Starting up echo server  on {self._IPAddr} port {self.server_port}")
        sock.bind(self.node_election_address)
        # Listen to clients, argument specifies the max no. of queued connections
        sock.listen(5)
        while self.is_elected:
            logging.info("Waiting to receive message from client")
            client, _ = sock.accept()
            data = client.recv(data_payload)
            decoded_message = data.decode('utf-8')
            message_type, message = self._data_format(decoded_message)
            if data and message_type == 'SAVE':
                self.message_queue.put(message)
                client.send(data)
                client.close()


    def send_message(self, data = None):

        logging.info("starting send message process")
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        # Connect the socket to the server
        if self.is_elected:
            sock.connect(self.server_address)
        else:
            sock.connect(self.node_election_address)
            
        # Send data
        try:
            # Send data
            if data:
                message = data
            else:
                message = f"<SAVE>device_id = {self._device_id} | hostname = {self._hostname} | ip = {self._IPAddr} | timestamp = {datetime.now()}"
            logging.info(f"Sending {message}")
            sock.sendall(message.encode('utf-8'))
            # Look for the response
            amount_received = 0
            amount_expected = len(message)
            while amount_received < amount_expected:
                data = sock.recv(16)
                amount_received += len(data)
        except socket.error as err:
            logging.error(f"Timeout: {str(err)}")
        except Exception as err:
            logging.error(f"Other exception: {str(err)}")
        finally:
            logging.info("Closing connection to the server")
            sock.close()
            sleep(randrange(1, 5))


# node = Node('localhost', 8000)
node = Node()
for _ in range(100):
    while True:
        try:
            if node.is_elected:

                logging.info("starting processing thread")
                processing_thread = threading.Thread(target=node.process_queue)
                processing_thread.daemon = True

                logging.info("starting server thread")
                server_thread = threading.Thread(target=node.init_leader_server)
                server_thread.daemon = True

                processing_thread.start()
                server_thread.start()

                processing_thread.join()
                server_thread.join()

            else:
                node.send_message()
        except Exception as err:
            logging.error(err)
            logging.info(f"retrying node {node._device_id}")
            node.elect_new_leader()
            continue
        break
