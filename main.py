'''
The task [80%]
Your task is to create a chat server that accepts several connections from chat clients. The
idea is to create a chat conference where users send broadcast messages (one-to-all, kind of
WhatsApp group). When a user sends a message the user name should appear next to the
message. You can consider that usernames are all unique. Server should save the log of all
the incoming messages in a database in case if a user asks for the log of his/her messages.
Task for the 20%
Give users a possibility to send private messages to each other. You can do it this way:
On client side sending message: /private to username_here message_content.
On server side check if the message is starting from /private word and search for this person in
your connections list/dictionary
'''