/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>
 
#define PKT_INSTANCE_TYPE_INGRESS_CLONE 1
 
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<16> etherType_t;
 
 
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/
 
 
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    etherType_t etherType;
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
 
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> hdr_length;
    bit<16> checksum;
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
 
struct headers {
    ethernet_t  ethernet;
    ipv4_t      ipv4;
    udp_t       udp;
    rtp_t       rtp;
}
 
struct metadata {}
 
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
 
    action clone_packet() {
        const bit<32> REPORT_MIRROR_SESSION_ID = 500;
        clone(CloneType.I2E, REPORT_MIRROR_SESSION_ID);
    }
 
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        default_action = drop();
        size = 16384;
    }
    apply {
        if (hdr.ipv4.isValid()) {
            if ((hdr.ipv4.dstAddr == 0x0a000707 && hdr.ipv4.srcAddr == 0x0a000101) || (hdr.ipv4.dstAddr == 0x0a000101 && hdr.ipv4.srcAddr == 0x0a000707)) {
                clone_packet();
            }
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

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action change_h1_to_h7_addr() {
        standard_metadata.egress_spec = 0x3;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = 0x080000000333;
        hdr.ipv4.dstAddr = 0x0a000303;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
 
    apply {
 
        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE) {
            if (hdr.ipv4.dstAddr == 0x0a000707) {
                change_h1_to_h7_addr();
            }
            else{
                drop();
            }
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
