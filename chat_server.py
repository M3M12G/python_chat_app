import json
import pickle
import re
import socket as sc
import threading
import chat_db


def private_decompose(msg):
    """Used to split the receiver username and the message"""
    username = re.findall(r'\B&\w+\b&', msg)
    # verify that this private message is sent only for one client
    if len(username) > 1:
        return None, None
    receiver = username[0].strip("&")
    message = re.split(r'\A&\w+\b&', msg)
    return receiver, message[1]


def send_to(sender_username, receiver_socket, message):
    """Used to forward private message of one client to another one directly"""
    private_msg = "@{}: {}".format(sender_username, message)
    receiver_socket.send(private_msg.encode("utf-8"))


try:
    with open('conf.json', 'r') as configs:
        conf = json.load(configs)
        c = conf["server"]
except Exception as err:
    exception_type = type(err).__name__
    print("Configuration failed: {} - {}".format(exception_type, err))

HOST = c["host"]
PORT = c["port"]
# stores the socket connections from clients, which uses usernames as a key
client_sockets = {}


def broadcast_msg(sender_con, msg):
    """used to forward incoming messages to all connected client sockets except sender client socket"""
    for username, client_con in client_sockets.items():
        if client_con == sender_con:
            continue
        client_con.send(msg)


def client_handler(con, addr, db_con):
    """handles with client connection"""
    welcome = "[SERVER]: Welcome to Chat. Type 'q' to quit chat\n" \
              "to send private message to the client, send message in format: \n" \
              "\t&client& message text"
    wlc = welcome.encode("utf-8")
    con.send(wlc)

    with con:
        print("New client is joined - {}".format(addr))
        # getting client's username
        init_client = con.recv(2048)
        username = init_client.decode("utf-8")
        client_sockets[username] = con

        # register new usernames
        if not db_con.is_user_exists(username):
            db_con.record_user(username)

        # notify all users about new user
        join_msg = "------{} is joined to chat--------".format(username)
        broadcast_msg(con, join_msg.encode("utf-8"))

        # if server founds that this username(client)'s
        # messages/history is on db, then it sends to client
        if db_con.is_user_exists(username):
            con.send("hist_msg".encode("utf-8"))
            # at the start of conversation by firstly sending special
            # command to client to print them after that sent
            history = db_con.get_user_messages(username)
            con.send(pickle.dumps(history))
        while True:
            income_data = con.recv(2048)
            # taking incoming data
            msg = income_data.decode("utf-8")
            check_msg = list(msg)
            # if server receive this msg, then it deletes this connection
            # from dictionary
            if msg == "q":
                del client_sockets[username]
                print("Client - {} disconnected".format(con.getpeername()))
                con.close()
                break

            # as on broadcast, the receiver of message
            # is "all" clients
            receiver = "all"
            # check whether msg is private
            # if private, prepare details to store
            # inside condition, send directly to client socket
            if check_msg[0] == "&":
                receiver, msg = private_decompose(msg)

                # if client is already on chat send private msg
                # otherwise just store it to db
                # until receiving client joins to chat
                # and get the history of all msgs (private msg included)
                if receiver in client_sockets.keys():
                    send_to(username, client_sockets[receiver], msg)
                    # process of saving incoming messages to db
                    db_con.record_message(username, receiver, msg)
                    continue
            # process of saving incoming messages to db
            db_con.record_message(username, receiver, msg)

            print("#{}: {}".format(username, msg))
            message = "{}: {}".format(username, msg)
            # any msg that server receive from clients, it broadcasts to
            # all connected client's sockets
            broadcast_msg(con, message.encode("utf-8"))


with sc.socket(sc.AF_INET, sc.SOCK_STREAM) as chat_socket:
    print("[SERVER]: Start...")
    try:
        chat_socket.bind((HOST, PORT))
        # providing connection to db
        db_con = chat_db.chatDB()
        # creating tables in db if not exists
        db_con.seed_db()
    except Exception as err:
        exception_type = type(err).__name__
        print("[SERVER]: {} - {}".format(exception_type, err))
        quit()
    # chat server listening to connections from client's sockets
    chat_socket.listen()
    print("[SERVER]: Listening new connections on {} - {}".format(
        HOST, PORT
    ))
    while True:
        # accept incoming client sockets
        incoming_con, addr = chat_socket.accept()
        con_thread = threading.Thread(target=client_handler, args=(incoming_con, addr, db_con))
        con_thread.start()
        print("[SERVER]: Connected - {}".format(threading.active_count() - 1))
