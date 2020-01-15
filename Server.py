import socket
import struct
import queue
import time
from threading import Thread

import packet
from Color import color
from Buffer import Buffer


class Server:
    def __init__(self, port):
        self.port = port                # Server application port
        self.socket = None              # Server's UDP socket
        self.running = False
        self.debug = 0

        self.clients = []               # List of onnected clients
        self.client_ids = {}            # Index of connected client ids to their respective object reference
        self.host = None                # Reference to client that is host
        self.pending_acks = {}          # Index of pending acknowledgements to their status


    # Print message in console and send it to all clients
    def message(self, msg, col):                  
        data = bytearray(len(msg) + 2 + 1)                      # Length of packet + 1 each for packet padding and packet type
        struct.pack_into('BB', data, 0, 0, 3)                   # set up the packet (Padding, PacketType 3 for message)
        fmt = str(len(msg)) + 's'                               # set up format code for struct.pack_into (length of string + type string)
        struct.pack_into(fmt, data, 2, msg.encode('utf-8'))     # don't forget that offset arg (2 here) when writing to the bytearray!
        packet.send_all(self, data)
        print(col + msg + color.end)


    # track and deal with client timeouts
    def timeouts(self):
        while True:
            time.sleep(3)
            for x in self.clients:
                if ((time.time() - x.last_ping) > 3):           # if client's last ping was more than 3 seconds ago
                    x.disconnect(1)                             # disconnect the client, reason 1 means timeout



    # RLLY Basic, only use this loop for basic testing # # # # Perhaps add support for more than 2 connected players
    def basictick(self, tickrate):  
        while self.running:
            time.sleep(0.010)                                         # Sleep for 10 milliseconds (IMPORTANT TO REDUCE CPU USAGE)
            if (self.clients and not self.clients[0].queue.empty()):  # check if self.clients is not empty, and client 1's queue has data ##CHANGE TO HOST LATER 
                new_data = bytearray(12)                    # creates a buffer of 12 bytes  (do you need to destroy it when done?//memory leak?)
                struct.pack_into('BB', new_data, 0, 0, 4)   # set up the packet (Padding, PacketType)
                offset = 2                                  # define current offset for the buffer "new_data"

                for i in self.clients:                  # loop through connected clients and get their most recent data from their Queues
                    client_queue = i.queue

                    if (not client_queue.empty()):                  # if the queue isn't empty...
                        data_tuple = client_queue.get()             # data_tuple = (clientnumber, pos x, pos y)
                        struct.pack_into('<BHH', new_data, offset, data_tuple[0], data_tuple[1], data_tuple[2])
                        offset += 5
                        
                packet.send_all(self, new_data)       # send this packet to all clients! maybe in another thread?


        
    def gametick(self, tickrate):
        while self.running:
            time.sleep(0.010)                           # Sleep for 10 milliseconds
            if (self.host and self.host.new_packet):    # Check if we've received new tick packet from the host
                new_data = Buffer(512)                  # Create a new buffer of 512 bytes to hold outgoing packet data
                new_data.prepare_packet(10)

                new_data.offset = 150           # Go to start of player data
                for x in self.clients:                          
                    new_data.write_real('B', 1, x.id)           # write x's uid

                    new_data.write_real('H', 2, x.pos_x)        # write x's pos_x
                    new_data.write_real('H', 2, x.pos_y)        # write x's pos_y
                    new_data.write_real('B', 1, x.is_alive)     # write x's is_alive
                    new_data.write_real('f', 4, x.hull_angle)   # write x's hull_angle
                    new_data.write_real('f', 4, x.turret_angle) # write x's turret_angle

                    new_data.offset += 16                       # Advance to next player's data

                packet.send_all(self, new_data.data)    # send this packet to all clients! maybe in another thread?
                self.host.new_packet = False
 


    def start(self):
        self.running = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # configure socket for ipv4 and UDP
        self.socket.bind(("", 4296))                                   # "" means socket will listen to any network source on port 4296

        # set up and start the gamethread
        #gamethread = Thread(target=self.basictick, args=(60,))
        #gamethread.start()

        gamethread = Thread(target=self.gametick, args=(60,))
        gamethread.start()

        # set up and start timeout handler
        timethread = Thread(target=self.timeouts, args=())
        timethread.start()

        # packet handling loop
        while self.running: 
            data, ip = self.socket.recvfrom(1024)   # get the data sent to the server

            # unpack part of the data to find the packet type
            # data [1:2] is used to look at the first byte since Gamemaker 
            # pads sent out packets/buffers with 1 byte, the [0] looks at the first element in the returned tuple
            data_type = struct.unpack('B', data[1:2])[0] 
            
            # set up a thread to handle the packet type
            if (data_type == 1):    # PING
                t = Thread(target=packet.handle_ping, args=(self, ip, data))

            elif (data_type == 2):  # HANDSHAKE
                t = Thread(target=packet.handle_handshake, args=(self, ip, data))

            elif (data_type == 3):  # MESSAGE
                t = Thread(target=packet.handle_message, args=(self, ip, data))

            elif (data_type == 4):  # BASIC TICK
                t = Thread(target=packet.basic_tick, args=(self, ip, data))

            elif (data_type == 5):  # CONNECTION
                print(color.red + "got unhandled packet (connection)" + color.end)

            elif (data_type == 6):  # ACKNOWLEDGEMENT
                t = Thread(target=packet.handle_ack, args=(self, ip, data))

            elif (data_type == 10): # GAMETICK
                t = Thread(target=packet.handle_gametick, args=(self, ip, data))

            else:
                continue

            t.start()       # start the thread to handle the packet