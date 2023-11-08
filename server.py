import sys
import socket
import threading
from datetime import datetime, timedelta
from collections import OrderedDict

from myconstant import *

login_failed_attempt = {}
login_unblock_time = {}

# Dict of all active users. The value field consist of (login time, IP, UDP port, conn)
active_user = OrderedDict()

# Dict of all chat groups. The value field cosist of [[members added], [members joined], group_message_id]
groups = OrderedDict()

# Dict of all user's joined groups
users_joined_groups = {}

with open(USER_LOG, 'w') as file:
    pass

with open(MSG_LOG, 'w') as file:
    pass

message_id = 1

# Load credentials from file
def load_credentials():
    with open(CREDENTIAL, 'r') as f:
        return [line.strip().split() for line in f.readlines()]

# Handle client connection
def handle_client(conn, addr):
    """
    Handle client's request.
    """

    print(f'Connected by {addr}')

    username = authenticate(conn, addr)

    # Main loop for handling commands
    while True:
        try:
            conn.sendall(COMMAND_PROMPT.encode())
            print("Waiting for user input...")

            arguments = conn.recv(1024).decode().strip().split()
            if not arguments:
                continue

            flag = handle_command(conn, username, arguments)
            if flag != 0:
                break
        except BrokenPipeError:
            print(f"User: {username} has closed the connection.")
            logout(username)
            break
    
    conn.close()

def handle_command(conn, username, arguments):
    global active_user, groups, users_joined_groups
    command = arguments[0]
    command_timestamp = datetime.now()
    print(f"Received command: {command} from user: {username}.")

    if command == '/logout':
        if len(arguments) != 1:
            conn.sendall(b'Usage: /logout\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        logout(username)
        return 1

    elif command == '/msgto':
        global message_id
        if len(arguments) < 3:
            conn.sendall(b'Usage: /msgto USERNAME MESSAGE_CONTENT\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        recv = arguments[1]
        content = " ".join(arguments[2:])
        msg_timestamp = command_timestamp.strftime("%d %b %Y %H:%M:%S")

        # log message
        with open(MSG_LOG, 'a') as log:
            log.write(f"{message_id}; {msg_timestamp}; {recv}; {content}\n")

        # display to the receiver
        dest_conn = active_user[recv][3]
        dest_conn.sendall(f"\n\n{msg_timestamp}, {username}: {content}\n\n".encode())
        dest_conn.sendall(COMMAND_PROMPT.encode())

        conn.sendall(f"Message is successfully sent at {msg_timestamp}, id = {message_id}.\n".encode())
        print(f"User: {username} requested {command} successfully.")

        message_id += 1

    elif command == '/activeuser':
        if len(arguments) != 1:
            conn.sendall(b'Usage: /activeuser\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        if len(active_user) == 1:
            conn.sendall(b'no other active user.\n')
        else:
            userlist = "\n"
            for user, value in active_user.items():
                if user != username:
                    userlist += f"{user}, active since {value[0]}. IP address: {value[1]}. UDP port: {value[2]}\n"
            userlist += '\n'
            conn.sendall(userlist.encode())
        print(f"User: {username} requested {command} successfully.")

    elif command == '/creategroup':
        if len(arguments) < 3:
            conn.sendall(b'Usage: /creategroup groupname username1 username2 ..\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        groupname = arguments[1]
        if groupname in groups:
            conn.sendall(f'Group name: {groupname} already exist. Please try another name.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        # check name is legal
        if not groupname.isalnum():
            conn.sendall(f'Group name: {groupname} is not legal. Group name can only contain alphanumeric character. Please try another name.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        # check invitees are legal
        invitees = arguments[2:]
        invalid_invitee = []
        for user in invitees:
            if user not in active_user:
                invalid_invitee.append(user)

        if invalid_invitee != []:
            namelist = ", ".join(invalid_invitee)
            conn.sendall(f'Invalid invitee username: {namelist}. Please try other users.\n'.encode())
            print(f"Invalid invitee name input by user: {username}. Request for {command} is denied.")
            return 0

        members = invitees
        members.insert(0, username)
        groups[groupname] = [members, [username], 1]   # [[members_added], [members_joined], group_message_id]

        with open(f"{groupname}_{MSG_LOG}", 'w'):
            pass

        conn.sendall(f"\nGroup chat room has been created, room name: {groupname}, users added to this room: {members}.\n\n".encode())
        print(f"User: {username} successfully created the group chat: {groupname}.")

    elif command == '/joingroup':
        if len(arguments) != 2:
            conn.sendall(b'Usage: /joingroup groupname\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        groupname = arguments[1]
        if groupname not in groups:
            conn.sendall(f'Group: {groupname} does not exist. Please try again.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        if username not in groups[groupname][0]:
            conn.sendall(f'You are not part of the group: {groupname}.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        if username in groups[groupname][1]:
            conn.sendall(f'You already joined {groupname}.\n'.encode())
            print(f"User: {username} already in group. Request for {command} is denied.")
            return 0

        groups[groupname][1].append(username)
        users_joined_groups[username].append(groupname)

        conn.sendall(f'You have successfully joined {groupname}. You can now send group message in {groupname}.\n'.encode())
        print(f"User: {username} successfully joined {groupname}.")

    elif command == '/groupmsg':
        if len(arguments) < 3:
            conn.sendall(b'Usage: /groupmsg groupname message\n')
            print(f"Invalid arguements input by user: {username}. Request for {command} is denied.")
            return 0

        groupname = arguments[1]
        if groupname not in groups:
            conn.sendall(f'Group: {groupname} does not exist. Please try again.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        if username not in groups[groupname][0]:
            conn.sendall(f'You are not part of the group: {groupname}.\n'.encode())
            print(f"Invalid group name input by user: {username}. Request for {command} is denied.")
            return 0

        joined_users = groups[groupname][1]
        if username not in joined_users:
            conn.sendall(f'You have not joined {groupname}.\n'.encode())
            print(f"User: {username} has not joined the group. Request for {command} is denied.")
            return 0

        content = " ".join(arguments[2:])
        msg_timestamp = command_timestamp.strftime("%d %b %Y %H:%M:%S")

        with open(f"{groupname}_{MSG_LOG}", 'a') as log:
            log.write(f"{groups[groupname][2]}; {msg_timestamp}; {username}; {content}\n")

        for recv in joined_users:
            if recv != username:
                # display to the receiver
                dest_conn = active_user[recv][3]
                dest_conn.sendall(f"\n\n{msg_timestamp}, {groupname}, {username}: {content}\n\n".encode())
                dest_conn.sendall(COMMAND_PROMPT.encode())

        conn.sendall(f"Group message is successfully sent at {msg_timestamp} in {groupname}.\n".encode())
        print(f"User: {username} requested {command} successfully.")

        groups[groupname][2] += 1   # group_message_id

    elif command == '/p2pvideo':
        pass

    elif command == '/help':
        conn.sendall(HELP_PROMPT.encode())
        print(f"User: {username} requested {command} successfully.")

    else:
        conn.sendall(b'Command not recognized.\n')
        print(f"Invalid command by user: {username}.")

    return 0


def authenticate(conn, addr):
    """
    Authenticate user given a established connection.
    Return: username.
    """
    global active_user, login_failed_attempt, login_unblock_time

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

            users_joined_groups[username] = []

            return username
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

def logout(username):
    global users_joined_groups, active_user
    for g in users_joined_groups[username]:
        groups[g][1].remove(username)
    users_joined_groups.pop(username)
    active_user.pop(username)
    log_active_user()
    try:
        conn.sendall(b'You have successfully logged out.\n')
        conn.sendall(b'Goodbye!\n')
    except BrokenPipeError:
        pass
    print(f"User: {username} is logged out.")

def log_active_user():
    i = 1
    with open(USER_LOG, 'w') as log:
        for user, value in active_user.items():
            log.write(f'{i}; {value[0]}; {user}; {value[1]}; {value[2]}\n')
            i += 1

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
