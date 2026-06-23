from scapy.all import *

def redirect_packet(packet):
    if packet.haslayer(IP):
        packet[IP].dst = "192.168.0.199"
        
        send(packet,verbose=False)
        
sniff(prn=redirect_packet,filter="ip",store=False)