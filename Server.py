#!/usr/bin/python
import socket
from threading import Thread

# {statuscode: phrase}
status = {'200': 'OK', '400': 'Bad Request', '404': 'Not Found', '505': 'P2P-CI Version Not Supported'}
# {hostname: port}
active_peers = {}
# {rfcnumber: rfctitle}
rfc_info = {}
# {rfcnumber: [hostname1, hostname2..]}
rfc_peer_map = {}

version = "P2P-CI/1.0"
server_port = 7734 # predefined well known port
server_name = socket.gethostname()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', server_port))
server_socket.listen(1)

def peers_with_a_rfc(rfcnumber):
    '''Returns a list of peers having a particular RFC'''
    global rfc_info
    if rfcnumber in rfc_info: # if this RFC exists
        message = version + " 200 " + status['200'] + "\r\n\r\n" # for successful request
        peerlist = rfc_peer_map.get(rfcnumber) # get list of peers having the RFC
        tempmsg =''
        rfcdata = "RFC " + rfcnumber + " " + rfc_info.get(rfcnumber) + " "
        for peer in peerlist: # generate the message for each peer
            tempmsg += rfcdata + peer + "\r\n"
        message += tempmsg
    else: # if RFC is not found
        message = version + " 404 " + status['404'] + "\r\n"
    return message


def add_peer_to_rfc(rfcnumber, rfctitle, hostname):
    '''Adding a new RFC if not exists and adding peer to a particular RFC'''
    global rfc_peer_map,rfc_info
    if rfcnumber not in rfc_info: # if RFC is not present in list
        rfc_info[rfcnumber] = rfctitle # store the RFC title
        rfc_peer_map[rfcnumber] = [hostname] # generate the new entry with RFC number as key with hostname as value
    else:
        peer_list=rfc_peer_map.get(rfcnumber) # get list of peers having the RFC
        peer_list.append(hostname) # add new peer to the peer_list
    message = version + " 200 " + status['200'] + "\r\n" + "RFC " + rfcnumber + " " + rfctitle + " " + hostname +  "\r\n" # for successful request
    return message

def register_new_peer(hostname, port):
    '''Add a new peer to list of active peers'''
    global active_peers
    active_peers[hostname] = port # register new hostname with its port



def display_rfc_and_peers(hostname):
    '''Displays the list of all peers and RFC details'''
    global rfc_peer_map, rfc_info
    rfclist = rfc_peer_map.keys() # get list of RFCs
    if rfclist:
        message = version + " 200 " + status['200'] + "\r\n\r\n" # success message
       # print("RFC LIST : ",rfclist)

        for rfc in rfclist: # for each RFC
            peerlist=rfc_peer_map.get(rfc) # get peers having this RFC
            rfcmsg = "RFC: " + str(rfc) + " " + str(rfc_info.get(rfc))
            peermsg=''
            for peer in peerlist:
                peermsg += rfcmsg + " " + peer + "\r\n"
            message += peermsg
    else: # if no RFC found
        message = version + " 404 " + status['404'] + "\r\n"
    return message

def p2p_server(conn, addr):
    '''Validates the client request, performs necessary action and returns the response'''
    request = conn.recv(1024).decode()
    portnumber = request.strip()
    hostname = addr[0]+" "+portnumber
    register_new_peer(hostname, portnumber)

    print('---------New Connection established  ------------------------------------')
    print(hostname)
    print('-----------------------------------------------------------------')

    while True:
        newrequest = conn.recv(1024).decode()
        print('---------Received Request ------------------------------------')
        print(newrequest)
        print('-----------------------------------------------------------------')
        hostversion = newrequest.split('\r\n')[0].split(' ')[-1:]
        hostversion = hostversion[0]

        if version != hostversion: # if version mismatch
            message = "505 " + status['505'] + "\r\n"

        if newrequest == "Exit":
            break

        elif "Host: " in newrequest.split('\r\n')[1] and "Port: " in newrequest.split('\r\n')[2]: # check for correct request format

            if newrequest.split('\r\n')[0].split(' ')[0] == "ADD" and newrequest.split('\r\n')[0].split(' ')[1] == "RFC" and "Title: " in newrequest.split('\r\n')[3]:
                rfcnumber = newrequest.split('\r\n')[0].split(' ')[2]
                rfctitle = newrequest.split('\r\n')[3].split(': ')[1]
                message = add_peer_to_rfc(rfcnumber, rfctitle, hostname)

            elif newrequest.split('\r\n')[0].split(' ')[0] == "LOOKUP" and newrequest.split('\r\n')[0].split(' ')[1] == "RFC" and "Title: " in newrequest.split('\r\n')[3]:
                rfcnumber = newrequest.split('\r\n')[0].split(' ')[2]
                rfctitle = newrequest.split('\r\n')[3].split(': ')[1]
                message = peers_with_a_rfc(rfcnumber)

            elif newrequest.split('\r\n')[0].split(version)[0] == "LIST ALL ":
                message = display_rfc_and_peers(hostname)
            else:
                message = " 400 " + status['400'] + "\r\n" # bad request format
        else:
            message = " 400 " + status['400'] + "\r\n" # bad request format

        print('---------Server response ------------------------------------')
        print(message)
        print('-----------------------------------------------------------------')

        conn.send(str(message).encode()) # tranfer the response to client

    print('--------Removing connection ------------------------------------')
    print(hostname)
    print('-----------------------------------------------------------------')


    to_be_removed = []
    # Remove the client when it closes connection
    for rfc in rfc_peer_map: # for each RFC in available RFC list
        peerlist=rfc_peer_map.get(rfc) # peer list of each RFC
        if hostname in peerlist:# if hostname is present
            peerlist.remove(hostname)
            if len(peerlist) == 0:
                to_be_removed.append(rfc)

    for val in to_be_removed:
        rfc_peer_map.pop(val, None)

        # if hostname in peerlist: # if hostname is present
        #     if len(peerlist) > 1: # if other hosts are there apart from the client which closes connection
        #         peerlist.pop(hostname) # remove the client from list
        #         #global rfc_peer_map
        #         rfc_peer_map[rfc]=peerlist # uodate the dictionary for the RFC
        #     else: # if this is only client hving this RFC
        #         #global rfc_peer_map, rfc_info
        #         rfc_peer_map.pop(rfc, None) # remove the RFC entry from RFC client dictionary
        #         rfc_info.pop(rfc) # remove RFC entry from list of known RFCs



    if hostname in active_peers.keys(): # to remove the client from active peer list
        #global active_peers
        active_peers.pop(hostname, None)

    conn.close() # close the connection after the client's information is deleted


if __name__ == '__main__':
    '''This makes the server to run and handle each request from client asynchronously'''
    print("Server Listening at Port :",server_port,"\r\n")
    while True: # keeps running to handle new clients
        conn, addr = server_socket.accept() # accept the client connection
        Thread(target=p2p_server, args=(conn, addr)).start() # spawn a new thread for each client

    server_socket.close()
