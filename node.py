import socket
import sys
import logging
import threading
import queue
import traceback

from random import randrange
from time import sleep
from datetime import datetime

from typing import Tuple

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s'
)


class Node:
    def __init__(self, server_host: str = 'server', server_port: int = 80) -> None:

        self._device_id: int = int(sys.argv[1])
        # self._device_id = 4

        self.node_list: list = [int(x) for x in sys.argv[2].split(",")]
        self._hostname: str = socket.gethostname()
        self._IPAddr: str = socket.gethostbyname(self._hostname)
        self.server_host: str = server_host
        self.server_port: int = server_port
        self._message_quantity: int = 100
        self.server_address: Tuple(str,int) = (self.server_host, self.server_port)

        self.node_election_id: int = 4

        # self.node_election_host = "localhost"
        # self.node_election_port = 8081
        self.node_election_host: str = f"node-{self.node_election_id}"
        self.node_election_port: int = 80
        self.node_election_address: Tuple(str,int) = (
            self.node_election_host, self.node_election_port)
        self.node_address: Tuple(str,int) = (
            f"node-{self._device_id}", self.node_election_port)
        # self.node_address: Tuple(str,int) = (
        #     f"localhost", 8001)
        self.is_elected: bool = False

        self.elections_started: bool = False
        self.actual_election_sending_node: int = -1

        self.message_queue: queue = queue.Queue()

        self._set_elected_node()

    def _set_elected_node(self):
        if self.node_election_id == self._device_id:
            self.is_elected = True
        self.node_election_host = f"node-{self.node_election_id}"
    
    def _promote_node(self, leader):
        logging.info("promoting leader")
        self.node_election_id = leader
        self.node_election_host = f"node-{self.node_election_id}"
        if self.node_election_id == self._device_id:
            self.is_elected = True

    def process_queue(self):
        while True:
            data = self.message_queue.get()
            self._send_message(message=data)

    def elect_new_leader(self):
        logging.info("electing new leader")
        self.elections_started = True
        self.actual_election_sending_node = self.node_list[0]
        self.node_list.remove(self.node_election_id)
        custom_addr = (
            f"node-{self.node_list[0]}", self.node_election_port)
        message = f"<ELECTION>{self._device_id}"
        logging.info(f"send election message: {message} to {custom_addr}")
        self._send_message(message=message, custom_addr=custom_addr)

    def do_election(self, message):
        logging.info("Ongoing election")
        voting_list = [int(x) for x in message.split(",")]
        logging.info(f"{self.node_election_id} not in {voting_list}: {self.node_election_id not in voting_list}")
        if self.node_election_id not in voting_list:
            missing_nodes = list(set(self.node_list) - set(voting_list))
            next_node = missing_nodes[0]
            self.actual_election_sending_node = next_node
            sending_message = f"<ELECTION>{message},{self._device_id}"
            custom_addr = (
                f"node-{next_node}", self.node_election_port)
            logging.info(f"sending {sending_message} to {custom_addr}")
            self._send_message(message=sending_message,custom_addr=custom_addr)
        else:
            logging.info("Setting a Leader")
            leader = max(self.voting_list)
            broadcast_list = self.voting_list.remove(self._device_id)

            for node in broadcast_list:
                message = sending_message = f"<LEADER>{leader}"
                custom_addr = (
                    f"node-{node}", self.node_election_port)
                self._send_message(
                    sending_message=sending_message,
                    custom_addr=custom_addr
                )

    def _data_format(self, data: str):
        message_splited = data.split('>')
        return message_splited[0].replace('<', '').replace('>', '').replace(' ', ''), message_splited[1]

    def init_node_server(self):

        data_payload = 2048  # The maximum amount of data to be received at once
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        # Enable reuse address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        logging.info(
            f"Starting up echo server  on {self.node_address}")
        logging.info(self.node_address)
        sock.bind(self.node_address)
        # Listen to clients, argument specifies the max no. of queued connections
        sock.listen(5)
        while True:
            try:
                logging.info("Waiting to receive message from client")
                client, _ = sock.accept()
                data = client.recv(data_payload)
                decoded_message = data.decode('utf-8')
                message_type, message = self._data_format(decoded_message)
                logging.info(f"{message_type} - {message}")

                if data and self.is_elected and message_type == 'SAVE':
                    self.message_queue.put(message)
                    
                if data and message_type == 'ELECTION':
                    self.elections_started = True
                    if self._device_id not in [int(x) for x in message.split(",")]:
                        self.do_election(message=message)
                        sleep(5)
                if data and message_type == 'LEADER' and self.elections_started == True:
                    if self._device_id not in message:
                        self.do_election(message=message)
                        self.elections_started = False
                        sleep(5)
                client.send(data)
                client.close()
            except Exception as err:
                logging.error(traceback.format_exc())
                logging.error(err)

    def _send_message(self, message: str = '', custom_addr: Tuple[str, int] = ()):
            logging.info("starting send message process")
            # Create a TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            try:
                if self.is_elected:
                    sock.connect(self.server_address)
                elif len(custom_addr) > 0:
                    sock.connect(custom_addr)
                else:
                    logging.info(self.node_election_address)
                    sock.connect(self.node_election_address)
                # Send data
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
                if not self.elections_started:
                    node.elect_new_leader()
            except Exception as err:
                logging.error(f"Other exception: {str(err)}")
            finally:
                logging.info("Closing connection to the server")
                sock.close()

    def message_spam(self):
        if not self.is_elected and not self.elections_started :
            message = f"<SAVE>device_id = {self._device_id} | hostname = {self._hostname} | ip = {self._IPAddr} | timestamp = {datetime.now()}"
            for _ in range(self._message_quantity):
                if self.node_election_id in self.node_list:
                    self._send_message(message=message)
                    sleep(randrange(1, 5))

node = Node()


while True:
    try:
        logging.info("starting processing thread")
        processing_thread = threading.Thread(target=node.process_queue)
        processing_thread.daemon = True

        logging.info("starting server thread")
        server_thread = threading.Thread(target=node.init_node_server)
        server_thread.daemon = True

        logging.info("starting message_spam thread")
        message_spam_thread = threading.Thread(target=node.message_spam)
        message_spam_thread.daemon = True

        processing_thread.start()
        server_thread.start()
        message_spam_thread.start()

        processing_thread.join()
        server_thread.join()
        message_spam_thread.join()

    except Exception as err:
        logging.error(err)
        logging.info(f"retrying node {node._device_id}")
