from datetime import datetime
from flask import Flask, render_template, request
import ujson
app = Flask(__name__)

@app.route('/')
def index():
    global network_data
    return render_template("index.html",
                           network_data=network_data,
                           client_count = len(network_data.keys())
                           )

@app.route('/json_report/<host_name>')
def json_report(host_name=None):
    global network_data
    ret_list = []
    if host_name == None:
        pass
    else:
        ret_list.append([
            network_data[host_name]["time_data"][0]["time"],
            int(network_data[host_name]["time_data"][0]["total"])
        ])
        for i in range(1, len(network_data[host_name]["time_data"])):
            ret_list.append([
                network_data[host_name]["time_data"][i]["time"],
                int(network_data[host_name]["time_data"][i]["total"]) - sum([x[1] for x in ret_list[0:i]])
            ])
    return ujson.dumps(ret_list)

@app.route('/report/submit', methods=["POST"])
def submit_report():
    global network_data
    js = ujson.loads(request.data)
    src_ip = js["src"]["ip"]
    src_name = js["src"]["name"]
    if not network_data.has_key(src_name):
        network_data[src_name] = {}
        network_data[src_name]["ip"] = src_ip
        network_data[src_name]["data"] = {}
        network_data[src_name]["time_data"] = []
    dst_data = js["data"]
    total_time_data = {
        "time": datetime.now(),
        "incoming": 0,
        "outgoing": 0,
        "total": 0
    }
    for dst_host in dst_data:
        dst_ip = dst_host["ip"]
        if not network_data[src_name]["data"].has_key(dst_ip):
            network_data[src_name]["data"][dst_ip] = []
        packet_counts = dst_host["packet_counts"]
        incoming_count = packet_counts["incoming"]
        total_time_data["incoming"] += incoming_count
        outgoing_count = packet_counts["outgoing"]
        total_time_data["outgoing"] += outgoing_count
        total_count = incoming_count + outgoing_count
        total_time_data["total"] += total_count
        time_data = {
            "time": datetime.now(),
            "incoming": incoming_count,
            "outgoing": outgoing_count,
            "total": total_count
        }
        network_data[src_name]["data"][dst_ip].append(time_data)
    network_data[src_name]["time_data"].append(total_time_data)
    return ujson.dumps({"status": "ok"})

if __name__ == '__main__':
    network_data = {}
    app.run(host="128.153.178.47")