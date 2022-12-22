#include <core.p4>
#include <v1model.p4>

typedef bit<9>  sw_port_t;   /*< Switch port */
typedef bit<48> mac_addr_t;  /*< MAC address */

#define TYPE_SML 0x05FF
#define NUM_WORKERS 3
#define CHUNK_SIZE 63

/* DERIVED DEFINES */
#define VECTOR_LENGTH_BITS (CHUNK_SIZE * 32)
#define VECTOR_INDICES VECTOR_LENGTH_BITS+7:8
#define NUM_CHUNKS_RECEIVED_INDICES 7:0

header ethernet_t {
  mac_addr_t dstAddr;
  mac_addr_t srcAddr;
  bit<16>   etherType;
}

header sml_t {
  bit<VECTOR_LENGTH_BITS> vector;
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
  state start {
    transition parse_ethernet;
  }
  
  state parse_ethernet {
    packet.extract(hdr.eth);
    transition select(hdr.eth.etherType) {
      TYPE_SML: parse_sml;
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

  register<bit<(VECTOR_LENGTH_BITS + 8)>>(1) reg;

  apply {
    bit<(VECTOR_LENGTH_BITS + 8)> reg_val;
    @atomic {
      reg.read(reg_val, 0);						//Read register
									
      reg_val[NUM_CHUNKS_RECEIVED_INDICES] = reg_val[NUM_CHUNKS_RECEIVED_INDICES] + 1;	//Update values in register
      reg_val[VECTOR_INDICES] = reg_val[VECTOR_INDICES] + hdr.sml.vector;

      if (reg_val[NUM_CHUNKS_RECEIVED_INDICES] == NUM_WORKERS) {	// If all chunks received
        hdr.sml.vector = reg_val[VECTOR_INDICES];			// Broadcast the aggregation results
        standard_metadata.mcast_grp = 1;
    	reg.write(0, 0);						// Clear register for reuse
      } else {
        reg.write(0, reg_val);					// Write updated values to register
        mark_to_drop(standard_metadata);
      }
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
