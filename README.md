# Chat and P2P Video Sharing Application

## Introduction
This document describes a comprehensive Python-based application that includes a Chat Server and a P2P Video Sharing Client. The Chat Server handles user authentication, messaging, and group chats, while the Client enables direct video file sharing among users.

## Chat Server (`server.py`)

### Features
- **User Authentication**: Validates user credentials.
- **Messaging**: Supports DMs and group chats.
- **Active User Management**: Tracks and logs active users.
- **Group Management**: Allows creating and joining groups.
- **Security**: Blocks users after failed login attempts.

### Requirements
- Python 3.x
- Modules: `sys`, `socket`, `threading`, `datetime`, `collections`

### Setup
1. **Credentials File**: Set user credentials in the specified file in `myconstant.py`.
2. **Starting the Server**: Execute with `python3 server.py [server_port] [max_failed_attempts]`.

## P2P Video Sharing Client (`client.py`)

### Features
- **TCP/IP and UDP Sockets**: Utilizes TCP/IP for server communication and UDP for file transfer.
- **Video File Sharing**: Shares video files with other users.
- **User List Management**: Manages a list of active users.

### Requirements
- Python 3.x
- Modules: `re`, `sys`, `socket`, `select`, `threading`, `time`

### Setup
1. **Starting the Client**: Run with `python3 client.py [server_IP] [server_port] [client_udp_port]`.
2. **File Sharing Command**: Use `/p2pvideo [username] [filename]` for sharing.

## Common Considerations
- **Port Numbers**: Use valid port numbers (1024-65535).
- **Network Security**: Data transmissions are not encrypted.
- **Error Handling**: Includes basic handling for network and file operations.

## Future Enhancements
- Implement SSL/TLS for secure communication.
- Improve user interface and error messages.
- Add features like voice/video calls or file sharing in chats.

## Troubleshooting
- Check Python version and modules.
- Ensure correct port numbers for server and client.
- Verify the credentials file format and location for the server.

## Conclusion
This application demonstrates the use of TCP/IP and UDP in Python for real-time communication and peer-to-peer video file sharing, providing a foundation for chat services with additional capabilities.
