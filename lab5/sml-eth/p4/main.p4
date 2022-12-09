#include <core.p4>
#include <v1model.p4>

typedef bit<9>  sw_port_t;   /*< Switch port */
typedef bit<48> mac_addr_t;  /*< MAC address */

const bit<16> TYPE_SML = 0x05FF // ?? Arbitrary for now, to be decided later I guess
const int NUM_WORKERS = 2;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header sml_t {
  /* TODO: Define me */
  int vector;
}

struct headers {
  ethernet_t eth;
  sml_t sml;
}

struct metadata { /* empty */ }

parser TheParser(packet_in packet,
                 out headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
  /* TODO: Implement me */
  state start {}
  
  state parse_ethernet {
    packet.extract(hdr.ethernet);
    transition select(hdr.ethernet.etherType) {
      TYPE_SML: parse_sml;
      default: accept;
    }
  }

  state parse_sml {
    packet.extract(hdr.sml_t);
    transition accept;
  }
}

int curr_aggregation_value = 0; // TODO is it allowed to store this here? Don't think so,
short num_chunks_received = 0;

control TheIngress(inout headers hdr,
                   inout metadata meta,
                   inout standard_metadata_t standard_metadata) {
                   
  broadcast_result(broadcast_value) {
  	hdr.sml.vector = broadcast_value;
  	standard_metadata.mcast_grp = 1;
  	//TODO: send stuff
  }
  
  reset() {
  	curr_aggregation_value = 0;
  	num_chunks_received = 0;
  }             
  
  apply {
    /* TODO: Implement me */
    curr_aggregation_value += hdr.sml.vector;
    
    if (++num_chunks_received == NUM_WORKERS) {
    	broadcast_result(curr_aggregation_value);
    	reset();
    } else {
    	mark_to_drop(standard_metadata);
    }
  }
}

control TheEgress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheChecksumVerification(inout headers hdr, inout metadata meta) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheChecksumComputation(inout headers  hdr, inout metadata meta) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheDeparser(packet_out packet, in headers hdr) {
  apply {
    /* TODO: Implement me */
    packet.emit(hdr.eth);
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
