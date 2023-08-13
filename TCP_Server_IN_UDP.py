import socket
import struct
import signal
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
import threading
from time import sleep
import datetime
import binascii
import random

#https://superfastpython.com/threadpoolexecutor-get-results/#:~:text=The%20map()%20function%20in%20ThreadPoolExecutor,submitted%20to%20the%20thread%20pool.

#python3 server_putah.py --ip 127.0.0.1 --port 8000

#//welcome thread for establishing new connections with users

"""TODO:    cleanup files from early attempt(s)
            add real FIN/ACK for exit and ctr c
            add headers to ping pong sends (probably???)
            more comments : )"""
#replace named tuple from project 2


class header:
    def __init__(self, sourcePort, destPort):
        self.sourcePort = sourcePort #2 byte
        self.destPort = destPort # 2 bytes
        self.offset = 6 #4 bit field, set to 14 for 14 byte header
        self.RSV = 0 #6 bits
        self.URG = 0 #1 bit
        self.ACK = 0 #1 bit
        self.PSH = 0 #1 bit
        self.RST = 0 #1 bit
        self.SYN = 1 #1 bit
        self.FIN = 0 #1 bit
        self.allFlags = None #helper is not included in sent (not a new field)
        self.raw = None #helper that has and is returned as final bit string to be sentTo() (not a new field)
    def setCtrlFlag(self): #update ctrl to of handshake
        self.offset = (self.offset << 13)
        self.RSV = (self.RSV << 6)
        self.URG = (self.URG << 5)
        self.ACK = (self.ACK << 4)
        self.PSH = (self.PSH << 3)
        self.RST = (self.RST << 2)
        self.SYN = (self.SYN << 1)
        self.FIN = self.FIN
        self.allFlags = self.offset + self.RSV + self.URG + self.ACK + self.PSH + self.RST + self.SYN + self.FIN
    def assembleRaw(self):
        self.setCtrlFlag()
       # self.raw = struct.pack('!HHH', self.sourcePort,self.destPort,self.allFlags) #!222 = 6 bytes
        self.raw = format(self.sourcePort,'b').zfill(16)
        self.raw += format(self.destPort,'b').zfill(16)
        self.raw += format(self.allFlags,'b').zfill(16) #couldn't make pack actually fill the bits correctly so cheating by using string it is what it is
        # print(self.raw)
        #print(self.sourcePort, self.destPort, self.allFlags)
        #print(bin(self.sourcePort), bin(self.destPort), bin(self.allFlags))
        return self.raw
    def rawToHeader(self, message):
        self.sourcePort = message[0:16]  # 2 byte
        self.destPort = message[16:32]  # 2 bytes
        self.offset = message[32:36]
        self.RSV = message[36:42]
        self.URG = message[42:43]
        self.ACK = message[43:44]
        self.PSH = message[44:45]
        self.RST = message[45:46]
        self.SYN = message[46:47]
        self.FIN = message[47:48]
        self.allFlags = self.offset + self.RSV + self.URG + self.ACK + self.PSH + self.RST + self.SYN + self.FIN
        self.raw = self.sourcePort + self.destPort + self.allFlags

def logInteraction(header):
    with open('putah_interactions_log.txt', 'a') as openFD:  # create/reset log files
        openFD.write(str(header.sourcePort) + '\t|\t' + str(header.destPort) + '\t|\t')
        if ((header.ACK >> 4) == 1 and (header.SYN >> 1) != 1) or ((header.URG >> 5) == 1 and (header.ACK >> 4) == 1):
            openFD.write('ACK \t\t|\t\t')
        elif (header.ACK >> 4)== 1 and (header.SYN >> 1) == 1:
            openFD.write('SYN/ACK \t|\t\t')
        elif( header.ACK >> 4) != 1 and (header.SYN >> 1) == 1:
            openFD.write('SYN \t\t|\t\t')
        elif header.FIN == 1:
            openFD.write('FIN \t\t|\t\t')
        else:
            openFD.write('DATA\t\t|\t\t')
        openFD.write(str(header.offset >> 13) +'\t\t|\t' + str(datetime.datetime.now()) + '\n')
def logNewConnection(desc, ip, port):#order when called with transfer sockets differs based on thread sleeps/scheduling map
    with open('putah_connection_log.txt', 'a') as openFD:  # create log file
        openFD.write(desc + "\tIP: " + str(ip) + "\tPORT: " + str(port) + "\n")

def accept(server):
    message = server.recvfrom(1024) #recieved a SYN message
    print(message[0].decode()," read in msg")
    tempMessageHeader = header(0,0) #initialize
    tempMessageHeader.rawToHeader(message[0].decode())
    print(tempMessageHeader.raw)
    print("ack:", tempMessageHeader.ACK)
    print("syn:", tempMessageHeader.SYN)
    if tempMessageHeader.SYN == '1' and tempMessageHeader.ACK != '1': #is just SYN
        newPort = random.randint(5000, 8000 - 1)
        print("new port addr @~ ",newPort, message[1][1])
        responseSYNACK = header(newPort,message[1][1]) #use src as the client already knows servers src
        responseSYNACK.ACK = 1
        responseSYNACK.assembleRaw()
        print(responseSYNACK.raw)
        logInteraction(responseSYNACK)
        server.sendto(responseSYNACK.raw.encode(), (server.getsockname()[0],message[1][1])) #send SYN/ACK
        ackIn = server.recvfrom(1024)
        finalAckAccepted = header(0, 0)  # initialize
        finalAckAccepted.rawToHeader(ackIn[0].decode())
        print(finalAckAccepted.raw, "end")
        if finalAckAccepted.ACK == '1':
            server.close()
            return True, newPort
        else:
            print("error in final ACK")
    else:
        print("error with SYN")

def welcomeSocketThread(ip, port, exiting):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as welcomeSock:
        welcomeSock.bind((ip, port))
        while True:
            print("welcomesocket listening:")
            handshake, port1 = accept(welcomeSock)
            clientList.append((True, port1))
            print("num clients",len(clientList))
            print("ports:",clientList)
            if(exiting.is_set()):
                start_putah_server(ip,port)
            return

def clientHandlerThread(ip, newPort, id,exiting):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as transferSock:
        transferSock.bind((ip,newPort))
        transferSock.settimeout(5)
        print("new client connecting", id, ip, newPort)
        logNewConnection("Server Transfer Socket Created", ip, newPort)
        messageId = 1
        while not exiting.is_set():
            data = transferSock.recvfrom(1024)
            if exiting.is_set():
                exitH = header(newPort, data[1][1])
                exitH.SYN = 0
                exitH.FIN = 1
                exitH.assembleRaw()
                logInteraction(exitH)
                transferSock.sendto(exitH.raw.encode(), (ip, data[1][1]))
                ackExit = transferSock.recvfrom(1024)
                if ackExit[0].decode()[42:43] == 1:
                    sleep(2)
                    transferSock.close()
                    return
            dataDat = data[0].decode()[49:51] + data[0].decode()[51:53] + data[0].decode()[53:55] + data[0].decode()[55:57]
            dataDat = binascii.unhexlify(dataDat).decode("UTF-8")
            print(dataDat)
            if dataDat:
                if messageId == 1:
                    sleep(1)
                    pass
                pong = "pong"
                recmessage = header(newPort, data[1][1])
                recmessage.SYN = 0
                recmessage.offset = 10  # 6 for header + 4 for ping
                recmessage.assembleRaw()
                logInteraction(recmessage)
                recmessage.raw += str(binascii.hexlify(pong.encode()).decode("UTF-8"))
                transferSock.sendto(recmessage.raw.encode(),(ip,data[1][1]))
                messageId += 1
            else:
                print("not")
                transferSock.close()
                break

def start_putah_server(ip, port):
    logNewConnection("Welcome Socket Created", ip, port) #here instead of in welcome socket thread because my implementation results in multiple welcome sockets
    clientId = 0
    exiting = threading.Event()
    def signal_handler(signum, frame):
        start_putah_server(ip,port)

    signal.signal(signal.SIGTERM, signal_handler)
    with ThreadPoolExecutor(max_workers=10) as executor: # welcome thread and
        try:
            while True:
                print("inside while")
                future = executor.submit(welcomeSocketThread, ip, port, exiting) #main thread handles welcome socket
                result = future.result()
                print("future result:",result)
                if clientList[clientId]: #if connection was ACK
                    executor.submit(clientHandlerThread,ip, clientList[clientId][1],clientId, exiting)
                    clientId += 1
        except KeyboardInterrupt:
            print('Caught keyboardinterrupt')
            exiting.set()
            return
def parse_args():
    # parse the command line arguments
    args = ArgumentParser()
    args.add_argument('--ip', default="127.0.0.1")
    args.add_argument('--port', default=8000, type=int)
    return args.parse_args()

if __name__ == '__main__':
    global numClients
    global clientList
    with open('../putah_connection_log.txt', 'w') as openFD: #create/reset log files
        openFD.write('')
    with open('../putah_interactions_log.txt', 'w') as openFD:  # create/reset log files
        openFD.write('Source | Destination | Message Type | Message Length | TimeStamp\n')
    numClients = 0
    clientList = []
    args = parse_args()
    print(args.ip, args.port, "SERVER STARTED")
    start_putah_server(args.ip,args.port)
    print("-----------finished---------")
