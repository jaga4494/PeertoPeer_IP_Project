import socket
import platform
import os
import sys
import email.utils
import time
from pathlib import Path
from threading import Thread


P2P_VERSION = "P2P-CI/1.0"
RFC_FILES_FOLDER = os.getcwd() + "/RFCFiles/rfc"
RFC_DOWNLOADS_FOLDER = os.getcwd() + "/Downloads/rfc"
SERVER_PORT_NUM = 7734 # the server_port and the address are according to the requirements
SERVER_HOST_NAME = 'localhost' # change the below to other IP if the server is running in any other system. Here we will be running both the client and the server in the same system.


client_port_number = int(sys.argv[1])
#client_port_number = 60000

def upload_rfc_from_peer():
    '''This is the upstream that handles any peer request for an RFC. This is constantly running in a seperate thread from main thread.
        This is the response to the get request
        P2P-CI/1.0 200 OK
        Date: Wed, 12 Feb 2009 15:12:05 GMT
        OS: Mac OS 10.2.1
        Last-Modified: Thu, 21 Jan 2001 9:23:46 GMT
        Content-Length: 12345
        Content-Type: text/text
        (data data data ...)
    '''

    upload_server_socket = socket.socket()
    upload_server_socket.bind(('localhost',client_port_number))
    upload_server_socket.listen(10)
    while True:
        incoming_socket,incoming_addr = upload_server_socket.accept()
        data = str(incoming_socket.recv(1024).decode()).strip()
        print("rcvd data ",data)
        request = data.split("\r\n")
        if len(request) == 3 and request[0].startswith('GET RFC') and request[1].startswith('Host:') and request[2].startswith('OS:'):
            if P2P_VERSION not in request[0]:
                incoming_socket.sendall(str("505 P2P-CI Version Not Supported\r\n").encode())
            else:
                rfc_requested = request[0].split(" ")[2]
                rfc_file_location = RFC_FILES_FOLDER+rfc_requested+".txt"
                payload = open(rfc_file_location,'r').read()
                response = str(P2P_VERSION + " 200 OK\r\n" +\
                            "Date: " + str(email.utils.formatdate(usegmt=True)) +"\r\n" +\
                            "OS: " + platform.platform() +"\r\n" +\
                            "Last-Modified: " + str(time.ctime(os.path.getmtime(rfc_file_location))) +"\r\n" +\
                            "Content-Length: " + str(len(payload)) +"\r\n" +\
                            "Content-Type: text/text\r\n" )
                print('---------Upload RFC response ------------------------------------')
                print(response)
                print('-----------------------------------------------------------------')
                response += payload
                incoming_socket.sendall(response.encode())
        else:
            incoming_socket.sendall(str("400 Bad Request\r\n").encode())


def send_get_request_to_peer(peer_host_name, peer_port_num, rfc_num, rfc_title, get_request):
    '''This method is used for making requests to any peer after getting the information from the server regarding the peer'''

    print(" --- Client Request ----------------------------------------------------------")
    print(get_request)
    print(" -----------------------------------------------------------------------------")

    download_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    download_socket.connect((peer_host_name,int(peer_port_num)))
    download_socket.sendall(str(get_request).encode())
    data = download_socket.recv(1024).decode()
    response = data.split("\r\n")
    print(" --- Peer Response ----------------------------------------------------------")
    print("\r\n".join(response[0:5]))
    print("data ... data ... data ...")
    print(" -----------------------------------------------------------------------------")



    if P2P_VERSION+ ' 200 OK' in response[0]:
        content_length = response[4]
        content_length = int(content_length[16:])
        if content_length > 1024:
            data += download_socket.recv(content_length+1024).decode() # gets the whole package
        data = data[data.find('text/text\r\n')+11:]
        rfc_file_location = RFC_DOWNLOADS_FOLDER + rfc_num + ".txt"
        with open(rfc_file_location,'w') as file:
            file.write(data)
            print('-----------------------------------------------------------------------')
            print('File ',rfc_num+'.txt is downloaded' )
            print('-----------------------------------------------------------------------')
    else:
        print(response[0])
    download_socket.close()

def user_choices(choice,P2Ssocket):
    '''This method is a hook method for the make requests . This is used for getting additional information that are required for the requests'''
    print('--------------------------------------------------------------------------------')
    print("Type Back to get the option menu and Exit to close")

    try:
        choice = int(choice)
    except ValueError:
        print("Please Enter a valid number")
        return True

    # Choices 1,2,3 are made from the Client to the server
    if choice == 1:
        print("This choice is used for registering the RFC of the client in the server")
        user_input = input("enter the input in the following format\r\n'ADD <RFC_NUM> <RFC_TITLE>' \r\n" )
    elif choice == 2:
        print("This choice is used for getting all the peers that serves the Given RFC  ")
        user_input = input("enter the input in the following format\r\n'LOOKUP <RFC_NUM> <RFC_TITLE>'  \r\n")
    elif choice == 3:
        user_input = "LOOK ALL"
    # Choice 4
    elif choice == 4:
        print("This choice is used for getting an RFC from a Peer after connecting ")
        user_input = input("enter the input in the following format\r\n'GET <RFC_NUM> <RFC_TITLE>'   \r\n")
    # Default case
    else:
        user_input = 'Exit'

    if user_input == 'Back':
        return True

    return make_requests(P2Ssocket, user_input, choice)


def make_requests(P2Ssocket, input, choice):
    '''This method executes the request according to the user input and returns a boolean(True) for continuation and false for exiting'''
    if choice > 4:
        if(input == 'Exit'):
            P2Ssocket.sendall(str(input).encode())
            print("Terminating Connection")
            return False

    # for adding a New RFC to server
    if choice == 1:
        input_values = input.split(' ')
        if len(input_values) != 3 and not input.startswith('ADD'):
            print("Please enter the format as ADD <RFC_NUM> <RFC_TITLE> next time")
            return True
        rfc_num = str(input_values[1])
        rfc_title = str(input_values[2])
        rfc_file_location = Path(RFC_FILES_FOLDER+rfc_num+".txt")
        try:
            rfc_file_location.resolve()
        except FileNotFoundError:
            print("given rfc dosen't exist to be added to the server")
            return True
        else:
            # file exists and we begin the add process
            request = add_rfc_method(rfc_num,rfc_title)
            print(" --- Client Request ----------------------------------------------------------")
            print(request)
            print(" -----------------------------------------------------------------------------")
            P2Ssocket.sendall(str(request).encode())
            response = P2Ssocket.recv(1024).decode()
            print(" --- Server Responded with ---------------------------------------------------")
            print(response)
            print(" -----------------------------------------------------------------------------")
            return True


    #for listing all RFCs from server
    elif choice == 3:
        request = list_all_method()
        print(" --- Client Request ----------------------------------------------------------")
        print(request)
        print(" -----------------------------------------------------------------------------")
        P2Ssocket.sendall(str(request).encode())
        response = P2Ssocket.recv(1024).decode()
        print(" --- Server Responded with ---------------------------------------------------")
        print(response)
        print(" -----------------------------------------------------------------------------")
        return True

    #for looking up an RFC from server
    elif choice == 2 or choice == 4:
        input_values = input.split(' ')
        if len(input_values) != 3:
            print("Please enter the format as LOOKUP <RFC_NUM> <RFC_TITLE> next time")
            return True
        rfc_num = input_values[1]
        rfc_title = input_values[2]

        request = lookup_rfc_method(rfc_num, rfc_title)
        print(" --- Client Request ----------------------------------------------------------")
        print(request)
        print(" -----------------------------------------------------------------------------")
        P2Ssocket.sendall(str(request).encode())
        response = P2Ssocket.recv(1024).decode()
        print(" --- Server Responded with ---------------------------------------------------")
        print(response)
        print(" -----------------------------------------------------------------------------")
        if choice == 2:
            return True
        else:
            # This is for getting the file from the peer (choice 4)
            response_lines = response.split("\r\n")
            if '404' in response_lines[0] or "Not Supported" in response_lines[0] or "Bad" in response_lines[0]:
                print("Unable to perform GET request")
                return True
            response_peer_information  = response_lines[2].split(" ") # this is the start of the peer information and can span multiple lines depending on the number of peers having that RFC

            peer_host_name = response_peer_information[3]
            peer_port_num = response_peer_information[4]
            get_request = get_rfc_method(rfc_num)
            Thread(target= send_get_request_to_peer,args=(peer_host_name,peer_port_num,rfc_num,rfc_title,get_request)).start()
            return True
    else:
        return False



# below are the functions that represent the functions for getting the request format for a particular type of method
# between Peers P2P
def get_rfc_method(rfc_number):
    ''' This Method is used for returning the format of the RFC request from one peer. Example of the request is as follows
        GET RFC 1234 P2P-CI/1.0
        Host: somehost.csc.ncsu.edu
        OS: Mac OS 10.4.1 '''
    return "GET RFC " + str(rfc_number) +" " + str(P2P_VERSION) + "\r\n" + \
            "Host: " + str(socket.gethostname()) +"\r\n" +\
            "OS: " + str(platform.platform()) +"\r\n"


# Between a client and a server P2S
def add_rfc_method(rfc_number,rfc_title):
    '''This Method is used for adding an rfc to the index of the server. The request format is as follows
        ADD RFC 123 P2P-CI/1.0
        Host: thishost.csc.ncsu.edu
        Port: 5678
        Title: A Proferred Official ICP
        ADD RFC 2345 P2P-CI/1.0 '''
    return "ADD RFC " + str(rfc_number) +" " + P2P_VERSION + "\r\n" + \
            "Host: " + str(socket.gethostname()) +"\r\n" + \
            "Port: " + str(client_port_number) +"\r\n" +\
            "Title: " + str(rfc_title) +"\r\n"

def lookup_rfc_method(rfc_number,rfc_title):
    ''' This method is used to get the index of all the peers for a given RFC from the server
        LOOKUP RFC 3457 P2P-CI/1.0
        Host: thishost.csc.ncsu.edu
        Port: 5678
        Title: Requirements for IPsec Remote Access Scenarios '''
    return "LOOKUP RFC " + str(rfc_number) +" " + str(P2P_VERSION) + "\r\n" + \
            "Host: " + str(socket.gethostname()) +"\r\n" + \
            "Port: " + str(client_port_number) +"\r\n" + \
            "Title: " + str(rfc_title) +"\r\n"

def list_all_method():
    '''This method is used to get all the peers information from the server
        LIST ALL P2P-CI/1.0
        Host: thishost.csc.ncsu.edu
        Port: 5678 '''
    return "LIST ALL " +str(P2P_VERSION) + "\r\n" + \
            "Host: " + str(socket.gethostname()) +"\r\n" + \
            "Port: " + str(client_port_number) +"\r\n"



def user_interface(P2Ssocket):
    '''This is the main function that is used by the client for making any file requests. This is where the user inputs his option as client and peer/server responds'''
    print('--------------------------------------------------------------------')
    option_list = "Please select one of the various options \r\n"+\
                    "The below options 1,2,3 is for requesting the SERVER for information regarding the peers/rfcs\r\n"+\
                    "1.ADD\r\n"+\
                    "2.LOOKUP\r\n"+\
                    "3.LOOKALL\r\n"+\
                    "The below option is used for requesting the PEER\r\n"+\
                    "4.GET\r\n"+\
                    ">= 5 .Exit  \r\n"

    while True:
        choice = input(option_list)
        if not user_choices(choice,P2Ssocket):
            print("Terminatated. However this peer will continue to server incoming RFC requests")
            break




if __name__ == '__main__':
    '''This is the starter main method that connects to the server and passes the server socket to the required methods'''
    P2Ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    P2Ssocket.connect(('', SERVER_PORT_NUM))
    P2Ssocket.sendall(str(client_port_number).encode()) # letting the server know the portnumber the client is going to use
    t=Thread(target=upload_rfc_from_peer)
    t.start()

    user_interface(P2Ssocket)