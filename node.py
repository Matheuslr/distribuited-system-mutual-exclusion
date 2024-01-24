import socket
from random import randrange
from time import sleep
from datetime import datetime

import sys
def client(host = 'server', port=80): 
  device_id = sys.argv[1]
  hostname = socket.gethostname()
  IPAddr = socket.gethostbyname(hostname)
  # Create a TCP/IP socket 
  for i in range(100):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    # Connect the socket to the server 
    server_address = (host, port) 
    print ("Connecting to %s port %s" % server_address) 
    sock.connect(server_address) 
    # Send data 
    try: 
        # Send data 
        message = f"device_id = {device_id} | hostname = {hostname} | ip = {IPAddr} | timestamp = {datetime.now()}" 
        print ("Sending %s" % message) 
        sock.sendall(message.encode('utf-8')) 
        # Look for the response 
        amount_received = 0 
        amount_expected = len(message) 
        while amount_received < amount_expected: 
            data = sock.recv(16) 
            amount_received += len(data) 
            print ("Received: %s" % data) 
    except socket.error as e: 
        print ("Socket error: %s" %str(e)) 
    except Exception as e: 
        print ("Other exception: %s" %str(e)) 
    finally: 
        print ("Closing connection to the server") 
        sock.close() 
        sleep(randrange(1,5))

client()