import socket
import struct
import queue

import info

# set up some colors for terminal output (ANSI)
class color:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    cyan = '\033[96m'
    end = '\033[0m'


def ping(socket, ip, data):        # PING
    if (info.debug > 0):
        print(color.cyan + "{}: _Ping!".format(ip) + color.end)
    socket.sendto(data, ip)


def handshake(socket, ip, data):   # HANDSHAKE
    handshake_type = struct.unpack('B', data[2:3])[0]

    if (handshake_type == 0): # Initial Client Request
        if (info.debug > 0):
            print(color.cyan + "{}: _Handshake Request!".format(ip) + color.end)
        info.clients.append(ip)                 # Add this client to the list of connected clients
        client_num = len(info.clients)          # the client's serverside id number
        info.client_data.append(queue.Queue(0)) # add the client's queue for passing data to the gamethread, to the list of queues
        new_data = struct.pack('BBBB', 0, 2, 1, client_num) # new_data = (Padding, Packet_Type, Handshake_Type, Client_Number)
        socket.sendto(new_data, ip)

    elif (handshake_type == 2): # Client Acknowledgement
        print(color.green + "{}: _Client Connected!".format(ip) + color.end)
        socket.sendto(data, ip)
        ###### Maybe add code to make this actually functional besides a console.log?


def message(socket, ip, data):     # MESSAGE
    print("{}: {}".format(ip, data.decode('utf-8')))
    send_all(socket, ip, data)


# Only to be used for two player coordinate testing
def basic_tick(socket, ip, data):
    #info.tick += 1
    #print("Tick: " + str(info.tick))
    #print(repr(data))
    #print(repr(data[2:]))
    data_tuple = struct.unpack('<BHH', data[2:])            # put packet's data in data_tuple = (clientnumber, pos x, pos y)
    #print(data_tuple)
    #print(info.client_data)
    info.client_data[ data_tuple[0] - 1 ].put(data_tuple)   # push data_tuple into the client's corresponding queue



# Send a packet to all connected clients
def send_all(socket, ip, data):     # SENDALL
    for x in info.clients:
        socket.sendto(data, x)