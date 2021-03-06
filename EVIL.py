


###Outline for socket.py

import socket
import threading
import Queue

import connection
import util
from util import debugLog
import random
import copy
import select

class Evil:
    BUFSIZE = 1000

    def __init__(self):

        self.connections = {}
        self.connectionsLock = threading.Lock()
        self.unknownPackets = Queue.Queue()

        self.outgoingPackets = Queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.maxWindowSize = 3
        self.isClosed = False

    def listener(self):
        debugLog("listenerThread started on port " + str(self.sock.getsockname()[1]))

        while True:
            debugLog("receiving")
            ready = select.select([self.sock], [], [], 5)
            if self.isClosed:
                break
            if (ready[0]):
                msg, address = self.sock.recvfrom(1024)
            else:
                continue
            if self.isClosed:
                break
            debugLog("received packet from: " + address[0] + ":" + str(address[1]))
            packet = util.EVILPacket()
            packet = packet.parseFromString(msg)
            packet.printSelf()

            if not packet.validateCheckSum():
                debugLog("Invalid Checksum,"+ hex(packet.checksum) + " vs. " + hex(packet.generateCheckSum()) + ", tossing packet")
                continue

            if address in self.connections:
                debugLog("packet belonged to an existing connection")
                self.connectionsLock.acquire()
                self.connections[address].handleIncoming(packet)
                self.connectionsLock.release()
            else:
                debugLog("packet didn't belong to any existing connections")
                if packet.checkFlag(util.FLAG.SYN):
                    debugLog("packet contained syn flag")
                    self.unknownPackets.put((packet, address), False)

    def speaker(self):
        debugLog("speakerThread started on port " + str(self.sock.getsockname()[1]))

        while True:
            if self.isClosed:
                break
            try:
                recipient, packet = self.outgoingPackets.get(timeout=5)
            except Exception as e:
                continue
            if self.isClosed:
                break
            debugLog("pack checksum: " + hex(packet.checksum)+'\n')
            debugLog("Recip: " + str(recipient)+'\n')
            #packet.printSelf()
            self.sock.sendto(packet.toString(), recipient)
            debugLog("sent: " + hex(packet.checksum))


    def bind(self, host, port):
        self.sock.bind((host, port))
        listenerThread = threading.Thread(None, self.listener, "listener_thread")
        listenerThread.start()
        speakerThread = threading.Thread(None, self.speaker, "speaker_thread")
        speakerThread.start()

    def accept(self,block=True,timeout=None):
        """
        called by client code - Socket and connection threads should not touch!
        blocks until a new connection is received and a Connection object has
        been created.

        Return: a Connection instance
        Errors: if socket closed, throw exception
        """
        unknownPacket = self.unknownPackets.get(block,timeout)
        debugLog("got unknown packet for accept call")
        self.connectionsLock.acquire()

        newConn = connection.Connection(self.sock.getsockname()[1], unknownPacket[1][1], self.maxWindowSize,
        connection.STATE.SYN_RECV, unknownPacket[1][0], self)

        self.connections[(unknownPacket[1][0], unknownPacket[1][1])] = newConn
        self.connectionsLock.release()

        newConn.establishConnection()
        return newConn



    def connect(self, host, port):
        """
        Called by client code - socket and connection threads should not touch!
        blocks while attempting to establish a connection with specified server

        Return: a Connection instance (if successful) or an error
        Errors: if socket closed, throw exception
        """
        self.connectionsLock.acquire()

        newConn = connection.Connection(self.sock.getsockname()[1], port, self.maxWindowSize,
        connection.STATE.SYN_SENT, host, self)

        self.connections[(host, port)] = newConn
        self.connectionsLock.release()
        newConn.establishConnection()
        debugLog("new connection created with: " + host + " on port " + str(port))
        return newConn

    def addToOutput(self, address, packet):
        packet.checksum = packet.generateCheckSum()
        #if random.random() < 0.02:
            #debugLog("INTRODUCING ERROR INTO PACKET!!!")
            #packet = copy.deepcopy(packet)
            #packet.data += "~"
            #return
        self.outgoingPackets.put((address, packet))

    def close(self):
        self.isClosed = True
        for c in self.connections:
            try:
                self.connections[c].close()
            except Exception as e:
                pass
            debugLog("connection closed")
        self.sock.close()
        debugLog("socket closed")

    def setMaxWindowSize(self, W):
        self.maxWindowSize = W
        for connection in self.connections:
            self.connections[connection].setMaxWindowSize(W)
