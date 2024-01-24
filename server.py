import socket
import os

# Define o caminho do arquivo e da pasta


def create_file(path: str, folder):
  if not os.path.exists(folder):
    os.makedirs(folder)

  with open(path, 'w') as file:
      pass  

def write_on_logs(path: str, data: str):
    with open(path, '+a') as file:
      file.write(f"{data.decode('utf-8')}\n")
    print('data saved on log file')

def server(host = 'server', port=80):
    folder = "files"
    file = "logs.txt"
    path = os.path.join(folder, file)
    create_file(path, folder)
    data_payload = 2048 #The maximum amount of data to be received at once
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
    # Enable reuse address/port 
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the port
    server_address = (host, port)
    print ("Starting up echo server  on %s port %s" % server_address)
    sock.bind(server_address)
    # Listen to clients, argument specifies the max no. of queued connections
    sock.listen(5) 
    while True: 
        print ("Waiting to receive message from client")
        client, address = sock.accept() 
        data = client.recv(data_payload) 
        if data:
            write_on_logs(path, data)
            client.send(data)
            print (f"sent {data} bytes back to {address}" )
            # end connection
            client.close()  
server()