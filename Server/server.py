from datetime import datetime, timedelta
import os
from flask import Flask, render_template, request, Response

import ujson
import dateutil.parser
import redis
import time
app = Flask(__name__)

DATA_TTL = 60 * 60 * 24
REDIS_IP = ''

# Redis Key Scheme
RK_HOSTNAME_KEY = 'HOSTNAMES'
RK_SOURCE_HOST = 'HOSTNAME|%s'
RK_DESTINATION_KEY = 'DEST|%s'
RK_TIME_KEY = 'TIME|%s'


@app.route('/')
def index():
    global DATA_TTL
    network_data = {}
    all_keys = _redis_connection.keys("HOSTNAME|*")
    dest_keys = _redis_connection.keys("HOSTNAME|*;DEST|*")
    src_names = list(set([x.split(';')[0].replace("HOSTNAME|", "") for x in all_keys]))
    for name in src_names:
        network_data[name] = {
            "ip": _redis_connection.hmget(RK_SOURCE_HOST % name, "ip")[0],
            "data": {}
        }
        dest_ips = [x.split('|')[-1] for x in dest_keys if name in x]
        for dest_ip in dest_ips:
            network_data[name]["data"][dest_ip] = []
            dest_redis_key = ';'.join([RK_SOURCE_HOST % name, RK_DESTINATION_KEY % dest_ip])
            network_data[name]["data"][dest_ip].append({
                "incoming": _redis_connection.hget(dest_redis_key, 'incoming'),
                "outgoing": _redis_connection.hget(dest_redis_key, 'outgoing'),
                "total": _redis_connection.hget(dest_redis_key, 'total')
            })
    s = DATA_TTL
    hours = s // 3600
    # remaining seconds
    s = s - (hours * 3600)
    # minutes
    minutes = s // 60
    # remaining seconds
    seconds = s - (minutes * 60)
    ttl = "%s:%s:%s" % (hours, minutes, seconds)
    return render_template("index.html",
                           network_data=network_data,
                           client_count = len(network_data.keys()),
                           ttl=ttl
                           )

@app.route('/csv_report/<host_name>')
def csv_report(host_name=None):
    ret_list = []
    if host_name == None:
        pass
    else:
        time_keys = [x for x in _redis_connection.keys(';'.join([RK_SOURCE_HOST % host_name, "TIME"]) + "*") if len(x.split(';')) == 2]
        unique_times = list(sorted(set([x.split('|')[-1] for x in time_keys])))
        ret_list.append([
            unique_times[0],
            int(_redis_connection.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[0]]), 'total'))
        ])
        cur_count = ret_list[0][1]
        cur_counts = []
        cur_counts.append(cur_count)
        for i in range(1, len(unique_times)):
            time_count = int(
                _redis_connection.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[i]]), 'total')) - sum(cur_counts)
            ret_list.append([
                unique_times[i],
                time_count
            ])
            cur_counts.append(time_count)
    outLines = []
    for x in ret_list:
        outLines.append(','.join([str(x[0]), str(x[1])]))
    f =  '\r\n'.join([x for x in outLines])
    return Response(f, mimetype='text/csv')

def parse_date(param):
    d = dateutil.parser.parse(param)
    return time.mktime(d.timetuple())


@app.route('/json_report/<host_name>')
def json_report(host_name=None):
    ret_list = []
    if host_name == None:
        pass
    else:
        time_keys = [x for x in _redis_connection.keys(';'.join([RK_SOURCE_HOST % host_name, "TIME"]) + "*") if len(x.split(';')) == 2]
        unique_times = list(sorted(set([x.split('|')[-1] for x in time_keys])))
        ret_list.append([
            parse_date(unique_times[0]),
            int(_redis_connection.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[0]]), 'total'))
        ])
        cur_count = ret_list[0][1]
        cur_counts = []
        cur_counts.append(cur_count)
        for i in range(1, len(unique_times)):
            time_count = int(
                _redis_connection.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[i]]), 'total')) - sum(cur_counts)
            ret_list.append([
                parse_date(unique_times[i]),
                time_count
            ])
            cur_counts.append(time_count)
    return ujson.dumps(ret_list)

@app.route("/set_ttl", methods=["POST"])
def set_ttl():
    global DATA_TTL
    js = ujson.loads(request.form.keys()[0])
    ttl = [int(x) for x in js['ttl'].split(':')]
    DATA_TTL = ttl[0] * 3600 + ttl[1] * 60 + ttl[2]
    print "[+] Data TTL Set To %s" % DATA_TTL

@app.route('/report/submit', methods=["POST"])
def submit_report():
    global _redis_connection
    js = ujson.loads(request.data)
    src_ip = js["src"]["ip"]
    src_name = js["src"]["name"]
    src_key = RK_SOURCE_HOST % src_name
    r_tmp = _redis_connection.hgetall(src_key)
    if len(r_tmp.keys()) == 0:
        _redis_connection.hmset(src_key, {'ip': src_ip})
    time_key = RK_TIME_KEY % datetime.now()
    src_time_key = ';'.join([src_key, time_key])
    dst_data = js["data"]
    total_time_data = {
        "time": datetime.now(),
        "incoming": 0,
        "outgoing": 0,
        "total": 0
    }
    for dst_host in dst_data:
        dst_ip = dst_host["ip"]
        dest_redis_key = ';'.join([src_key, time_key, dst_ip])
        dest_total_key = ';'.join([src_key, RK_DESTINATION_KEY % dst_ip])
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
        _redis_connection.hmset(dest_redis_key, time_data)
        _redis_connection.expire(dest_redis_key, DATA_TTL)
        _redis_connection.hmset(dest_total_key, time_data)
    _redis_connection.hmset(src_time_key, total_time_data)
    return ujson.dumps({"status": "ok"})

if __name__ == '__main__':
    config = {}
    config = ujson.load(open('config.json', 'r'))
    REDIS_IP = config['redis']
    _redis_connection = redis.StrictRedis(host=REDIS_IP, port=6379, db=0)
    app.run(host=config['ip'])