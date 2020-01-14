import time
import queue

import packet
from Color import color

class Client:

    def __init__(self, id, ip, server, username):
        self.id = id                            # unique client id
        self.ip = ip                            # client network address
        self.username = username                # ingame username
        self.server = server                    # reference to main server
        self.handshake = False                  # whether client has completed handshake
        self.last_ping = time.time()            # time of last ping                 
        self.queue = queue.Queue(0)             # TODO Fix queue out of sync bug
        self.connected = False

        # Unused
        self.tick_data = None 
        self.new_packet = False                 # Whether a new packet has arrived (gameloop resets this to false)
        self.is_host = False                    # Whether client is host
        self.x = None
        self.y = None
        self.hull_angle = None
        self.turret_angle = None



    def connect(self):
        self.connected = True

        if (self.server.host == None):                  # Set this client as host if the server has none
            self.server.host = self
            self.is_host = True

        packet.send_connection(self.server, 0, self)    # Send ids and usernames of connected clients to this client
        packet.send_connection(self.server, 1, self)    # Tell all clients this client has connected

        self.server.clients.append(self)                # Add this client to list of hosts
        self.server.client_ids[self.id] = self          # Add this client's id to Index

        time.sleep(1)

        if (self.handshake == False):                   # Disconnect if client hasn't completed handshake
            self.disconnect(0)
        else:
            msg = self.username + " connected!"
            self.server.message(msg, color.green)
            
              


    def disconnect(self, reason):
        self.connected = False
        packet.send_connection(self.server, 3, self)     # Tell all clients this client has disconnected

        if (reason == 0):               # Failed handshake
            msg = self.username + " disconnected (failed handshake)"
            self.server.message(msg, color.red)

        if (reason == 1):               # Timeout
            msg = self.username + " disconnected (timed out)"
            self.server.message(msg, color.red)


        self.server.clients.remove(self)
        self.server.client_ids.pop(self.id)