import binascii
import socket
from argparse import ArgumentParser
from server_putah import header
import random
from time import sleep
from server_putah import logNewConnection
from server_putah import logInteraction


def dataSocket(dataPort,server_host):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as new_client_socket:
        newclientPort = random.randint(5000, 8000 - 1)
        new_client_socket.bind((server_host, newclientPort))
        new_client_socket.settimeout(5)
        logNewConnection("Client Transfer Socket Created", server_host, newclientPort)
        while True:
            ping = 'ping'
            message = header(newclientPort,dataPort)
            message.SYN = 0
            message.offset = 10 # 6 for header + 4 for ping
            message.assembleRaw()
            logInteraction(message)
            message.raw += str(binascii.hexlify(ping.encode()).decode("UTF-8"))
            new_client_socket.sendto(message.raw.encode(), (server_host, dataPort))
            data = new_client_socket.recvfrom(1024)
            if data[0].decode()[47:48] == '1':
                ackExitM = header(newclientPort, dataPort)
                ackExitM.ACK = 1
                ackExitM.SYN = 0
                ackExitM.assembleRaw()
                logInteraction(ackExitM)
                print("log added for ack")
                new_client_socket.sendto(ackExitM.raw.encode(), (server_host, dataPort))
                sleep(2)
                new_client_socket.close()
                return
            dataDat = data[0].decode()[49:51] + data[0].decode()[51:53] + data[0].decode()[53:55] + data[0].decode()[55:57]
            dataDat = binascii.unhexlify(dataDat).decode("UTF-8")
            print(dataDat)
            sleep(0.2)

#python3 client_putah.py --server_ip 127.0.0.1 --server_port 8000
def connect(client, server_host,server_port, clientPort):
    message = header(clientPort, server_port)
    message.assembleRaw()
    # print("message syn ", client_socket.getsockname()[1])
    logInteraction(message)
    client.sendto(message.raw.encode(), (server_host, server_port))
    # print(message, clientPort,server_port)
    response = client.recvfrom(1024)
    tempResponseHeader = header(0, 0)
    tempResponseHeader.rawToHeader((response[0].decode()))
    print(tempResponseHeader.raw, int(tempResponseHeader.sourcePort, 2), int(tempResponseHeader.destPort, 2))
    if tempResponseHeader.SYN == '1' and tempResponseHeader.ACK == '1':
        print("accepted send ack")
        finalAck = header(clientPort, server_port)
        finalAck.ACK = 1
        finalAck.SYN = 0
        finalAck.assembleRaw()
        print(finalAck.raw, finalAck.sourcePort, finalAck.destPort)
        logInteraction(finalAck)
        client.sendto(finalAck.raw.encode(), (server_host, finalAck.destPort))
        return int(tempResponseHeader.sourcePort,2)
def start_udp_client(server_host, server_port):
    # create a client socket with the following specifications1
    #   AF_INET -> IPv4 socket
    #   SOCK_DGRAM -> UDP protocol
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        # send message to server at address (server_host, server_port)
        clientPort = random.randint(5000,server_port - 1)# could just let windows default assign but for windows testing setup random
        print("new socket", server_host,clientPort)
        client_socket.bind((server_host, clientPort))
        logNewConnection("\nClient Connect Socket Created", server_host, clientPort)
        dataPort = connect(client_socket, server_host, server_port, clientPort)
        client_socket.close()
    sleep(2)
    dataSocket(dataPort,server_host)

       # new_client_socket.close()
        # print(tempResponseHeader.raw, response[1][0],response[1][1], int(tempResponseHeader.sourcePort,2), int(tempResponseHeader.destPort,2))
        #
        # message, addr = client_socket.recvfrom(1024)
        # print(f"Message from {addr}: {message.decode()}")
        #
        # if (message.decode() == "SYNACK"):
        #     print("SYNACK recieved")
        #     message = "ACK"
        #     client_socket.sendto(message.encode(), (addr[0], addr[1]))
        # else:
        #     print("SYN not recieved return to welcomeSocketThread")
        #     return
       # for message_id in range(1, 11):
            #message = f"127.0.0.1 8001 #{message_id}".encode()
           # client_socket.sendto(message, (server_host, server_port))
def parse_args():
    # parse the command line arguments
    args = ArgumentParser()
    args.add_argument('--server_ip', default="127.0.0.1")
    args.add_argument('--server_port', default=8000, type=int)
    return args.parse_args()
if __name__ == '__main__':
    args = parse_args()
    print(args.server_ip, args.server_port)
    start_udp_client(args.server_ip, args.server_port)
