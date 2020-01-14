import socket
import struct
import queue
import random
import time
from threading import Thread

from Color import color
from Client import Client


def handle_ping(server, ip, data):
    client_id = struct.unpack('B', data[2:3])[0]                # get the client_id of the packet sender (0 if unconnected client)
    if client_id in server.client_ids.keys():                   # check if client is connected
        server.client_ids[client_id].last_ping = time.time()    # update last ping time if it is
    server.socket.sendto(data, ip)                              # send ping response


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def handle_handshake(server, ip, data):
    handshake_type = struct.unpack('B', data[2:3])[0]

    if (handshake_type == 0):   # Initial client connection request

        while True:                                         # Generate a new random uid that is not already in use
            new_id = random.randint(1, 255)
            if (new_id not in server.client_ids.keys()):
                break

        username = data[3:].decode('utf-8')
        new_client = Client(new_id, ip, server, username)   # Create a new client object

        new_data = struct.pack('BBBB', 0, 2, 1, new_id)     
        server.socket.sendto(new_data, ip)                  # reply to client with its unique id
        new_client.connect()
        

    elif (handshake_type == 2): # Client completion of handshake
        client_id = struct.unpack('B', data[3:4])[0]
        server.client_ids[client_id].handshake = True       # change client handshake status, client will be kicked if left false


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def handle_message(server, ip, data):  # TODO update this to inclue server.message()
    print("{}: {}".format(ip, data.decode('utf-8')))
    send_all(server, data)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Only to be used for two player coordinate testing
def basic_tick(server, ip, data):
    data_tuple = struct.unpack('<BHH', data[2:])            # put packet's data in data_tuple = (client_id, pos x, pos y)
    client_id = data_tuple[0]
    if client_id in server.client_ids.keys():               # only process the data if the client_id matches one of a connected client
        server.client_ids[client_id].queue.put(data_tuple)  # push data_tuple into the client's corresponding queue


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Send a packet to all connected clients
def send_all(server, data):
    for x in server.clients:
        server.socket.sendto(data, x.ip)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


###=====### WIP ###=====###


def handle_ack(server, ip, data):
    ack_code = struct.unpack('B', data[2:3])[0]
    server.pending_acks[ack_code] = True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# Only to be used with packet types that support acknowledgements
def send_with_ack(server, client, data):
    while True:                                     # Generate a new unique random ack_code
        ack_code = random.randint(1, 255)
        if (ack_code not in server.pending_acks.keys()):
            break

    server.pending_acks[ack_code] = False           # add ack code to pending acks dictionary
    struct.pack_into('B', data, 3, ack_code)        # add ack code to packet data
                                
    while client.connected:                         # keep sending packet until an acknowledgement is received
        server.socket.sendto(data, client.ip)
        time.sleep(1)
        if server.pending_acks[ack_code] == True:
            break

    server.pending_acks.pop(ack_code)               # remove ack_code from pending acks dictionary

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

def send_connection(server, conn_type, client):  # Requires acknowledgement
    print("connected clients :" + str(server.clients))
    # prepare packet header
    new_data = bytearray(200)
    offset = 0
    struct.pack_into('BB', new_data, offset, 0, 5)
    offset += 2

    struct.pack_into('B', new_data, offset, conn_type) 
    offset += 1
    offset += 1   # add padding for ack_code

    # send all client ids and usernames to the specified client
    if (conn_type == 0):
        struct.pack_into('B', new_data, offset, len(server.clients))
        offset += 1

        for x in server.clients:                        
            struct.pack_into('B', new_data, offset, x.id)
            offset += 1

            fmt = str(len(x.username)) + 's'            
            struct.pack_into(fmt, new_data, offset, x.username.encode('utf-8'))
            offset += len(x.username)

        print("sent conn type 0 to " + str(client.id))
        t = Thread(target=(send_with_ack), args=(server, client, new_data))
        t.start()

    # tell all clients a new client has connected to the server
    elif (conn_type == 1):      
        struct.pack_into('B', new_data, offset, client.id)
        offset += 1
        fmt = str(len(client.username)) + 's'            
        struct.pack_into(fmt, new_data, offset, client.username.encode('utf-8'))

        for x in server.clients:
            print("sent conn type 1 to " + str(x.id))
            t = Thread(target=(send_with_ack), args=(server, x, new_data))
            t.start()

    # tell a client it has been disconnected
    elif (conn_type == 2):      
        return 0

    # tell all clients a client has disconnected
    elif (conn_type == 3):      
        struct.pack_into('B', new_data, offset, client.id)
        for x in server.clients:
            print("sent conn type 3 to " + str(x.id))
            t = Thread(target=(send_with_ack), args=(server, x, new_data))
            t.start()




# TODO
# handle_connection
# send
# handle_command
# handle_ack