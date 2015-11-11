import redis
import os

# Redis Key Scheme
RK_HOSTNAME_KEY = 'HOSTNAMES'
RK_SOURCE_HOST = 'HOSTNAME|%s'
RK_DESTINATION_KEY = 'DEST|%s'
RK_TIME_KEY = 'TIME|%s'

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
    return f

print("Redis server remote access.\n")
print("To list commands, type \"help\".")

while True:

    userCommand = raw_input("\nCommand > ")
    parsedCommand = userCommand.split(" ")

    if parsedCommand[0] == "help":
        print("connect [ip address] [port number] - Connect to a redis server.")
        print("download [host name [filename] - download redis data as a CSV file, must be connected to a redis server.")
        print("exit - Disconnect from a redis server and close command interface.")
    elif parsedCommand[0] == "connect":

        _redis_connection = redis.StrictRedis(host=parsedCommand[1], port=int(parsedCommand[2]), db=0,
                                              socket_connect_timeout = 10)
        print("connected!")

    elif parsedCommand[0] == "download":
        retrievedData = csv_report(parsedCommand[1])
        csvFile = open(parsedCommand[2], "w")
        csvFile.write(retrievedData)
        csvFile.close()
        print "Filed saved to " + os.path.abspath(parsedCommand[2])

    elif parsedCommand[0] == "exit":
        print("Closing Redis connection....")
        print("Exiting interface...")
        exit()
    else:
        print("Command '%s' unrecognized" % parsedCommand[0])