from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from scapy.all import *

NUM_ITER   = 1     # TODO: Make sure your program can handle larger values
CHUNK_SIZE = 16 #None  # TODO: Define me
TYPE_SML = 0x05FF

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        # TODO: Implement me
        IntField('vector', 0)
    ]

def AllReduce(iface, rank, data, result):    
    pack = Ether(type=TYPE_SML)/SwitchML(vector=data[0])
    response = srp1(pack, iface=iface)
    result[0] = int.from_bytes(response[Raw].load, 'big')

    """
    Perform in-network all-reduce over ethernet

    :param str  iface: the ethernet interface used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """
    # TODO: Implement me

def main():
    iface = 'eth0'
    rank = GetRankOrExit()
    Log("Started...", rank)
    for i in range(NUM_ITER):
        num_elem = 1 #GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData("eth-iter-%d" % i, rank, data_out)
        AllReduce(iface, rank, data_out, data_in)
        print(data_in) #TODO
        RunIntTest("eth-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()
