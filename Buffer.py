import struct

class Buffer:
    def __init__(self, size):
        self.data = bytearray(size)
        self.offset = 0


    def prepare_packet(self, packet_type):
        struct.pack_into('BB', self.data, self.offset, 0, packet_type)
        self.offset += 2


    def write_real(self, real_type, type_bytesize, value):
        fmt = '<' + real_type
        struct.pack_into(fmt, self.data, self.offset, value)
        self.offset += type_bytesize


    def write_string(self, string):
        string = string.encode('utf-8')
        fmt = str(len(string)) + 's'
        struct.pack_into(fmt, self.data, self.offset, string)
        self.offset += len(string)

