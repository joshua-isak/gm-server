import socket
import struct
import queue
import time
from threading import Thread

import info
import packet
from Color import color


class Server:
    def __init__(self, port):
        self.port = port                # Server application port
        self.socket = None              # Server's UDP socket
        self.running = False

        self.clients = []               # Connected clients
        self.client_ids = {}            # Index of connected client ids to their respective object reference
        self.host = None                # Reference to client that is host


    # Print message in console and send to all clients
    def message(self, msg, clr):                  
        data = bytearray(len(msg) + 2 + 1)              # Length of packet + 1 each for packet padding and packet type
        struct.pack_into('BB', data, 0, 0, 3)           # set up the packet (Padding, PacketType 3 for message)
        fmt = str(len(msg)) + 's'                       # set up format code for struct.pack_into (length of string + type string)
        struct.pack_into(fmt, data, 2, msg.encode('utf-8'))     # don't forget that offset arg (2 here) when writing to the bytearray!
        packet.send_all(self, data)
        #print(msg)
        #print(repr(data))
        print(clr + msg + color.end)


    # RLLY Basic, only use this loop for basic testing # # # # Perhaps add support for more than 2 connected players
    def basictick(self, tickrate):  
        while self.running:
            time.sleep(0.010)                                         # Sleep for 10 milliseconds (IMPORTANT TO REDUCE CPU USAGE)
            if (self.clients and not self.clients[0].queue.empty()):  # check if self.clients is not empty, and client 1's queue has data ##CHANGE TO HOST LATER 
                new_data = bytearray(12)                    # creates a buffer of 12 bytes  (do you need to destroy it when done?//memory leak?)
                struct.pack_into('BB', new_data, 0, 0, 4)   # set up the packet (Padding, PacketType)
                offset = 2                                  # define current offset for the buffer "new_data"

                for i in self.clients:          # loop through connected clients and get their most recent position data from their Queues
                    #client_id = i.id
                    #client_queue = self.client_data[client_num]     # gets the client's queue from info.client_data[]
                    client_queue = i.queue

                    if (not client_queue.empty()):                  # if the queue isn't empty...
                        data_tuple = client_queue.get()             # data_tuple = (clientnumber, pos x, pos y)
                        print("this worked")
                        print(str(data_tuple))
                        struct.pack_into('<BHH', new_data, offset, data_tuple[0], data_tuple[1], data_tuple[2])
                        offset += 5
                        
                print(repr(new_data))
                packet.send_all(self, new_data)       # send this packet to all clients! maybe in another thread?
                #print("SENT A TICK to: " + str(ip))
 


    def start(self):
        self.running = True

        # set up the socket using local address and a specified port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # configure socket for ipv4 and UDP
        self.socket.bind(("", 4296))                                   # "" means socket will listen to any network source

        # set up and start the gamethread
        gamethread = Thread(target=self.basictick, args=(info.tickrate,))
        gamethread.start()

        # packet handling loop
        while self.running:
            # get the data sent to the server
            data, ip = self.socket.recvfrom(1024)

            # unpack part of the data to find the packet type
            # data [1:2] is used to look at the first byte since Gamemaker 
            # pads sent out packets/buffers with 1 byte, the [0] looks at the first element in the returned tuple
            data_type = struct.unpack('B', data[1:2])[0] 
            
            # set up a thread to handle the packet type
            if (data_type == 1):   # PING
                t = Thread(target=packet.handle_ping, args=(self, ip, data))

            elif (data_type == 2): # HANDSHAKE
                t = Thread(target=packet.handle_handshake, args=(self, ip, data))

            elif (data_type == 3): # MESSAGE
                t = Thread(target=packet.handle_message, args=(self, ip, data))

            elif (data_type == 4): # BASIC TICK
                t = Thread(target=packet.basic_tick, args=(self, ip, data))
            else:
                continue

            # start the thread to handle the packet
            t.start() 