
import sys
import socket
import binascii

ip = '8.8.8.8'
port = 53

#Read the hostname provided by a user, Extract the host name.
def readHostNameFromUser():
    if len(sys.argv) < 3:
        name = sys.argv[1]                       
        hostname = str(name).lower()                   
    else:
        print("\nSingle Hostname Expected, Try Again\n")
        exit()
    return hostname

#prepare a DNS query message.
def DnsQuery(hostname):

    #Header Section includes ID(16 bit id), QR (0 for query),OPCODE(0),RD(1),QDCOUNT(1)
    ID = 'AAAA'
    QSECTION = '0100'
    QDCOUNT = '0001'

    Header = ID + QSECTION + QDCOUNT + '0000' + '0000' + '0000'

    #Question Section contains QNAME in hex, QTYPE(1) and QCLASS(1)

    #we need to work on this to convert the hostname like 'yahoo.com' to 	"057961686f6f03636f6d00" format
    #we need to split yahoo.com as yahoo and com
    #find yahoo -> ascii value as 7961686f6f and find the lenght which is 5 and append the ascii value to the lenght to get 057961686f6f
    #find com -> ascii value as 636f6d and find the lenght which is 3 and append the ascii value to the lenght to get 03636f6d
    #finally append ascii values of yahoo and com and add 0 at the end to get "057961686f6f03636f6d00" format

    #QNAME = binascii.hexify(hostname) 
    #print("QNAME = ",QNAME)

    #for QNAME
    splitHostNames = hostname.split('.')
    resultString = ''
    for splitHostName in splitHostNames:
        lenHostName = len(splitHostName)
        hexObj = hex(lenHostName)
        lenNumHexObj = '0' + hexObj[2:]
        #till this statement we get "05" as hex obj for yahoo
        #Now we need to convert yahoo to its ascii values and append after the lenNumHexObj
        #''.join(str(ord(c)) for c in splitHostName) 
        #format(ord("c"), splitHostName)
        #ord(character) gets us the ascii integer value of the character
        #hex(ord(character)) gets the hexadecimal value of the ascii integer in the form like h -> 104 -> 0x68
        listHex = ''
        for character in splitHostName:
            y = hex(ord(character))
            y = format(ord(character), "x")
            listHex = listHex + y
            
        resultString = resultString + lenNumHexObj + listHex
        
    resultString = resultString + '00'
    
    QNAME = resultString
    QTYPE = '0001'
    QCLASS = '0001'
    Question = QNAME + QTYPE + QCLASS

    queryMessage = Header + Question


    print('\nPreparing DNS query..')
    print('\nDNS query header = ',Header)
    print('\nDNS query question section = ',Question)
    print('\nComplete DNS query = ',queryMessage)
    print('\n')

    return queryMessage


def sendQuery(DnsQueryMessage,ip):
    
    client_socket  = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    print("Contacting DNS server..")
    print("Sending DNS query..")
    
    attempts = 1
    
    while(1):
        if(attempts > 3):
            print("Error: Timeout")
            break
            
        else:
            print("DNS response received (attempt " + str(attempts) + " of 3)")
            print("Entering Connection Sending DNS Message")
            client_socket.settimeout(5.0)
            client_socket.sendto(binascii.unhexlify(DnsQueryMessage),(ip,port))
            data,addr = client_socket.recvfrom(4096)
            attempts +=1
            
    client_socket.close()
           
    return binascii.hexlify(data).decode("utf-8")



def string_to_int(txt):
  number = 0
  for c in txt:
    number = (number << 8) + ord(c)
  return number



#arg r      response    
def readResponse(r) :
    response_length = len(r)
    domain_size = r[11] * 256 + r[12]
    parsed_r = {
        "id" :      r[0:4],
        "qr" :      int(r[4:5]) >> 3,    
        "opcode" :  (int(r[4:5]) << 4 + int(r[5:6])) & 0x78 >> 3,   #0b1000 0001 & 0b0111 1000
        "aa" :      (int(r[5:6]) & 4) >> 2,
        "tc" :      (int(r[5:6]) & 2) >> 1,
        "rd" :      int(r[5:6]) & 1,
        "ra" :      int(r[6:7]) >> 3,
        "z" :       int(r[6:7]) & 7,
        "rcode" :   int(r[7:8]) & 0xF,
        "qdcount" : (r[8:12]),
        "ancount" : (r[12:16]),
        "nscount" : (r[16:20]),
        "arcount" : (r[20:24]),
        #question
        "qname" : r[24: 24 + r[24:len(r)+1].find('00') + 2],
        "qtype" : r[24 + r[24:len(r)+1].find('00') + 2 : 24 + r[24:len(r)+1].find('00') + 6],
        "qclass" : r[24 + r[24:len(r)+1].find('00') + 6 : 24 + r[24:len(r)+1].find('00') + 10],
        "name" : r[24 + r[24:len(r)+1].find('00') + 2][0:4]
    }
    print("header.id = ", parsed_r.get("id"))
    print("header.qr = ", parsed_r.get("qr"))
    print("header.opcode = ", parsed_r.get("opcode"))
    print("header.aa = ", parsed_r.get("aa"))
    print("header.tc = ", parsed_r.get("tc"))
    print("header.rd = ", parsed_r.get("rd"))
    print("header.ra = ", parsed_r.get("ra"))
    print("header.z = ", parsed_r.get("z"))
    print("header.rcode = ", parsed_r.get("rcode"))
    print("header.qdcount = ", parsed_r.get("qdcount"))
    print("header.ancount = ", parsed_r.get("ancount"))
    print("header.nscount = ", parsed_r.get("nscount"))
    print("header.arcount = ", parsed_r.get("arcount"))
    print("header.qname = ", parsed_r.get("qname"))
    print("header.qtype = ", parsed_r.get("qtype"))
    print("header.qclass = ", parsed_r.get("qclass"))
    print("answer.name = ", parsed_r.get("name"))
    return

hostname = readHostNameFromUser()
DnsQueryMessage = DnsQuery(hostname)
readResponse(sendQuery(DnsQueryMessage,ip))
