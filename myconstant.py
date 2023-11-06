#   SERVER SETTING

HOST = '0.0.0.0'

BLOCK_TIME = 10

USER_LOG = 'userlog.txt'
MSG_LOG = 'messagelog.txt'
CREDENTIAL = 'credentials.txt'

UDP_BUFFER = 1024

#   TEXT

COMMAND_PROMPT = b'Enter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo ,/logout, /help): '

HELP_PROMPT = """
/msgto: Private message, which the user launches a private chat with another active user and send private messages,
/activeuser: Display active users,
/creategroup: Group chat room service, which user can build group chat for multiple users
/joingroup: Group chat room service, which user can join the already created group chat
/groupmsg: Group chat message, user can send the message to a specific group and all the users in the group will receive the message,
/logout: Log out
/p2pvideo: send video file to another active user directly via UDP socket (for CSE Students only).\n
"""