import socket
import pickle

port = 12345

# Get the local IP address automatically
ip = "192.168.79.119"

# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = (ip, port)
s.bind(server_address)
print("Do Ctrl+C to exit the program !!")

while True:
    print("####### Server is listening #######")
    data, address = s.recvfrom(4771)
    decoded_data = pickle.loads(data)
    print("\n\n 2. Server received: ", decoded_data, "\n\n")
