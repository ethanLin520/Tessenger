import sys
import socket
import threading
from datetime import datetime, timedelta
from collections import OrderedDict

# Check if the correct number of arguments is provided
if len(sys.argv) != 3:
    print("Usage: python3 server.py server_port number_of_consecutive_failed_attempts")
    sys.exit(1)

# Extract command-line arguments
server_port = int(sys.argv[1])
max_attempts = int(sys.argv[2])

# Check if the port number is valid
if not 1024 <= server_port <= 65535:
    print("Invalid port number. Please use a port number between 1024 and 65535.")
    sys.exit(1)

# Ensure max_attempts is between 1 and 5
if not 1 <= max_attempts <= 5:
    print("The number of consecutive failed attempts must be between 1 and 5.")
    sys.exit(1)

BLOCK_TIME = 10     # seconds

# Server settings
HOST = '0.0.0.0'

login_failed_attempt = {}
login_unblock_time = {}

# Dict of all active users. The value field consist of (login time, IP, UDP port, conn)
active_user = OrderedDict()

with open('userlog.txt', 'w') as file:
    pass

with open('messagelog.txt', 'w') as file:
    pass

message_id = 1

# Load credentials from file
def load_credentials():
    with open('credentials.txt', 'r') as f:
        return [line.strip().split() for line in f.readlines()]

# Handle client connection
def handle_client(conn, addr):
    """
    Handle client's request.
    """

    print(f'Connected by {addr}')

    username, client_upd = authenticate(conn, addr)

    # Main loop for handling commands
    while True:
        conn.sendall(b'Enter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo ,/logout, /?): ')
        print("Waiting for user input...")

        arguments = conn.recv(1024).decode().strip().split()
        if not arguments:
            continue

        command = arguments[0]
        command_timestamp = datetime.now()
        print(f"Received command: {command} from user: {username}.")

        if command == '/logout':
            active_user.pop(username)
            log_active_user()
            conn.sendall(b'Goodbye!\n')
            print(f"User: {username} is logged out.")
            break
        elif command == '/msgto':
            global message_id
            if len(arguments) < 3:
                conn.sendall(b'Usage: /msgto USERNAME MESSAGE_CONTENT\n')
                print(f"Invalid arguements input by user: {username}.")
                continue

            recv = arguments[1]
            content = " ".join(arguments[2:])
            msg_timestamp = command_timestamp.strftime("%d %b %Y %H:%M:%S")

            # log message
            with open('messagelog.txt', 'a') as log:
                log.write(f"{message_id}; {msg_timestamp}; {recv}; {content}\n")

            conn.sendall(f"Message is successfully sent at {msg_timestamp}, id = {message_id}.\n".encode())
            print(f"User: {username} requested {command}.")

            message_id += 1

            # display to the receiver
            # dest_conn = active_user[recv][3]
            # dest_conn.sendall(f"{msg_timestamp}, {username}: {content}\n".encode())


        elif command == '/activeuser':
            if len(arguments) != 1:
                conn.sendall(b'Usage: /activeuser\n')
                print(f"Invalid arguements input by user: {username}.")
                continue

            if len(active_user) == 1:
                conn.sendall(b'no other active user.\n')
            else:
                message = ""
                for user, value in active_user.items():
                    if user != username:
                        message += f"{user}, active since {value[0]}. IP address: {value[1]}. UDP port: {value[2]}\n"

                conn.sendall(message.encode())
            print(f"User: {username} requested {command}.")
        else:
            conn.sendall(b'Command not recognized.\n')
            print(f"Invalid command by user: {username}.")

    conn.close()

def authenticate(conn, addr):
    """
    Authenticate user given a established connection.
    Return: username.
    """
    credentials = load_credentials()

    # print(login_failed_attempt)   # debug use

    while True:
        conn.sendall("Enter username: ".encode())
        username = conn.recv(1024).decode().strip()
        print(f"Received username: {username}.")

        conn.sendall("Enter password: ".encode())
        password = conn.recv(1024).decode().strip()
        print(f"Received password for {username}.")

        attempts = login_failed_attempt[username] if username in login_failed_attempt else 0
        
        # Check if user is currently blocked
        if username in login_unblock_time:
            block_time = login_unblock_time[username]
            if datetime.now() < block_time:
                conn.sendall(b'You are blocked. Please try again later.\n')
                print(f"User: {username} is blocked from logging in.")
                continue
            else:
                # Block duration has passed, remove the block
                login_unblock_time.pop(username)

        # Check credentials
        if [username, password] in credentials:
            # Get the current time
            current_time = datetime.now().strftime("%d %b %Y %H:%M:%S")
            login_failed_attempt.pop(username, None)
            login_unblock_time.pop(username, None)
            conn.sendall(b'Welcome!\n')
            print(f"User: {username} successfully logged in")
            client_upd_port = int(conn.recv(1024).decode().strip())

            active_user[username] = (current_time, addr[0], client_upd_port, conn)
            log_active_user()

            return username, client_upd_port
        else:
            attempts += 1
            login_failed_attempt[username] = attempts
            conn.sendall(b'Invalid credentials. Try again.\n')
            print(f"User: {username} unsuccessfully attempted to log in {attempts} times.")

        # Block user after max_attempts
        if attempts >= max_attempts:
            unblock = datetime.now() + timedelta(seconds=10)
            login_unblock_time[username] = (unblock)
            login_failed_attempt.pop(username)
            conn.sendall(b'You are blocked due to multiple failed login attempts.\n')
            print(f"User: {username} has attempted {attempts} time and is blocked until {unblock}.")

def log_active_user():
    i = 1
    with open('userlog.txt', 'w') as log:
        for user, value in active_user.items():
            log.write(f'{i}; {value[0]}; {user}; {value[1]}; {value[2]}\n')
            i += 1

# Create socket and bind to address
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, server_port))
    s.listen()

    print(f'Server is listening on {HOST}:{server_port}')

    # Main server loop
    while True:
        conn, addr = s.accept()
        # Start a new thread for each client
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()
