from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from scapy.all import *

NUM_ITER   = 5
CHUNK_SIZE = 63
TYPE_SML   = 0x05FF

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        FieldListField("vector", None, IntField('element', 0))
    ]

def AllReduce(iface, rank, data, result):
    """
    Perform in-network all-reduce over ethernet

    :param str  iface: the ethernet interface used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """
    for chunk_start in range(0, len(data), CHUNK_SIZE):
        pack = Ether(type=TYPE_SML)/SwitchML(vector=data[chunk_start:chunk_start + CHUNK_SIZE])
        response = srp1(pack, iface=iface)
        response_load = response[Raw].load
        result[chunk_start:chunk_start + CHUNK_SIZE] = [int.from_bytes(response_load[i:i+4], 'big') for i in range(0, len(response_load), 4)]

def main():
    iface = 'eth0'
    rank = GetRankOrExit()
    Log("Started...", rank)
    for i in range(NUM_ITER):
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData("eth-iter-%d" % i, rank, data_out)
        AllReduce(iface, rank, data_out, data_in)
        RunIntTest("eth-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()
