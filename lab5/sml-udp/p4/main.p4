#include <core.p4>
#include <v1model.p4>

typedef bit<9>  sw_port_t;   /*< Switch port */
typedef bit<48> mac_addr_t;  /*< MAC address */
typedef bit<32> ip4_addr_t;  /*< IPv4 address */

const bit<16> TYPE_SML = 0x05FF; // ?? Arbitrary for now, to be decided later I guess
const int NUM_WORKERS = 3;
const int CHUNK_SIZE = 2;

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
  bit<32> vector0;
  bit<32> vector1;
}

struct headers {
  ethernet_t ethernet;
  ipv4_t ipv4;
  udp_t udp;
  sml_t sml;
}

struct metadata { /* empty */ }

parser TheParser(packet_in packet,
                 out headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
  /* TODO: Implement me */
  state start {
    transition parse_ethernet;
  }
  
  state parse_ethernet {
    packet.extract(hdr.ethernet);
    packet.extract(hdr.ipv4);
    packet.extract(hdr.udp);
    packet.extract(hdr.sml);
    transition accept;
    /*transition select(hdr.ethernet.etherType) {
      TYPE_SML: parse_sml;
      default: accept;
    }*/
  }

  state parse_sml {
    packet.extract(hdr.ipv4);
    packet.extract(hdr.udp);
    packet.extract(hdr.sml);
    transition accept;
  }
}

control TheIngress(inout headers hdr,
                   inout metadata meta,
                   inout standard_metadata_t standard_metadata) {

  table debug {
    key = { hdr.ethernet.etherType : exact;
            hdr.sml.vector0 : exact;
            hdr.sml.vector1 : exact;
            standard_metadata.mcast_grp : exact;
            hdr.ipv4.hdrChecksum : exact; }
    actions = {}
  }

  register<bit<72>>(128) reg;

  apply {
    /* TODO: Implement me */
    bit<72> tmp;
    bit<32> curr_aggregation_value1;
    bit<32> curr_aggregation_value0;
    bit<8> num_chunks_received;
    
    @atomic {
    	reg.read(tmp, 0);

    	curr_aggregation_value1 = tmp[71:40];
    	curr_aggregation_value0 = tmp[39:8];
    	num_chunks_received = tmp[7:0];

    	curr_aggregation_value0 = curr_aggregation_value0 + hdr.sml.vector0;
    	curr_aggregation_value1 = curr_aggregation_value1 + hdr.sml.vector1;
    	num_chunks_received = num_chunks_received + 1;

    	if (num_chunks_received == NUM_WORKERS) {
    	    hdr.sml.vector0 = curr_aggregation_value0;
    	    hdr.sml.vector1 = curr_aggregation_value1;

    	    hdr.ipv4.srcAddr = 0x0A00020f;
    	    standard_metadata.mcast_grp = 1;

    	    reg.write(0, 0);	// clear register for reuse
        } else {
            reg.write(0, curr_aggregation_value1 ++ curr_aggregation_value0 ++ num_chunks_received);	// save data to register
            mark_to_drop(standard_metadata);
        }
    }
    debug.apply();
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
	      hdr.sml.vector0,
	      hdr.sml.vector1 },
	    hdr.udp.checksum,
	    HashAlgorithm.csum16
	);

  }
}

control TheDeparser(packet_out packet, in headers hdr) {
  apply {
    /* TODO: Implement me */
    packet.emit(hdr.ethernet);
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
