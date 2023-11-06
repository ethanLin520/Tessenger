import sys
import socket
import select

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
        # Use select to wait for input from stdin and data from the server simultaneously
        readable, _, _ = select.select([sys.stdin, s], [], [], 1)

        if s in readable:
            # Data from the server is available
            data = s.recv(1024)
            if not data:
                print("Connection closed by the server.")
                sys.exit(0)

            prompt = data.decode()
            print(prompt, end='', flush=True)
            if 'Welcome' in prompt:
                s.sendall(f"{client_udp_port}".encode())

        if sys.stdin in readable:
            # User input is available
            user_input = sys.stdin.readline().strip()
            s.sendall(user_input.encode())
