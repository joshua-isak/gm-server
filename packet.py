import socket
import struct
import queue
import random
import time

import info
from Color import color
from Client import Client


def handle_ping(server, ip, data):        # PING
    if (info.debug > 0):
        print(color.cyan + "{}: _Ping!".format(ip) + color.end)
    server.socket.sendto(data, ip)


def handle_handshake(server, ip, data):   # HANDSHAKE
    handshake_type = struct.unpack('B', data[2:3])[0]

    if (handshake_type == 0): # Initial client connection request
        #info.clients.append(ip)                 # Add this client to the list of connected clients
        #client_num = len(info.clients)          # the client's serverside id number
        #info.client_data.append(queue.Queue(0)) # add the client's queue for passing data to the gamethread, to the list of queues
        #new_data = struct.pack('BBBB', 0, 2, 1, client_num) # new_data = (Padding, Packet_Type, Handshake_Type, Client_Number)
        #server.socket.sendto(new_data, ip)

        # # # TESTING # # #
        while True:                             # Generate a new random id that is not already in use
            new_id = random.randint(0, 255)
            if (new_id not in server.client_ids.keys()):
                break
        username = data[3:].decode('utf-8')
        new_client = Client(new_id,ip,server,username)
        info.test_client = new_client

        #Uncomment this to make this testing block actually work
        new_data = struct.pack('BBBB', 0, 2, 1, new_id)
        server.socket.sendto(new_data, ip)
        new_client.connect()
        
    elif (handshake_type == 2): # Client Acknowledgement
        #print(color.green + "{}: _Client Connected!".format(ip) + color.end)
        server.socket.sendto(data, ip)
        ###### Maybe add code to make this actually functional besides a console.log?
        # # # TESTING # # #
        client_id = struct.unpack('B', data[3:4])[0]
        #print("id: " + str(client_id))
        #print(str(server.client_ids))
        server.client_ids[client_id].handshake = True
        #info.test_client.handshake = True


def handle_message(server, ip, data):     # MESSAGE
    print("{}: {}".format(ip, data.decode('utf-8')))
    send_all(server, data)


# Only to be used for two player coordinate testing
def basic_tick(server, ip, data):
    #info.tick += 1
    #print("Tick: " + str(info.tick))
    #print(repr(data))
    #print(repr(data[2:]))
    data_tuple = struct.unpack('<BHH', data[2:])            # put packet's data in data_tuple = (clientnumber, pos x, pos y)
    #print(data_tuple)
    #print(info.client_data)
    #info.client_data[ data_tuple[0] - 1 ].put(data_tuple)   # legacy of below
    #print(str(server.client_ids))
    ##print(str(data_tuple))
    client_id = data_tuple[0]
    ##print(str(server.client_ids[client_id].username))
    ##print(str(server.client_ids[client_id].queue))
    server.client_ids[client_id].queue.put(data_tuple)  # push data_tuple into the client's corresponding queue



# Send a packet to all connected clients
def send_all(server, data):     # SENDALL
    for x in server.clients:
        server.socket.sendto(data, x.ip)