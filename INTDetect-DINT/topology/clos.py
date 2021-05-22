from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from p4_mininet import P4Switch, P4Host

import argparse
import time
import os
import sys
import random
import subprocess

os.system("sudo rm ../controller/tmp/*")
os.system("sudo mn -c")

curdir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description='CLOS architecture topology')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", default="{}/../bmv2_model/simple_switch".format(curdir))
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", default=9090)
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", default="{}/../p4_source_code/my_int.json".format(curdir))
parser.add_argument('--nodes-list', help='Number of spine, leaf, tor, host, pod',
                    type=int, nargs='*', default=[2,2,2,2,2])
parser.add_argument('--pcap-dump', help='Dump packets on interfaces to pcap files',
                    type=str, action="store", required=False, default=False)
args = parser.parse_args()


class clos(Topo):

    def __init__(self, behavioral_exe, thrift_port, json, nodes_list, pcap_dump, **opts):

        Topo.__init__(self, **opts)

        spine_num = nodes_list[0]
        set_num = nodes_list[1]
        leaf_num = nodes_list[1]
        tor_num = nodes_list[2]
        h_num = nodes_list[3]
        pod_num = nodes_list[4]

        self.spine_sw_list = []
        self.leaf_sw_list = []
        self.tor_sw_list = []
        self.h_list = []

        device_id=0
        for i in range(set_num):
            self.spine_sw_list.append([])
            for j in range(spine_num):
                sw = self.addSwitch('s%d_s%d' % (i + 1, j + 1),
                                    sw_path=behavioral_exe,
                                    json_path=json,
                                    thrift_port=thrift_port,
                                    nanolog="ipc:///tmp/bm-%d-log.ipc"%device_id,
                                    device_id=device_id,
                                    pcap_dump=pcap_dump)
                self.spine_sw_list[i].append(sw)
                thrift_port+= 1
                device_id+=1

        for i in range(pod_num):
            self.leaf_sw_list.append([])
            for j in range(leaf_num):
                sw = self.addSwitch('p%d_l%d' % (i + 1, j + 1),
                                    sw_path=behavioral_exe,
                                    json_path=json,
                                    thrift_port=thrift_port,
                                    nanolog="ipc:///tmp/bm-%d-log.ipc"%device_id,
                                    device_id=device_id,
                                    pcap_dump=pcap_dump)
                self.leaf_sw_list[i].append(sw)
                thrift_port = thrift_port + 1
                device_id+=1

        for i in range(pod_num):
            self.tor_sw_list.append([])
            for j in range(tor_num):
                sw = self.addSwitch('p%d_t%d' % (i + 1, j + 1),
                                    sw_path=behavioral_exe,
                                    json_path=json,
                                    thrift_port=thrift_port,
                                    nanolog="ipc:///tmp/bm-%d-log.ipc"%device_id,
                                    device_id=device_id,
                                    pcap_dump=pcap_dump)
                self.tor_sw_list[i].append(sw)
                thrift_port = thrift_port + 1
                device_id+=1

        for i in range(pod_num):
            self.h_list.append([])
            for j in range(tor_num):
                self.h_list[i].append([])
                for k in range(h_num):
                    h = self.addHost('p%d_t%d_%d' % (i + 1, j + 1,k+1),ip="10.%d.%d.%d"%(i+1,j+1,k+1))
                    self.h_list[i][j].append(h)

        for i in range(set_num):
            for j in range(spine_num):
                for k in range(pod_num):
                    self.addLink(self.spine_sw_list[i][j], self.leaf_sw_list[k][i])

        for i in range(pod_num):
            for j in range(leaf_num):
                for k in range(tor_num):
                    self.addLink(self.leaf_sw_list[i][j], self.tor_sw_list[i][k])

        for i in range(pod_num):
            for j in range(tor_num):
                for k in range(h_num):
                    self.addLink(self.h_list[i][j][k], self.tor_sw_list[i][j])


def main():

    #nodes_list = map(int, args.nodes_list)
    nodes_list = args.nodes_list
    print(nodes_list, flush=True)
    topo = clos(args.behavioral_exe,
                args.thrift_port,
                args.json,
                nodes_list,
                args.pcap_dump)
    net = Mininet(topo=topo,
                  host=P4Host,
                  switch=P4Switch,
                  controller=None)

    net.start()

    os.system("sh {}/../flow_table/command.sh".format(curdir))

    for i in range(nodes_list[4]):
        for j in range(nodes_list[2]):
            for k in range(nodes_list[3]):
                h=net.get(topo.h_list[i][j][k])
                #if i == 1 and j == 0 and k == 0 :
                #    h.cmd("python3 {}/../packet/receive/receive.py >p2_t1_1_receive.out 2>&1 &".format(curdir))
                h.cmd("python3 {}/../packet/receive/receive.py >/dev/null &".format(curdir))
                #if i == 0 and j == 0 and k == 0:
                #    h.cmd("python3 {}/../packet/send/send_int_probe.py >p1_t1_send.out 2>&1 &".format(curdir))
                h.cmd("python3 {}/../packet/send/send_int_probe.py >/dev/null &".format(curdir))

    #cmdstr = "python3 {}/../controller/controller.py >controller.out &".format(curdir)
    #rs = os.system(cmdstr) # rs = exit code
    #proc = subprocess.Popen(cmdstr, shell=True) # If shell = True, it returns the pid of the shell, and cmdstr becomes its child process
    f = open("controller.out", "w")
    proc = subprocess.Popen(["python3", "{}/../controller/controller.py".format(curdir), "&"], stdout=f, stderr=f, shell=False)
    print("Start controller: [{}]!".format(proc.pid), flush=True)

    time.sleep(3) # Wait their initialization
    
    # Test
    print("Start test!", flush=True)
    random.seed(0)
    for i in range(1):
        tmplink = random.choice(net.links)
        snode_name = tmplink.intf1.node.name
        dnode_name = tmplink.intf2.node.name
        print("Cut down link {}, snode_name: {}, dnode_name: {}\n".format(i, snode_name, dnode_name), flush=True)
        net.configLinkStatus(snode_name, dnode_name, "down")
        time.sleep(5)
        net.configLinkStatus(snode_name, dnode_name, "up")
        print("Recover link {}, snode_name: {}, dnode_name: {}\n".format(i, snode_name, dnode_name), flush=True)
    print("Finish test!", flush=True)

    #CLI(net)

    print("Kill controller!", flush=True)
    proc.terminate()
    f.close()

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()
