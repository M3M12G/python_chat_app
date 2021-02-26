import json
import pickle
import socket as sc
import threading


def print_history_of_messages(data):
    """used to print the history of messages sent by client"""
    print("\n-----------Log/History of Messages-------------")
    msgs_list = pickle.loads(data)
    for msg_i in range(len(msgs_list)):
        print("@{} -> @{}: {}".format(msgs_list[msg_i][0], msgs_list[msg_i][1], msgs_list[msg_i][2]))
    print("--------------------End------------------------")


try:
    with open('conf.json', 'r') as configs:
        conf = json.load(configs)
        c = conf["server"]
except Exception as err:
    exception_type = type(err).__name__
    print("Configuration failed: {} - {}".format(exception_type, err))

HOST = c["host"]
PORT = c["port"]

# perform connection to server socket
with sc.socket(sc.AF_INET, sc.SOCK_STREAM) as client_socket:
    print("[CLIENT]: Connecting to server... at {}:{}".format(HOST, PORT))
    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[CLIENT]:Chat server not available..")


    def chit_chat():
        """Serves for sending messages and special commands"""
        while True:
            msg = input("#{}: >".format(username))
            if msg == "q":
                client_socket.send(msg.encode("utf-8"))
                client_socket.close()
                print("[CLIENT]: Connection closed")
                break
            # wrap sending msg to try except
            try:
                client_socket.send(bytearray(msg, encoding='utf-8'))
            except Exception as con_err:
                exception_t = type(con_err).__name__
                print("Connection lost: {} - {}".format(exception_t, con_err))


    def receive():
        """Serves as message receiver from server using connection to server socket"""
        while True:
            data = client_socket.recv(2048)
            # acknowledgement message in case if this history of client messages
            # or disconnection from server

            # wait from server about history of messages sent by the
            # client's username
            # if server founds client's msg history/logs
            # then sends to client special command
            # that initiates the print of previous messages
            if data.decode("utf-8") == "hist_msg":
                # special function to print msg history from server
                msg_history = client_socket.recv(2048)
                print_history_of_messages(msg_history)
            print()
            print("@{}".format(data.decode("utf-8")))


    # getting welcome message from server
    wlc = client_socket.recv(2048)
    welcome_message = wlc.decode("utf-8")
    print(welcome_message)

    # "registering"/sending to bind username to client socket
    print("Incoming messages starts with @")
    print("Private incoming messages starts with @@")
    username = input("[CLIENT]:Please, type your username >")
    client_socket.send(username.encode("utf-8"))

    # placing receive process is used to solve the problem of waiting clients
    # other client, which for that moment is ready/sending message to server
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    # client start chatting here
    chit_chat()
