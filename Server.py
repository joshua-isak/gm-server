import socket
import struct
import queue
import time
from threading import Thread

import info
import packet


# set up some colors for terminal output (ANSI)
class color:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    cyan = '\033[96m'
    end = '\033[0m'


class Server:
    def __init__(self, port):
        self.port = port                # Server application port
        self.clients = []               # Connected clients
        self.socket = None              # Server's UDP socket
        self.running = False



    def basictick(self, tickrate): # RLLY Basic, only use this loop for basic testing # # # # Perhaps add support for more than 2 connected players
        while self.running:
            time.sleep(0.010)                                         # Sleep for 10 milliseconds (IMPORTANT TO REDUCE CPU USAGE)
            if (info.clients and not info.client_data[0].empty()):    # check if info.clients is not empty, and client 1's queue has data  
                new_data = bytearray(12)                    # creates a buffer of 12 bytes  (do you need to destroy it when done?//memory leak?)
                struct.pack_into('BB', new_data, 0, 0, 4)   # set up the packet (Padding, PacketType)
                offset = 2                                  # define current offset for the buffer "new_data"

                for i in range(len(info.clients)):          # loop through connected clients and get their most recent position data from their Queues
                    client_num = i
                    client_queue = info.client_data[client_num]     # gets the client's queue from info.client_data[]
        
                    if (not client_queue.empty()):                  # if the queue isn't empty...
                        data_tuple = client_queue.get()             # data_tuple = (clientnumber, pos x, pos y)
                        #print("Q: " + str(client_queue.qsize()))
                        struct.pack_into('<BHH', new_data, offset, data_tuple[0], data_tuple[1], data_tuple[2])
                        offset += 5

                        ip = info.clients[i]                # consider removing since packet.send_all() doesn't need an ip arg
                packet.send_all(self, ip, new_data)       # send this packet to all clients! maybe in another thread?
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
                t = Thread(target=packet.ping, args=(self, ip, data))

            elif (data_type == 2): # HANDSHAKE
                t = Thread(target=packet.handshake, args=(self, ip, data))

            elif (data_type == 3): # MESSAGE
                t = Thread(target=packet.message, args=(self, ip, data))

            elif (data_type == 4): # BASIC TICK
                t = Thread(target=packet.basic_tick, args=(self, ip, data))
            else:
                continue

            # start the thread to handle the packet
            t.start() 