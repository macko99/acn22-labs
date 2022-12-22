#include <core.p4>
#include <v1model.p4>

typedef bit<9>  sw_port_t;   /*< Switch port */
typedef bit<48> mac_addr_t;  /*< MAC address */
typedef bit<32> ip4_addr_t;  /*< IPv4 address */

#define PORT_SML 11037
#define NUM_WORKERS 2
#define CHUNK_SIZE 63

/* DERIVED DEFINES */
#define VECTOR_LENGTH_BITS (CHUNK_SIZE * 32)
#define WORK_RECEIVED_MASK (0b11111111 >> (8 - NUM_WORKERS))
#define VECTOR_INDICES VECTOR_LENGTH_BITS+15:16
#define WORK_RECEIVED_INDICES 15:8
#define CHUNK_NUM_INDICES 7:0

header ethernet_t {
  mac_addr_t dstAddr;
  mac_addr_t srcAddr;
  bit<16>   etherType;
}

header ipv4_t {
  bit<4>    version;
  bit<4>    ihl;
  bit<8>    diffserv;
  bit<16>   totalLen;
  bit<16>   identification;
  bit<3>    flags;
  bit<13>   fragOffset;
  bit<8>    ttl;
  bit<8>    protocol;
  bit<16>   hdrChecksum;
  ip4_addr_t srcAddr;
  ip4_addr_t dstAddr;
}

header udp_t {
  bit<16> srcPort;
  bit<16> dstPort;
  bit<16> hdr_length;
  bit<16> checksum;
}

header sml_t {
  bit<8> rank;
  bit<8> chunk_num;
  bit<VECTOR_LENGTH_BITS> vector;
}

struct headers {
  ethernet_t eth;
  ipv4_t ipv4;
  udp_t udp;
  sml_t sml;
}

struct metadata { /* empty */ }

parser TheParser(packet_in packet,
                 out headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
  state start {
    transition parse_ethernet;
  }

  state parse_ethernet {
    packet.extract(hdr.eth);
    transition select(hdr.eth.etherType) {
      0x0800: parse_ipv4;
      default: accept;
    }
  }

  state parse_ipv4 {
    packet.extract(hdr.ipv4);
    transition select(hdr.ipv4.protocol) {
      0x11: parse_udp;
      default: accept;
    }
  }

  state parse_udp {
    packet.extract(hdr.udp);
    transition select(hdr.udp.srcPort) {
      PORT_SML: parse_sml;
      // no default, non-SML packets are dropped
    }
  }

  state parse_sml {
    packet.extract(hdr.sml);
    transition accept;
  }
}

control TheIngress(inout headers hdr,
                   inout metadata meta,
                   inout standard_metadata_t standard_metadata) {

  register<bit<(VECTOR_LENGTH_BITS + 16)>>(2) reg;
  
  action broadcast(bit<(VECTOR_LENGTH_BITS + 16)> reg_val) {
      hdr.sml.rank = 0xff;
      hdr.sml.vector = reg_val[VECTOR_INDICES];
      hdr.eth.dstAddr = 0xffffffffffff;
      hdr.eth.srcAddr = 0x0000000000ff;
      hdr.ipv4.dstAddr = 0x0A0002ff;
      hdr.ipv4.srcAddr = 0x0A00020f;
      standard_metadata.mcast_grp = 1;
  }

  apply {
    bit<(VECTOR_LENGTH_BITS + 16)> reg_val;
    bit<8> rank_mask = (8w1 << hdr.sml.rank);
    bit<32> chunk_is_odd = (bit<32>) hdr.sml.chunk_num & 1;

    @atomic {
    	reg.read(reg_val, chunk_is_odd);				// Read odd register for odd chunks and even register for even chunks

	if (hdr.sml.chunk_num != reg_val[CHUNK_NUM_INDICES]) {	// If incoming chunk_num is not what we're storing,
	    reg_val = 0;						// Clear old data as it's either (chunk_num - 2) or a new iteration
	    reg_val[CHUNK_NUM_INDICES] = hdr.sml.chunk_num; 		// and reuse its space for chunk_num
	}

	if (reg_val[WORK_RECEIVED_INDICES] & rank_mask == 0) {	// If chunk from this worker not yet received, aggregate values
	    reg_val[WORK_RECEIVED_INDICES] = reg_val[WORK_RECEIVED_INDICES] | rank_mask;
	    reg_val[VECTOR_INDICES] = reg_val[VECTOR_INDICES] + hdr.sml.vector;
	}
    	
    	if (reg_val[WORK_RECEIVED_INDICES] == WORK_RECEIVED_MASK) {	// If all work received for this chunk
    	    broadcast(reg_val);
        } else {
            mark_to_drop(standard_metadata);
        }

        reg.write(chunk_is_odd, reg_val);				// Write updated values to correct register
    }
  }
}

control TheEgress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
  apply {
  }
}

control TheChecksumVerification(inout headers hdr, inout metadata meta) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheChecksumComputation(inout headers hdr, inout metadata meta) {
  apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
        
	update_checksum(
	hdr.udp.isValid(),
	    { hdr.ipv4.srcAddr,
	      hdr.ipv4.dstAddr,
	      8w0,
	      hdr.ipv4.protocol,
	      hdr.udp.hdr_length,
	      hdr.udp.srcPort,
	      hdr.udp.dstPort,
	      hdr.udp.hdr_length,
	      hdr.sml.rank,
	      hdr.sml.chunk_num,
	      hdr.sml.vector },
	    hdr.udp.checksum,
	    HashAlgorithm.csum16
	);

  }
}

control TheDeparser(packet_out packet, in headers hdr) {
  apply {
    packet.emit(hdr.eth);
    packet.emit(hdr.ipv4);
    packet.emit(hdr.udp);
    packet.emit(hdr.sml);
  }
}

V1Switch(
  TheParser(),
  TheChecksumVerification(),
  TheIngress(),
  TheEgress(),
  TheChecksumComputation(),
  TheDeparser()
) main;
