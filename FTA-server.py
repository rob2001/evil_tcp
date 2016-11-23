import sys
import getopt
import EVIL
import threading
from util import debugLog

global _debug

class FTAserver:

    def __init__(self, argv):
        self.ourPort = 404
        self.maxMessageSize = 1024

        try:
            opts, args = getopt.getop(argv, "x:d")
        except getopt.GetopError:
            usage()
            sys.exit(2)

        for opt, arg in opts:
                if opt == '-x':
                    self.ourPort = arg
                elif opt == '-d':
                    _debug = True
                    debugLog("Maximum Verbosity!")

        self.sock = EVIL()
        self.sock.bind(('', self.ourPort))
        debugLog("socket bound to: " + str(self.ourPort))

        operateThread = threading.Thread(None, operate, operateThread)


    def operate(self):
        while True:
            newSessionConnection = self.sock.accept()
            debugLog("accepted connection from " + newSession.otherAddress[0] + ":" + str(newSession.otherAddress[1]))
            sessionThread = threading.Thread(None, handleSession, newSessionConnection)
            sessionThread.start()

    def handleSession(self, conn):
        debugLog("new session started with " + conn.otherAddress[0] + ":" + str(conn.otherAddress[1]))
        while True:
            string = conn.get(maxMessageSize)
            debugLog("received " + string + " from " + conn.otherAddress[0] + ":" + str(conn.otherAddress[1]))
            reply = string.upper()
            debugLog("replying to " + conn.otherAddress[0] + ":" + str(conn.otherAddress[1]) + " with: " + reply)
            conn.send(reply)

    def window(self, W):
        self.sock.setMaxWindowSize(W)

    def terminate(self):
        self.sock.close()
        sys.exit()

def main(argv):
    return FTAserver(argv)

def test(argv):
    app = main(argv)

test(sys.argv)
##main(sys.argv)