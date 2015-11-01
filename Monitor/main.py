import json
import threading
from scapy.all import *
import pprint
import requests

INTERVAL = 5


def insert_new_ip(src_ip):
    packet_data[src_ip] = {}
    packet_data[src_ip]["count"] = 0
    packet_data[src_ip]["incoming"] = 0
    packet_data[src_ip]["outgoing"] = 0


def customAction(packet):
    global packetCount, packet_data, monitor_config
    packetCount += 1
    try:
        inbound = False
        src_ip = packet[0][1].src
        dst_ip = packet[0][1].dst
        src_mac = packet[Ether].src
        if not src_ip == our_ip:
            inbound = True
            if not packet_data.has_key(src_ip):
                insert_new_ip(src_ip)
            packet_data[src_ip]["count"] += 1
            packet_data[src_ip]["incoming"] += 1
        else:
            if not packet_data.has_key(dst_ip):
                insert_new_ip(dst_ip)
            packet_data[dst_ip]["count"] += 1
            packet_data[dst_ip]["outgoing"] += 1
    except:
        pass

def send_reports():
    global packet_data, monitor_config, INTERVAL
    while True:
        report_url = monitor_config["report_url"]
        report_dict = {
            "src": {
                "name": our_name,
                "ip": our_ip
            },
            "data": [

            ]
        }
        for dest_ip in packet_data.keys():
            report_dict["data"].append({
                "ip": dest_ip,
                "packet_counts": {
                    "incoming": packet_data[dest_ip]["incoming"],
                    "outgoing": packet_data[dest_ip]["outgoing"]
                }
            })
        requests.post(report_url, data=json.dumps(report_dict))
        time.sleep(INTERVAL)

if __name__ == "__main__":
    our_name = socket.gethostname()
    our_ip = socket.gethostbyname(socket.gethostname())
    monitor_config = json.loads(open("config.json", "r").read())
    INTERVAL = monitor_config['interval']
    packetCount = 0
    packet_data = {}
    t = threading.Thread(target=send_reports)
    t.start()
    sniff(prn=customAction)
    pprint.pprint(packet_data)