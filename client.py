import json
import pickle
import socket as sc
import threading
from tkinter import *
from tkinter import messagebox

try:
    with open('conf.json', 'r') as configs:
        conf = json.load(configs)
        c = conf["server"]
except Exception as err:
    exception_type = type(err).__name__
    print("Configuration failed: {} - {}".format(exception_type, err))

HOST = c["host"]
PORT = c["port"]


class ClientGUI(Tk):
    """GUI of Chat client"""
    client_socket = None
    username = None

    def __init__(self):
        Tk.__init__(self)
        self.title('Chat client')
        self.geometry('700x500+100+50')
        self.app_frame = None
        # greeting frame would be initiated to prompt client username
        self.move_to_frame(Greeting_frame)

    def move_to_frame(self, next_frame):
        """frame switcher that deletes previous frame and puts new frame"""
        new_frame = next_frame(self)
        if self.app_frame is not None:
            self.app_frame.destroy()
        self.app_frame = new_frame
        self.app_frame.pack()
        # force to get the settled property of height and width by frames
        self.app_frame.pack_propagate(0)

    def set_username(self, user_name):
        """used to set client's username"""
        self.username = user_name

    def set_new_title(self, new_title):
        """used to change title of client GUI window by adding client's username like @my_name"""
        self.title(new_title)

    def connect_to_server(self):
        """do connection to chat server socket"""
        self.client_socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except ConnectionRefusedError:
            messagebox.showerror("Connection Failed", "Chat Server not available")
            self.destroy()

    def get_welcome_message(self):
        """returns welcome message from server"""
        wlc = self.client_socket.recv(2048)
        return wlc.decode("utf-8")

    def get_incoming_message(self):
        """works the same as get_welcome_message, but invoked while receiving"""
        data = self.client_socket.recv(2048)
        return data

    def send_username(self):
        """used to send client's username during connection to chat server"""
        user_name = self.username
        self.client_socket.send(user_name.encode("utf-8"))

    def send_msg(self, msg):
        """just enter not encoded text and this code would send it to server"""
        self.client_socket.send(bytearray(msg, encoding='utf-8'))

    def close_sc_connection(self):
        """Close connection and quit chat client app"""
        self.client_socket.close()
        quit()


class Greeting_frame(Frame):
    """First frame that meets client. here client types his/her username to join chat"""

    def __init__(self, root):
        Frame.__init__(self, root, height=300, width=400, bg='gray')
        self.root = root
        self.greeting_entry = StringVar()
        Label(master=self, text='Please, type your username here', font=12).pack(pady=75)
        Entry(master=self, textvariable=self.greeting_entry, font=14, width=25).pack(pady=10)
        Button(master=self, text='Join',
               font=10,
               command=self.prompt_username).pack()

    def prompt_username(self):
        """after prompting username, there would be switch of frame"""
        if self.greeting_entry.get() == '':
            return
        self.root.set_username(self.greeting_entry.get())
        self.root.move_to_frame(Chat_frame)


class Chat_frame(Frame):
    """main frame where client will 'chit-chat'"""

    def __init__(self, root):
        Frame.__init__(self, root, height=530, width=700)
        self.root = root
        self.root.set_new_title("Chat client - @{}".format(self.root.username))
        # connect to chat server socket here
        self.root.connect_to_server()
        self.output_welcome_msg()
        Button(self, text='Disconnect', width=25, font=11, command=self.disconnect).pack(side=TOP)
        # Part of interface where displayed incoming messages
        Label(self, text='Chat : Incoming Messages', font=11).pack()
        # there would be displayed incoming messages
        self.incoming_messages_area = Text(self, width=70, height=15, font=11)
        # adding scrollbar to see long list of messages
        scroll_bar = Scrollbar(self, command=self.incoming_messages_area.yview, orient=VERTICAL)
        self.incoming_messages_area.config(yscrollcommand=scroll_bar.set)
        self.incoming_messages_area.bind('<KeyPress>', lambda e: 'break')
        self.incoming_messages_area.pack()
        scroll_bar.pack(side='right', fill='y')
        # Part where would be prompted client messages
        Label(self, text='Type message', font=10).pack(side=LEFT)
        # entry prompt
        self.ent_msg = Text(self, width=70, height=1, font=12)
        self.ent_msg.pack()
        # to send message just type your message and press enter
        # binding pressing Enter key to event of sending message
        # I do not understand why event does not work, but messages sent only using btn
        self.ent_msg.bind('<Return>', self.send_message())
        Button(self, text='Send', width=25, font=11, command=self.send_message).pack(side=RIGHT)
        Button(self, text='Help', width=25, font=11, command=self.show_hints).pack(side=LEFT)
        # start in parallel receiving messages
        self.start_receive_threading()

    @staticmethod
    def show_hints():
        messagebox.showinfo("How to ..", "To send private message to client"
                                         "\nsend message in the format"
                                         "\n &client& message text ")
        messagebox.showinfo("How to ..", "Incoming messages starts with @\nPrivate incoming messages starts with @@")

    def print_history_of_messages(self, history_msg):
        """used to print history of messages at the start of connection to chat"""
        self.incoming_messages_area.insert('end', "-----------Log/History of Messages-------------" + '\n')
        self.incoming_messages_area.yview(END)
        msgs_list = pickle.loads(history_msg)
        for msg_i in range(len(msgs_list)):
            self.incoming_messages_area.insert('end',
                                               "@{} -> @{}: {}\n".format(msgs_list[msg_i][0], msgs_list[msg_i][1],
                                                                         msgs_list[msg_i][2]))
            self.incoming_messages_area.yview(END)
        self.incoming_messages_area.insert('end', "---------------------End-------------" + '\n')
        self.incoming_messages_area.yview(END)

    def output_welcome_msg(self):
        welcome_msg = self.root.get_welcome_message()
        messagebox.showinfo("Welcome to Chat", welcome_msg)
        # after receiving welcome message from chat server, client should send
        # his/her username to chat server in order to register client's socket
        # and username that can be used to retrieve client's logs of messages
        # private messages and so on
        self.root.send_username()

    def receive(self):
        """used to print on tkinter.Text widget incoming messages"""
        while True:
            message = self.root.get_incoming_message()
            if message.decode("utf-8") == "hist_msg":
                message_history = self.root.get_incoming_message()
                self.print_history_of_messages(message_history)
            self.incoming_messages_area.insert('end', "@{}\n".format(message.decode("utf-8")))
            self.incoming_messages_area.yview(END)

    def disconnect(self):
        """disconnecting from chat"""
        messagebox.showinfo("Connection closed", "You have disconnected from chat")
        self.root.close_sc_connection()
        self.root.destroy()

    def send_message(self):
        msg = self.ent_msg.get(1.0, 'end')
        self.incoming_messages_area.insert('end', "@You: "+msg)
        self.incoming_messages_area.yview(END)
        self.root.send_msg(msg)
        self.ent_msg.delete(1.0, 'end')
        return 'break'

    def start_receive_threading(self):
        """run process of receiving messages that sended from server parallel to sending process via client"""
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()


client = ClientGUI()
client.mainloop()
