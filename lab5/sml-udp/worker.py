from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from lib.comm import send, receive
from scapy.all import Packet, IntField, FieldListField
import socket

NUM_ITER   = 4
CHUNK_SIZE = 63
PORT_SML   = 11037

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        FieldListField("vector", None, IntField('element', 0))
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
        pack = SwitchML(vector=data[chunk_start:chunk_start + CHUNK_SIZE])
        send(soc, bytes(pack), ("10.0.2.15", PORT_SML))
        response = receive(soc, 42 + len(pack))[0]
        result[chunk_start:chunk_start + CHUNK_SIZE] = [int.from_bytes(response[i:i+4], 'big') for i in range(0, len(response), 4)]

def main():
    rank = GetRankOrExit()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	# Create UDP Socket
    s.bind(("10.0.2.255", PORT_SML))

    Log("Started...")
    for i in range(NUM_ITER):
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData("udp-iter-%d" % i, rank, data_out)
        AllReduce(s, rank, data_out, data_in)
        RunIntTest("udp-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()
