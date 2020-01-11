

class Client:

    def __init__(self, id, ip, server):
        self.id = id                            # unique client id
        self.ip = ip                            # client ip address (and port)
        self.server = server                    # reference to main server
        self.handshake_status = 0               # defaults 0, 1 when client has completed 3 way handshake for connection
        self.tick_data = None                   #

        self.x = None
        self.y = None

    def connect():
        return 0

    def disconnect():
        return 0