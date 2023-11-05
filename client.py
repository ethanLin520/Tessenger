import sys
import socket

# Check if the correct number of arguments is provided
if len(sys.argv) != 4:
    print("Usage: python3 client.py server_IP server_port client_udp_port")
    sys.exit(1)

# Extract command-line arguments
server_IP = sys.argv[1]
server_port = int(sys.argv[2])
client_udp_port = int(sys.argv[3])

# Check if the server port number is valid
if not 1024 <= server_port <= 65535:
    print("Invalid server port number. Please use a port number between 1024 and 65535.")
    sys.exit(1)

# Check if the client UDP port number is valid
if not 1024 <= client_udp_port <= 65535:
    print("Invalid client UDP port number. Please use a port number between 1024 and 65535.")
    sys.exit(1)


# Create a TCP/IP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to server
    s.connect((server_IP, server_port))
    
    print("Connected to the server.")
    
    while True:
        data = s.recv(1024)
        if not data:
            print("Connection closed by the server.")
            break

        prompt = data.decode()

        if 'Welcome' in prompt:
            print(prompt)
            s.sendall(f"{client_udp_port}".encode())
            continue
        elif prompt.endswith('\n'):
            print(prompt, end='')
            continue

        command = input(prompt)
        
        # Send command to the server
        s.sendall(command.encode())
        
