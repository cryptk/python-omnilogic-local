#!/usr/bin/env python3

import socket
import struct
import random
import time
import xml.etree.ElementTree as ET

TELEMETRY_REQUEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<Request xmlns="http://nextgen.hayward.com/api">
  <Name>RequestTelemetryData</Name>
</Request>"""


class OmniLogicRequest(object):
    HEADER_FORMAT = "!LQ4sLBBBB"
    def __init__(self, msgId, msgType, extraData=""):
        self.msgId = msgId
        self.msgType = msgType
        self.extraData = bytes(extraData, "utf-8")

        self.version = "1.19".encode("ascii")

    def toBytes(self):
        retval = struct.pack(OmniLogicRequest.HEADER_FORMAT, 
                             self.msgId,      # Msg id
                             int(time.time_ns()/(10**9)),   # Timestamp
                             bytes(self.version), # version string
                             self.msgType,    # OpID/msgType
                             1,               # Client type
                             0, 0, 0)         # reserved
        return retval + self.extraData

    def fromBytes(data):
        # split the header and data 
        header = data[0:24]
        rdata = data[24:]

        msgId, tstamp, vers, msgType, clientType, res1, res2, res3 = struct.unpack(OmniLogicRequest.HEADER_FORMAT, header)
        return msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data[24:]


class OmniLogicAPI(object):
    def __init__(self, controllerIpAndPort, senderPort, responseTimeout):
        self.controllerIpAndPort = controllerIpAndPort
        self.senderPort = senderPort
        self.responseTimeout = responseTimeout

    def getSock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        sock.bind(("0.0.0.0", self.senderPort))
        return sock

    def getConfig(self):
        sock = self.getSock()

        # Send get config request
        self._sendRequest(sock, 1)

        # Wait for the Lead Message
        data = self._receiveFile(sock)

        return data

    def getLogConfig(self):
        sock = self.getSock()

        # Send get config request
        self._sendRequest(sock, 31)

        # Wait for the Lead Message
        data = self._receiveFile(sock)

        return data


    def getTelemetry(self):
        sock = self.getSock()

        # Send get config request
        # 300
        # 304
        # 305
        # 977
        # 1003
        msgType = 1
        #data = self._sendRequest(sock, msgType, "\0\0\0\0\0\0\0\0" + TELEMETRY_REQUEST_XML + "\0")
        data = self._sendRequest(sock, msgType, TELEMETRY_REQUEST_XML + "\0")
        #data = self._sendRequest(sock, msgType) #, TELEMETRY_REQUEST_XML)
        print(1, data)

        # wait for the telemetry data
        msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = self._recv(sock)
        print(2, data)

        # Send an ack
        self._sendAck(sock, msgId)

        return data


    def _sendRequest(self, sock, msgType, extraData=""):
        # Good security practice, random msgId's. 
        msgId = random.randrange(2**32)

        request = OmniLogicRequest(msgId, msgType, extraData)

        sock.sendto(request.toBytes(), self.controllerIpAndPort)

        # wait for the ACK resp
        msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = self._waitForData(sock, msgId)
        print(msgId, tstamp, vers, msgType, clientType, res1, res2, res3)

        return data

    def _receiveFile(self, sock):
        # This handles when we get a LeadMessage. if the length of the file we 
        # requested is < 1024 bytes, then all the data is in this first packet
        # Otherwise we need to read "MsgBlockCount" number of BlockMessages.

        # TODO, there's two possible ways this goes. This follows mine, which is the > 1024 possibility
        # This will give is a new msgid, and is the leadMessage
        msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = self._recv(sock)

        # Send an ack
        self._sendAck(sock, msgId)

        # Parse XML
        root = ET.fromstring(data[:-1]) #strip trailing \x00
        blockCount = int(root.findall(".//*[@name='MsgBlockCount']")[0].text)

        # Wait for the block data data
        retval = ""
        for x in range(blockCount):
            msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = self._recv(sock)
            self._sendAck(sock, msgId)
            retval += data[8:].decode('utf-8') # Strip an 8byte header

        return retval


    def _sendAck(self, sock, msgId):
        request = OmniLogicRequest(msgId, 1002)
        sock.sendto(request.toBytes(), self.controllerIpAndPort)

    def _recv(self, sock):
        resp = sock.recvfrom(65565)
        msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = OmniLogicRequest.fromBytes(resp[0])
        return msgId, tstamp, vers, msgType, clientType, res1, res2, res3, data

    def _waitForData(self, sock, msgId):
        respMsgId = -1
        start = time.time()
        sock.settimeout(0.5)
        while respMsgId != msgId and time.time() < start + self.responseTimeout:
            try:
                respMsgId, tstamp, vers, msgType, clientType, res1, res2, res3, data = self._recv(sock)
                if msgId == respMsgId:
                    return respMsgId, tstamp, vers, msgType, clientType, res1, res2, res3, data
            except socket.timeout:
                pass
        raise Exception() # timeout


def scan(api, start, end):
    sock = api.getSock()
    for x in range(start,end):
        time.sleep(1)
        print("Attempting %d" % x)
        try:
            data = api._sendRequest(sock, x, TELEMETRY_REQUEST_XML)
            print("FOUND SOMETHING :%d" % x)
        except:
            pass

if __name__ == "__main__":
    api = OmniLogicAPI(("192.168.1.134", 10444), 10444, 5)

    #cfg = api.getConfig()
    #print(cfg)

    #logConfig = api.getLogConfig()
    #print(logConfig)

    telem = api.getTelemetry()
    print(telem)

    # Nums in the request that get an ack, but nothing else:
    # 300
    # 304
    # 305
    # 977
    # 1003

    #start = 1800
    #end = start + 200
    #scan(api, start, end)

