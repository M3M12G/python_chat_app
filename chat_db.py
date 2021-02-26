import json

import psycopg2 as pg


class chatDB(object):
    """
    used for work with postgres server database
    on >conf.json< file define the already created db name and other
    user credentials
    """
    _config = 'conf.json'
    _connection = None
    _cursor = None

    def __init__(self):
        try:
            with open(self._config, 'r') as configs:
                confs = json.load(configs)
                c = confs["db"]
            try:
                self._connection = pg.connect(host=c["host"], database=c["database"], port=c["port"], user=c["user"],
                                              password=c["password"])
                self._cursor = self._connection.cursor()
            except Exception as err:
                exception_type = type(err).__name__
                print("Connection failed: {} - {}".format(exception_type, err))
                return
        except Exception as err:
            exception_type = type(err).__name__
            print("Configuration failed: {} - {}".format(exception_type, err))
            return

    def is_connected(self):
        if not self._connection.closed:
            return True
        else:
            return False

    def close_connection(self):
        self._connection.close()

    def seed_db(self):
        """used to created table in database"""
        print("Creating tables...")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS users(\
                        user_id SERIAL PRIMARY KEY,\
                        username VARCHAR(255)\
                        );")
        print("...")
        self._cursor.execute("CREATE TABLE IF NOT EXISTS messages(\
                        msg_id SERIAL PRIMARY KEY,\
                        sender INTEGER NOT NULL,\
                        receiver VARCHAR(255),\
                        message VARCHAR(255),\
                        FOREIGN KEY (sender) REFERENCES users (user_id)\
                        ON UPDATE CASCADE ON DELETE RESTRICT\
                        );")
        self._connection.commit()
        print("Creating tables completed")

    def record_user(self, username):
        """save username to db"""
        if not self.is_connected():
            print("No connection with db")
            return False
        try:
            self._cursor.execute('INSERT INTO users (username) VALUES (%s)', (username,))
            self._connection.commit()
            return True
        except Exception as err:
            exception_type = type(err).__name__
            print("Error: {} - {}".format(exception_type, err))

    def is_user_exists(self, username):
        """during the user registration to chat, check whether this user exist in db"""
        sql = 'SELECT count(username) FROM users WHERE username=%s'
        self._cursor.execute(sql, (username,))
        res = self._cursor.fetchone()
        if res[0] == 0:
            return False
        return True

    def get_all_messages(self):
        """returns all messages"""
        sql = "SELECT users.username as sender, receiver, message FROM messages JOIN users ON messages.sender = users.user_id"
        self._cursor.execute(sql)
        results = self._cursor.fetchall()
        return results

    def get_userid_by_username(self, username):
        """returns the user's id based on username"""
        if not self.is_user_exists(username):
            return None
        sql = "SELECT user_id FROM users WHERE username=%s"
        self._cursor.execute(sql, (username,))
        user_id = self._cursor.fetchone()
        return user_id[0]

    def get_user_messages(self, username):
        """return all messages sent by particular username"""
        if not self.is_user_exists(username):
            return None
        sender_id = self.get_userid_by_username(username)
        sql = "SELECT username, receiver, message FROM messages JOIN users ON messages.sender = users.user_id WHERE sender=%s OR receiver=(SELECT username FROM users WHERE user_id=%s)"
        self._cursor.execute(sql, (sender_id,sender_id,))
        res = self._cursor.fetchall()
        return res

    def record_message(self, sender, receiver, message):
        """save incoming messages to db"""
        if not self.is_connected():
            print("No connection with db")
            return False
        sender_id = self.get_userid_by_username(sender)
        if sender_id is None:
            print("No user found by username {}".format(sender))
        try:
            sql = 'INSERT INTO messages (sender, receiver, message) VALUES (%s, %s, %s)'
            self._cursor.execute(sql, (sender_id, receiver, message,))
            self._connection.commit()
            return True
        except Exception as err:
            exception_type = type(err).__name__
            print("Error: {} - {}".format(exception_type, err))

#connection = chatDB()
#print(connection.get_user_messages("user2"))
# print(connection.is_user_exists("user2"))
# print(connection.is_connected())
# connection.seed_db()
# print(connection.record_user("user2"))
# sender = connection.get_userid_by_username("user2")
# print(connection.record_message(2, "all", "Why foreign key does not work"))
# print(connection.is_connected())
# print(connection.get_all_messages())
# print(connection.is_connected())
