# PeertoPeer_IP_Project

This is a PEER to PEER socket application with a Centralised Indexing System

## Environment for execution:

**use python 3**

**We tested the program on : python 'v3.6.3'**

In order to use this application please follow the following steps

First Start the Server in any system of choice

Command for starting the server:
**python Server.py**

This command will have the server running in the localsystem on port 7734

Command for starting the client:
**python Client.py <client_port_number> <server_host_ip>**
Give server ip as : localhost if running server and client on the same machine
Else give the appropriate server ip

On Starting, the client will be prompted to enter 4 options
1) Add
2) Lookup
3) Lookall
4) Get

give the appropriate option number

After giving the option number, enter the option details in the prompt format that appears

1) ADD
All the RFC files for transfer are available in the folder RFCFiles

for adding it, select option 1 and enter the option detail in the following format


ADD <RFC_NUM> <RFC_TITLE>

Example :

**ADD 1000 document1**

This adds rfc1000.txt's index to the server


2) LOOKUP
All the RFC files for transfer are available in the folder RFCFiles

for looking up all the peers that is carrying a particular RFC


LOOKUP <RFC_NUM> <RFC_TITLE>

Example :

**LOOKUP 1000 document1**

This looks up the peers containing rfc1000.txt's


3)LOOKALL

There is no prompt for this one

4)

the prompt message shows up as

GET <RFC_NUM> <RFC_TITLE>

Example :

**GET 1000 document1**

This gets the rfcs residing in the other system


