from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from lib.comm import send, receive
from scapy.all import Packet, IntField
import socket
import struct

NUM_ITER   = 1     # TODO: Make sure your program can handle larger values
CHUNK_SIZE = 2 #None  # TODO: Define me
TYPE_SML = 0x05FF

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        # TODO: Implement me
        IntField('vector0', '0'), #TODO less hardcoded CHUNK_SIZE please
        IntField('vector1', '0')
    ]

def AllReduce(soc, rank, data, result):
    """
    Perform in-network all-reduce over UDP

    :param str    soc: the socket used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """

    for chunk_start in range(0, len(data), CHUNK_SIZE):
        pack = SwitchML(vector0 = data[chunk_start], vector1 = data[chunk_start + 1])
        send(soc, bytes(pack), ("10.0.2.255", 1))
        bytes_sent = 42 + len(pack)
        receive(soc, bytes_sent) # TODO currently reads own broadcast and discards it, inefficient
        
        vector = receive(soc, bytes_sent)[0]
        print('response', vector)
        
        for i in range(CHUNK_SIZE):
            result[chunk_start + i] = int.from_bytes(vector[(i*4):(i*4)+4], 'big')

    # TODO: Implement me
    # NOTE: Do not send/recv directly to/from the socket.
    #       Instead, please use the functions send() and receive() from lib/comm.py
    #       We will use modified versions of these functions to test your program

def main():
    rank = GetRankOrExit()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # TODO: Create a UDP socket.
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(("10.0.2.255", 1))
    # NOTE: This socket will be used for all AllReduce calls.
    #       Feel free to go with a different design (e.g. multiple sockets)
    #       if you want to, but make sure the loop below still works

    Log("Started...")
    for i in range(NUM_ITER):
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData("udp-iter-%d" % i, rank, data_out)
        print('data_out', data_out)
        AllReduce(s, rank, data_out, data_in)
        print('data_in', data_in)
        RunIntTest("udp-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()
