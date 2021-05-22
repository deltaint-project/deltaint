# -*- coding:utf-8 -*-

import socket
from sys import argv
import json
from bitstring import BitArray, BitStream
import time
import threading
import struct
import os
import json

with open("../config.json", "r") as f:
    sendint_config = json.load(f)

class PacketSender(object):
    """
    INT Packet Sender
    """

    def __init__(self, port):
        """
        Initialization socket link to controller

        :param port: INT sending port
        """
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', self.port))
        self.s.listen(10)
        #self.s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        #self.s.bind(('h{}-eth1'.format(argv[1]), socket.htons(0x0003)))
        self.typeDict = {
            'TraversePath': self.doTraversePath,
            'Test': self.doTest
        }
        self.socket_list = {}

    def startSocket(self):
        """
        start socket link to controller
        """
        while True:
            conn, addr = self.s.accept()

            self.socketClient(conn, addr)

    def socketClient(self, conn, addr):
        """
        Send data by type

        :param conn: receive data from controller circulate
        :param addr: not be used
        """
        while True:
            data = conn.recv(4096).decode('utf-8')
            #pkt = self.s.recv(4096)
            #_, port, data = struct.unpack("!12sH{}s".format(len(pkt)-4), pkt)
            #if port == self.port and data: # 8888
            if data:
                dataJson = json.loads(data)
                dataType = dataJson.get('type')
                dataInfo = dataJson.get('info')

                print("Receive instruction from controller: type: {}, info: {}!".format(dataType, dataInfo), flush=True)
                self.typeDict.get(dataType, self.doDefault)(dataInfo)

    def doDefault(self, info):
        """
        Default action
        """

    def doTest(self, info):
        """
        Test action
        """
        pass

    def doTraversePath(self, info):
        """
        Traverse INT using given path 

        :param info: traverse path information
        """
        def sendUDP(content, address):
            """
            Send traverse path via UDP

            :param content: traverse route content (512-bit source routing + 32-bit act ID)
            :param address: traverse target address
            """
            # Remember socket for each path
            if content not in self.socket_list.keys():
                udpLink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket_list[content] = udpLink
            else:
                udpLink = self.socket_list[content]
            addr = (address, 2222)
            udpLink.sendto(content, addr)
            print("Send packet along {} to {}".format(content, addr), flush=True)

        def byteDateToSend(byteRoute, actId):
            """
            Convert traverse route byte info to a formatted byte info

            :param byteRoute: traverse route byte info
            :param actId: action id from controller
            :returns: a formatted byte info
            """
            actIdBin = bin(actId)[2:]
            actIdBinStr = '0' * (32 - int(len(actIdBin)) % 32) + actIdBin
            byteRouteStr = '0' * \
                (512 - int(len(byteRoute)) % 512) + byteRoute
            byteStr = byteRouteStr + actIdBinStr
            byteContent = BitArray('0b' + byteStr).bytes
            return byteContent

        def addRoute(port):
            """
            Convert a route switch port to route byte info

            :param port: a switch port in route
            :returns: a prttied binary port string
            """
            portOct = int(port) - 1 # Start from 0 <- Start from eth-1
            portBin = bin(portOct)[2:] # Skip '0b'
            #portBinPretty = '0' * ((4 - int(len(portBin))) % 4) + portBin
            portBinPretty = '0' * ((8 - int(len(portBin))) % 8) + portBin # Use 8-bit to support large network scale
            return portBinPretty

        def sendPacketByTimes(sendTimes, byteContent, address):
            """
            Send INT packet in the given number of times

            :param sendTimes: the number of times
            :param byteContent: the content to be send
            :param address: the target host IP address 
            """
            sleepTime = 10/sendTimes
            for i in range(10000):
                sendUDP(byteContent, address)
                time.sleep(sleepTime)

        def sendPacketByTime(sendTime, byteContent, address, actId):
            """
            Send INT packet in the given time

            :param sendTimes: the time to send packet
            :param byteContent: the content to be send
            :param address: the target host IP address 
            :param actId: the action ID receive from controller
            """
            startTime = time.time()
            i = 0
            times = 0
            while time.time() - startTime < sendTime:
                sendUDP(byteContent, address)
                i = i + 1

                sleepTime = float(sendint_config["epoch_len"]) # Epoch length
                time.sleep(sleepTime)
                times = times + 1
            endTime = time.time()
            p_rate = i / (endTime - startTime)

        actId = info.get('actId')
        sendTimes = info.get('sendTimes')

        addressList = info.get('addressList')
        portsLists = info.get('portsLists')
        listLen = len(portsLists)
        for i in range(listLen):
            portsList = portsLists[i]
            address = addressList[i]
            byteRoute = ''
            portsList.reverse()
            for port in portsList:
                byteRoute = byteRoute + addRoute(port)
            print("byte route: {}, act id: {}".format(byteRoute, actId), flush=True)
            byteContent = byteDateToSend(byteRoute, actId)

            # send packet async
            thread = threading.Thread(target=sendPacketByTime, args=(
                sendTimes, byteContent, address, actId))
            thread.setDaemon(False)
            thread.start()

    def __del__(self):
        self.s.close()


if __name__ == '__main__':
    curdir = os.path.dirname(os.path.abspath(__file__))
    sysdir = os.path.dirname(curdir)

    ps = PacketSender(8888)
    ps.startSocket()
