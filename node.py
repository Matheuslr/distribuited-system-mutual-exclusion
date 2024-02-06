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
    format='[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s'
)


class Node:
    def __init__(self, server_host: str = 'server', server_port: int = 80) -> None:

        self._device_id: int = int(sys.argv[1])

        self.node_list: list = [int(x) for x in sys.argv[2].split(",")]
        self._hostname: str = socket.gethostname()
        self._IPAddr: str = socket.gethostbyname(self._hostname)
        self.server_host: str = server_host
        self.server_port: int = server_port
        self._message_quantity: int = 1000
        self.server_address: Tuple(str,int) = (self.server_host, self.server_port)

        self.node_election_id: int = 4

        self.node_election_host: str = f"node-{self.node_election_id}"
        self.node_election_port: int = 80
        self.node_election_address: Tuple(str,int) = (
            self.node_election_host, self.node_election_port)
        self.node_address: Tuple(str,int) = (
            f"node-{self._device_id}", self.node_election_port)
   
        self.is_elected: bool = False

        self.elections_started: bool = False

        self.message_queue: queue = queue.Queue()

        self._set_elected_node()

    def _set_elected_node(self) -> None:
        """
            set a initial elected node
        """
        if self.node_election_id == self._device_id:
            self.is_elected = True
        self.node_election_host = f"node-{self.node_election_id}"

    def _promote_node(self, node: int) -> None:
        """
        Promote a new node as leader

        Args:
            node (int): node to be elected
        """
        logging.info(f"promoting node {node} to leader")
        self.node_election_id = node
        if self.node_election_id == self._device_id:
            self.is_elected = True
        self.node_election_host = f"node-{self.node_election_id}"
        self.node_election_address= (
            self.node_election_host, self.node_election_port)
        self.elections_started = False
        logging.info(f"node {node} has been promoted")
        logging.info(f"node_election_id = {self.node_election_id} | node_election_address = {self.node_election_address} | is_elected = {self.is_elected}")
    
    def process_queue(self) -> None:
        """
        Queue processer for elected node 
        """
        while True:
            data = self.message_queue.get()
            self._send_message(message=data)

    def elect_new_leader(self) -> None:
        """
        Start a election for Election Ring Algorithm
        """
        
        if self.elections_started == False:
            logging.info("electing new leader")
            self.elections_started = True
            self.is_who_started_a_election = True
            self.node_list.remove(self.node_election_id)
            next_node = self.node_list[0]
            custom_addr = (
                f"node-{next_node}", self.node_election_port)
            message = f"<ELECTION>{self._device_id},{next_node}"
            logging.info(f"send election message: {message} to {custom_addr}")
            self._send_message(message=message, custom_addr=custom_addr)

    def do_election(self, message: str) -> None:
        """
        Do the process of a election. Send a ELECTION message to actual node neighbour. 
        When all neighbours has been reached, send a LEADER message to all other nodes, telling who is the new leader

        Args:
            message (str): message containing the voting list
        """
        logging.info("Ongoing election")
        self.elections_started = True
        if self.node_election_id in self.node_list:
            self.node_list.remove(self.node_election_id)
        voting_list = [int(x) for x in message.split(",")]

        if self.node_election_id not in voting_list:
            missing_nodes = list(set(self.node_list) - set(voting_list))
            next_node = voting_list[0]

            if missing_nodes:
                next_node = missing_nodes[0]

            if str(self._device_id) in message and voting_list.count(self._device_id) > 1:
                logging.info("Setting a Leader")
                leader = max(voting_list)

                message = f"<LEADER>{leader}"
                custom_addr = (
                            f"node-{leader}", self.node_election_port)

                self._send_message(
                    message=message,
                    custom_addr=custom_addr
                )
                logging.info(f"node {leader} knows he is a leader")
                for node_id in voting_list:
                    if node_id != self._device_id and node_id != leader: 
                        custom_addr = (
                            f"node-{node_id}", self.node_election_port)
                        logging.info(f"sending {message} to {custom_addr}")
                        self._send_message(
                            message=message,
                            custom_addr=custom_addr
                        )
                self._promote_node(leader)

            else:
                if next_node != self._device_id:
                    sending_message = f"<ELECTION>{message},{next_node}"
                    custom_addr = (
                        f"node-{next_node}", self.node_election_port)
                    logging.info(f"sending {sending_message} to {custom_addr}")
                    self._send_message(message=sending_message,custom_addr=custom_addr)
                    
    def _data_format(self, data: str) -> Tuple[str,str]:
        """Format recived message

        Args:
            data (str): Unformated message

        Returns:
            Tuple[str,str]: (message type, message)
        """

        message_splited = data.split('>')
        return message_splited[0].replace('<', '').replace('>', '').replace(' ', ''), message_splited[1]

    def init_node_server(self) -> None:
        """
        Start a listening server for the actual node. This server is waiting for three commands:

            SAVE: If this node is a leader, it can save data on the main server. When this node receives a message, it will send it to a queue processor.
            ELECTION: If this node receives this message, it will start an election step, attempting to find a neighboring node.
            LEADER: If this node receives this message, it will set a new leader, using the message to set it.

        """
        data_payload = 2048  

        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        logging.info(
            f"Starting up echo server  on {self.node_address}")
        sock.bind(self.node_address)

        sock.listen(5)
        while True:
            try:
                logging.info("Waiting to receive message from client")
                client, _ = sock.accept()
                data = client.recv(data_payload)
                decoded_message = data.decode('utf-8')
                message_type, message = self._data_format(decoded_message)
                logging.info(f"node-{self._device_id} recived a message: {message_type} - {message}")

                if data and self.is_elected and message_type == 'SAVE':
                    self.message_queue.put(message)
                if data and message_type == 'ELECTION':
                    self.elections_started = True
                    self.do_election(message=message)
                if data and message_type == 'LEADER' and self.elections_started == True:
                    self._promote_node(int(message))
                client.send(data)
                client.close()
            except Exception as err:
                logging.error(traceback.format_exc())
                logging.error(err)

    def _send_message(self, message: str = '', custom_addr: Tuple[str, int] = ()) -> None:
        """
        Send a message using a socket connection 

        Args:
            message (str, optional): message to send. Defaults to ''.
            custom_addr (Tuple[str, int], optional): (adress, port). Defaults to ().
        """
        logging.info("starting send message process")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            if self.is_elected:
                sock.connect(self.server_address)
            elif len(custom_addr) > 0:
                sock.connect(custom_addr)
            else:
                sock.connect(self.node_election_address)
            logging.info(f"Sending {message}")
            sock.sendall(message.encode('utf-8'))
            amount_received = 0
            amount_expected = len(message)
            while amount_received < amount_expected:
                data = sock.recv(16)
                amount_received += len(data)  
        except socket.error as err:
            logging.error(f"Timeout: Tryed to send to:{sock.getsockname()} error: {str(err)}")
            node.elect_new_leader()
        except Exception as err:
            logging.error(f"Other exception: {str(err)}")
        finally:
            logging.info("Closing connection to the server")
            sock.close()

    def message_spam(self) -> None:
        """
            if this node is not the actual leader, span messages to the node leader
        """
        if not self.is_elected and not self.elections_started :
            for _ in range(self._message_quantity):
                message = f"<SAVE>device_id = {self._device_id} | hostname = {self._hostname} | ip = {self._IPAddr} | timestamp = {datetime.now()} | leader = {self.node_election_id}"
                if self.node_election_id in self.node_list and not self.elections_started and not self.is_elected :
                    self._send_message(message=message)
                sleep(randrange(1, 10))

node = Node()


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