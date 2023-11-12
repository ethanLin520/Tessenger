import re
import sys
import socket
import select
import threading
from time import sleep, time

from myconstant import UDP_BUFFER, UDP_CHUNK, COMMAND_PROMPT, UDP_SEND_PAUSE

def udp_server(udp_port, buffer_size=UDP_BUFFER):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.bind(('', udp_port))
        print(f"UDP server listening on port {udp_port}")

        while True:
            data, addr = udp_sock.recvfrom(buffer_size)
            if data:
                content = data.decode()
                if content.startswith('Start sending file:'):
                    file_name = content.split(':', 1)[1]
                    sender = addr
                    with open(file_name, 'wb') as file:
                        while True:
                            data, addr = udp_sock.recvfrom(buffer_size)
                            if addr != sender:
                                print(f"Receiving file was interrupted by {addr}. File may be corrupted.", flush=True)
                                break

                            try:
                                if data.decode() == "File send has finished.":
                                    break
                            except UnicodeDecodeError:
                                pass
                            file.write(data)

                    print(f"\n\nReceived file {file_name} from {addr}\n\n{COMMAND_PROMPT}", end='', flush=True)

def send_file_udp(target_ip, target_port, file_path, chunk_size=UDP_CHUNK):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        start_t = time()
        # Open the file
        with open(file_path, 'rb') as file:
            starting_prompt = f"Start sending file:{file_name}"
            udp_sock.sendto(starting_prompt.encode(), (target_ip, target_port))
            # Read and send the file in chunks
            chunk = file.read(chunk_size)
            while chunk:
                udp_sock.sendto(chunk, (target_ip, target_port))
                sleep(UDP_SEND_PAUSE)
                chunk = file.read(chunk_size)

        ending_prompt = f"File send has finished."
        udp_sock.sendto(ending_prompt.encode(), (target_ip, target_port))

        duration = time() - start_t
        print(f"Finished uploading file {file_path} to {target_ip}:{target_port}. Upload time: {round(duration, 2)}s.\n")

    except Exception as e:
        print(f"Error occurred in sending file {file_path}: {e}")
    finally:
        udp_sock.close()

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

# Run UDP socket
udp_thread = threading.Thread(target=udp_server, args=(client_udp_port,))
udp_thread.daemon = True  # This ensures the thread will exit when the main program exits
udp_thread.start()

# Create a TCP/IP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Connect to server
    s.connect((server_IP, server_port))
    
    print("Connected to the server.")

    username = None
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
            if 'Welcome!' in prompt:
                username = prompt.split('! ', maxsplit=1)[1].strip()
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
                    print(f'Usage: /p2pvideo username filename')
                else:
                    _, target_username, file_name = arguments

                    if not active_users:
                        print('No active users on record. Try running /activeuser to fetch current active users.')

                    elif target_username == username:
                        print("You cannot share video to yourself.")

                    elif target_username not in active_users:
                        print(f'User: {target_username} is not an active user. Please try again.')

                    else:
                        target_ip, target_udp_port = active_users[target_username]
                        send_file_udp(target_ip, target_udp_port, file_name)

                print(COMMAND_PROMPT, end='', flush=True)
                continue

            elif user_input == '/activeuser':
                get_list = True


            s.sendall(user_input.encode())

    s.close()
