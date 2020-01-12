import socket
import struct
import queue
import random
import time

import info
from Color import color
from Client import Client


def handle_ping(server, ip, data):
    if (server.debug > 0):               
        print(color.cyan + "{}: _Ping!".format(ip) + color.end)
    server.socket.sendto(data, ip)


def handle_handshake(server, ip, data):
    handshake_type = struct.unpack('B', data[2:3])[0]

    if (handshake_type == 0): # Initial client connection request

        while True:                             # Generate a new random uid that is not already in use
            new_id = random.randint(0, 255)
            if (new_id not in server.client_ids.keys()):
                break

        username = data[3:].decode('utf-8')
        new_client = Client(new_id,ip,server,username)

        new_data = struct.pack('BBBB', 0, 2, 1, new_id)
        server.socket.sendto(new_data, ip)
        new_client.connect()
        

    elif (handshake_type == 2): # Client Acknowledgement
        server.socket.sendto(data, ip)          # this line might no longer be necessary
        client_id = struct.unpack('B', data[3:4])[0]
        server.client_ids[client_id].handshake = True



def handle_message(server, ip, data):           # update this to inclue server.message()
    print("{}: {}".format(ip, data.decode('utf-8')))
    send_all(server, data)


# Only to be used for two player coordinate testing
def basic_tick(server, ip, data):
    data_tuple = struct.unpack('<BHH', data[2:])        # put packet's data in data_tuple = (client_id, pos x, pos y)
    client_id = data_tuple[0]
    server.client_ids[client_id].queue.put(data_tuple)  # push data_tuple into the client's corresponding queue



# Send a packet to all connected clients
def send_all(server, data):
    for x in server.clients:
        server.socket.sendto(data, x.ip)