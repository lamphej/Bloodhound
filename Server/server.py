from flask import Flask, render_template, request
import json
app = Flask(__name__)

@app.route('/')
def index():
    global network_data
    return render_template("index.html", network_data=network_data)

@app.route('/report/submit', methods=["POST"])
def submit_report():
    global network_data
    js = json.loads(request.data)
    src_ip = js["src"]["ip"]
    src_name = js["src"]["name"]
    if not network_data.has_key(src_name):
        network_data[src_name] = {}
        network_data[src_name]["ip"] = src_ip
        network_data[src_name]["data"] = {}
    dst_data = js["data"]
    for dst_host in dst_data:
        dst_ip = dst_host["ip"]
        if not network_data[src_name]["data"].has_key(dst_ip):
            network_data[src_name]["data"][dst_ip] = {}
        packet_counts = dst_host["packet_counts"]
        incoming_count = packet_counts["incoming"]
        outgoing_count = packet_counts["outgoing"]
        total_count = incoming_count + outgoing_count
        network_data[src_name]["data"][dst_ip]["incoming"] = incoming_count
        network_data[src_name]["data"][dst_ip]["outgoing"] = outgoing_count
        network_data[src_name]["data"][dst_ip]["total"] = total_count
    return json.dumps({"status": "ok"})

if __name__ == '__main__':
    network_data = {}
    app.run()