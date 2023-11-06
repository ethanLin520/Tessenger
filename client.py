import re
import sys
import socket
import select
import os

from myconstant import UDP_BUFFER

def send_file_udp(target_ip, target_port, file_path, chunk_size=UDP_BUFFER):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Open the file
        with open(file_path, 'rb') as file:
            # Read and send the file in chunks
            chunk = file.read(chunk_size)
            while chunk:
                udp_sock.sendto(chunk, (target_ip, target_port))
                chunk = file.read(chunk_size)
    except:
        pass
    finally:
        udp_sock.close()

def udp_server(udp_port, buffer_size=UDP_BUFFER):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.bind(('', udp_port))
        print(f"UDP server listening on port {udp_port}")

        while True:
            data, addr = udp_sock.recvfrom(buffer_size)
            if data:
                file_name = data.decode()
                with open(file_name, 'wb') as file:
                    while True:
                        data, addr = udp_sock.recvfrom(buffer_size)
                        if not data:
                            break
                        file.write(data)
                print(f"Received file {file_name} from {addr}")


def read_user_list(txt):
    lines = txt.split('\n')
    pattern = r"(.+), active since (.+). IP address: (.+). UDP port: (.+)"

    result = {}

    for line in lines:
        match = re.match(pattern, line)
        if match:
            user = match.group(1)
            ip = match.group(3)
            port = int(match.group(4))
            result[user] = (ip, port)

    return result

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

active_users = {}

# Create a TCP/IP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to server
    s.connect((server_IP, server_port))
    
    print("Connected to the server.")

    get_list = False

    while True:
        # Use select to wait for input from stdin and data from the server simultaneously
        readable, _, _ = select.select([sys.stdin, s], [], [], 1)

        if s in readable:
            # Data from the server is available
            data = s.recv(1024)
            if not data:
                print("Connection closed by the server.")
                break

            prompt = data.decode()
            print(prompt, end='', flush=True)
            if 'Welcome' in prompt:
                s.sendall(f"{client_udp_port}".encode())
            elif 'Goodbye' in prompt:
                break
            elif get_list:
                active_users = read_user_list(prompt)
                get_list = False

        if sys.stdin in readable:
            # User input is available
            user_input = sys.stdin.readline().strip()

            if user_input.startswith('/p2pvideo'):
                arguments = user_input.split()
                if len(arguments) != 3:
                    print('Usage: /p2pvideo username filename\n')
                    continue

                if not active_users:
                    print('No active users on record. Try running /activeuser to fetch current active users.')

                _, target_username, file_name = arguments

                if target_username not in active_users:
                    print(f'User: {target_username} is not an active user.')
                    continue

                target_ip, target_udp_port = active_users[target_username]
                send_file_udp(target_ip, target_udp_port, file_name)
                continue

            elif user_input == '/activeuser':
                get_list = True

            s.sendall(user_input.encode())

    s.close()
