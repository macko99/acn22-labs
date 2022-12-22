from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from lib.comm import send, receive, unreliable_send, unreliable_receive
from scapy.all import Packet, ByteField, IntField, FieldListField
import socket

NUM_ITER   = 2
CHUNK_SIZE = 63
PORT_SML   = 11037

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        ByteField("rank", None),
        ByteField("chunk_num", None),
        FieldListField("vector", None, IntField('element', 0))
    ]

def AllReduce(soc, rank, data, result):
    """
    Perform reliable in-network all-reduce over UDP
    :param str    soc: the socket used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector
    This function is blocking, i.e. only returns with a result or error
    """
    for chunk_num in range(1, int(len(data) / CHUNK_SIZE) + 1):
        chunk_start = (chunk_num - 1) * CHUNK_SIZE
        pack = SwitchML(rank = rank, chunk_num = chunk_num, vector=data[chunk_start:chunk_start + CHUNK_SIZE])

        response_received = False
        while not response_received:
            try:
            	#note low failure chances on unreliable_ calls to speed up testing/grading/etc
                unreliable_send(soc, bytes(pack), ("10.0.2.15", PORT_SML), 1, 0.05)
                response = unreliable_receive(soc, 42 + len(pack), 0.05)[0]
            except socket.timeout:
                pass
            else:
                if (response[1] == chunk_num):	#if the chunk_num of the incoming packet doesn't match the current chunk_num, retry
                    result[chunk_start:chunk_start + CHUNK_SIZE] = [int.from_bytes(response[i:i+4], 'big') for i in range(2, len(response), 4)]
                    response_received = True

def main():
    rank = GetRankOrExit()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)	# Create UDP Socket
    s.bind(("10.0.2.255", PORT_SML))
    s.settimeout(1)						# Set 1-second timeout on receives

    Log("Started...")
    for i in range(NUM_ITER):
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData("udp-rel-iter-%d" % i, rank, data_out)
        #print('data_out', data_out[:10])
        AllReduce(s, rank, data_out, data_in)
        #print('data_in', data_in[:10])
        RunIntTest("udp-rel-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()
