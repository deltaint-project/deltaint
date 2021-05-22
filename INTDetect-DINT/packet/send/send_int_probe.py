#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct
import time

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, get_if_addr
from scapy.all import Packet, ByteField, BitField
from scapy.all import Ether, IP, UDP, TCP

class Custom(Packet):
    fields_desc = [
            BitField("intopt", 0, 16),
            BitField("proto", 0, 16)
            ]

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface", flush=True)
        exit(1)
    return iface

def main():

    iface = get_if()

    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff', type=1793)
    #pkt = pkt / '\x00\x00' / '\x08\x00' / IP(src=get_if_addr(iface),dst='255.255.255.255')
    pkt = pkt / Custom(intopt=0x0000, proto=0x0800) / IP(src=get_if_addr(iface),dst='255.255.255.255')
    
    while True:
        sendp(pkt, iface=iface, verbose=False)
        print(pkt.show(dump=False), flush=True)
        time.sleep(1)
        


if __name__ == '__main__':
    main()
