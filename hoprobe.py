'''
Created on Dec 3, 2012

@author: woo
'''

import socket
import os
import time
import struct

my_IP_address = '129.22.150.243' # Put your own IP address here.
'''
This function is to make a ip_header myself, since we are using ocket.IP_HDRINCL, 1 option.
'''
def packIPheader (dest, ttl):
    # ip header fields
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    ip_tot_len = 0    
    ip_id = 54321    #Id of this packet
    ip_frag_off = 0
    ip_ttl = ttl
    ip_proto = socket.IPPROTO_UDP   
    ip_check = 0    # kernel will fill the correct checksum
    ip_saddr = socket.inet_aton (my_IP_address)    #enter your IP address here
    ip_daddr = socket.inet_aton ( dest )     
    ip_ihl_ver = (ip_ver << 4) + ip_ihl       # the ! in the pack format string means network order
    ip_header = struct.pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
    return ip_header
'''
Making udp header
'''
def packUDPheader (src_port, length):
    udp_src_port = src_port 
    udp_dest_port = 33434
    udp_length = length
    udp_checksum = 0;
    udp_header = struct.pack('!HHHH', udp_src_port, udp_dest_port,udp_length,udp_checksum)
    return udp_header
     
def main(dest_name):
    dest_addr = socket.gethostbyname(dest_name)
    port = 33434
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 16 
    ttl_max = 80
    ttl_roof = 80 #If ttl grows more than this value, probing will be given up
    ttl_min = 0
    RTT_last_round = 0
    
    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        #send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        #send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        send_socket = socket.socket (socket.AF_INET, socket.SOCK_RAW, udp)
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        recv_socket.bind(("", port))
        recv_socket.settimeout(3.0);
        probe_packet_IP = packIPheader (dest_addr, ttl)
        probe_packet_data = 'project 2' 
        '''
        I put os.getpid()+ttl to udp's source port, which is the sum of process id and ttl used in 
        this round, in order to identify if the incoming ICMP packet is responsing my probe packet.
        NOTE: involing ttl can make sure that I will not misuse the ICMP packets that are responding to
        the delayed probe packets that I send in the previous rounds.  
        '''
        probe_packet_UDP = packUDPheader (os.getpid()+ttl, 8 + len(probe_packet_data))            
        probe_packet = probe_packet_IP + probe_packet_UDP + probe_packet_data
        sending_time = time.time()  
        send_socket.sendto(probe_packet, (dest_addr, port)) 
        response_addr = None
        curr_name = None
        '''
        Break the loop if we stuck in a infinite loop or ttl reaches the boundry.
        
        '''
        if ttl > ttl_roof or ttl_max == ttl_min or ((ttl_max-ttl_min ==1) and (ttl==ttl_max or ttl== ttl_min)):
            print "Probing for", dest_name,dest_addr,'failed :('
            break
        try:
            response_packet, response_addr = recv_socket.recvfrom(512)    #Get ICMP response from socket.
            rcv_time = time.time() 
            response_addr = response_addr[0] 
            RTT = rcv_time - sending_time # Get RTT
            icmp_header_type = response_packet[20:21]
            icmp_type = struct.unpack('B' , icmp_header_type)
            ip_ttl_left = struct.unpack('B',response_packet[36])[0]
            udp_sport = struct.unpack('>H', response_packet[48]+response_packet[49])
            source_ip = socket.inet_ntoa(response_packet[40:44])
            '''
            Structure of packet received from socket
            |20 Bytes |8 Bytes    |20 Bytes          |8 Bytes            |    |
            ------------------------------------------------------------------
            |IP header|ICMP header|Original IP header|Original UDP header|Data|    
            '''            
            print ttl,'. Probing',dest_name,dest_addr,'icmp type:' , icmp_type[0], '. ttl_left',ip_ttl_left, 'RTT:',RTT*1000,'ms'
            
            try:
                curr_name = socket.gethostbyaddr(response_addr)[0]
            except socket.error:
                curr_name = response_addr
        except socket.error:
            pass
        finally:
            send_socket.close()
            recv_socket.close()
            
        '''  
         If TTL is 1 hop near its max or min value and no reply recieved in thir round
         I will end the loop, because it is going to be a infinite loop.
        '''
        if response_addr is None and (ttl==ttl_min+1 or ttl == ttl_max-1) and ip_ttl_left !=1 :
            print ttl, '*'
            print dest_name,'Unreachable. TTL left:',ip_ttl_left, 'ttl_max =', ttl_max, 'ttl_min = ', ttl_min 
            break;
        '''
        When we have reply from the server, analyse it and determine if it is our target server with a exact probe.
        If not, modify the TTL for next round.
        '''
        if response_addr is not None:
            curr_host = "%s (%s)" % (curr_name, response_addr)  
            if source_ip== my_IP_address and udp_sport[0]==os.getpid()+ttl:# Identify if this ICMP packet is replying my probe
                '''
                If icmp type is 11, means that our TTL is too small, and I will double the TTL if the doubled value is 
                smaller than the max TTL. 
                Otherwise I will set the TTL as (ttl_max-ttl)/2 + ttl
                '''
                if icmp_type[0]==11:
                    if ttl > ttl_min:
                        ttl_min=ttl
                    if ttl_max > ttl*2:    
                        ttl = ttl*2
                    else:
                        ttl = (ttl_max-ttl)/2 + ttl
                '''
                if icmp type is 3. means destination unreachable, it could be either our TTL is too high or just right.
                So we need to use the TTL in IP header that is included in ICMP packet, that TTL value will be the number of TTL
                left after my probe packet hit destination. If that ttl_left is more than 1. that means we are not using all the TTL to
                get the destination.
                '''
                if icmp_type[0]==3 and ip_ttl_left != 1:
                    if ttl < ttl_max:
                        ttl_max = ttl
                    if ttl_min < ttl/2:
                        ttl = ttl/2
                    else:
                        ttl = ttl-(ttl-ttl_min)/2   
                '''
                If TTL_left is 1 and ICMP type is 3. that means the probe packet reached my target server.
                '''             
                if icmp_type[0]==3 and ip_ttl_left == 1:
                    print dest_name, 'NUMBER OF HOPS:', ttl,'RTT is', RTT*1000,'ms'
                    break
               
        else:
            '''
            If some server or router do not reply our probe, as the project requirement said, I will double ttl if the value of
            2*ttl is less than our ttl_max, or the loop will be break.
            '''
            curr_host = "*"
            print "%d\t%s" % (ttl, curr_host)
            if ttl*2 < ttl_max:
                ttl=ttl*2
            else:
                print "Probing for", dest_name,dest_addr,'failed :('
                break 
                       
if __name__ == "__main__":
    main('google.com')
    main('facebook.com')
    main('blogspot.com')
    main('yandex.ru')
    main('google.es')
    main('xvideos.com')
    main('youku.com')
    main('cnn.com')
    main('redtube.com')
    main('google.pl')
    main('cnet.com')