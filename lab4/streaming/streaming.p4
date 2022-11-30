/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

const bit<16> TYPE_IPV4 = 0x800;
const bit<8> TYPE_UDP =  0x11;

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
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
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header rtp_t {
    bit<2>  version;
    bit<1>  padding;
    bit<1>  extension;
    bit<4>  CSRC_count;
    bit<1>  marker;
    bit<7>  payload_type;
    bit<16> sequence_number;
    bit<32> timestamp;
    bit<32> SSRC;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> hdr_length;
    bit<16> checksum;
}

const bit<8> EMPTY_FL    = 0;
const bit<8> RESUB_FL_1  = 1;
const bit<8> CLONE_FL_1  = 2;
const bit<8> RECIRC_FL_1 = 3;

struct metadata {  
    @field_list(RESUB_FL_1, CLONE_FL_1)
    bit<8>  f1;
    @field_list(RECIRC_FL_1)
    bit<16> f2;
    @field_list(CLONE_FL_1)
    bit<8>  f3;
    @field_list(RESUB_FL_1)
    bit<32> f4;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    udp_t        udp;
    rtp_t        rtp;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            8w0x11: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition parse_rtp;
    }

    state parse_rtp {
        packet.extract(hdr.rtp);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  
    }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
                    
    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    

    // TODO Make cloning/"mirroring" work
    action ipv4_clone(macAddr_t dstAddr1, egressSpec_t port1, macAddr_t dstAddr2, egressSpec_t port2) {
    	//log_msg("foo\n");
    	//log_msg("%s\n", hdr.ipv4.dstAddr);
        clone_preserving_field_list(CloneType.I2E, 5, CLONE_FL_1);

        ipv4_forward(dstAddr1, port1);    // still send original packet I guess?
    }
    
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_clone;
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 16384;
        default_action = drop();
    }

    apply {
        if (hdr.ipv4.isValid()) {
            ipv4_lpm.apply();
        }
    }

}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
                 
        
    table debug_ipv4_srcAddr {
        key = { hdr.ipv4.dstAddr : exact;
                standard_metadata.instance_type : exact; }
        actions = {}
    }

    apply {
        debug_ipv4_srcAddr.apply();    // just so debug_ipv4_srcAddr prints in the /streaming/logs files
        if (standard_metadata.instance_type == 2) {	// clone identification?
            standard_metadata.egress_spec = 3;
            hdr.ipv4.dstAddr = 0x0a000303; // 10.0.3.3
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {

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
    }

}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {

    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.rtp);
    }
    
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
