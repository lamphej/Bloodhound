import redis
import os
import socket

# Redis Key Scheme
RK_HOSTNAME_KEY = 'HOSTNAMES'
RK_SOURCE_HOST = 'HOSTNAME|%s'
RK_DESTINATION_KEY = 'DEST|%s'
RK_TIME_KEY = 'TIME|%s'

listOfRedisIPAddresses = []
listOfRedisServers = {}
connectionAlreadyExists = 0
connectCommandFailure = 0


def csv_report(server, host_name=None):
    ret_list = []
    if host_name == None:
        pass
    else:
        time_keys = [x for x in server.keys(';'.join([RK_SOURCE_HOST % host_name, "TIME"]) + "*") if
                     len(x.split(';')) == 2]
        unique_times = list(sorted(set([x.split('|')[-1] for x in time_keys])))
        ret_list.append([
            unique_times[0],
            int(server.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[0]]), 'total'))
        ])
        cur_count = ret_list[0][1]
        cur_counts = []
        cur_counts.append(cur_count)
        for i in range(1, len(unique_times)):
            time_count = int(
                server.hget(';'.join([RK_SOURCE_HOST % host_name, RK_TIME_KEY % unique_times[i]]),
                            'total')) - sum(cur_counts)
            ret_list.append([
                unique_times[i],
                time_count
            ])
            cur_counts.append(time_count)
    outLines = []
    for x in ret_list:
        outLines.append(','.join([str(x[0]), str(x[1])]))
    f = '\r\n'.join([x for x in outLines])
    return f


print("Redis server remote access V1.0.\n")
print("To list commands, type \"help\".")

while True:

    userCommand = raw_input("\nCommand > ")
    parsedCommand = userCommand.split(" ")

    if parsedCommand[0].lower() == "help":
        print("")
        print("connect [ip address] [port number] - Connect to a redis server, IP address can\n\t\t\t\t     also be a web address.\n")
        print(
        "download [host name] [ip address] [file name] - Download redis data as\n\t\t\t\t\t       a CSV file, must be connected\n\t\t\t\t\t       to a redis server.\n")
        print("list - Shows a list of connected redis servers as IP addresses or web addresses.")
        print("connected [ip address] - Query to see if a redis server is connected.\n")
        print("clear - Clears the command window of text.\n")
        print("exit - Disconnect from all redis servers and close command interface.\n")

    elif parsedCommand[0].lower() == "connect":

        if parsedCommand.__len__() == 3:
            for x in listOfRedisIPAddresses:
                if parsedCommand[1] == x:
                    print("ERROR: ALREADY CONNECTED TO THIS SERVER.")
                    connectionAlreadyExists = 1
                    break

            if (connectionAlreadyExists == 0):

                try:
                    server = redis.StrictRedis(host=parsedCommand[1], port=int(parsedCommand[2]), db=0, socket_connect_timeout=5)
                    print("Connecting...")
                    # Check if the redis server actually exists.
                    server.ping()
                    listOfRedisServers[parsedCommand[1]] = server

                except redis.BusyLoadingError:
                    print("ERROR: REDIS SERVER START UP IN PROGRESS.")
                    connectCommandFailure = 1
                except redis.ConnectionError:
                    print("ERROR: CONNECTION FAILURE.")
                    print("Incorrect IP address or port number.")
                    connectCommandFailure = 1
                except redis.TimeoutError:
                    print("ERROR: CONNECTION ATTEMPT TIMEOUT.")
                    connectCommandFailure = 1

                if connectCommandFailure == 0:
                    # Print success message and add the new connection to the array of servers connected to.
                    print("Connection successful!")
                    listOfRedisIPAddresses.append(parsedCommand[1])
                else:
                    # Reset flags for next connection attempt by user.
                    connectionAlreadyExists = 0
                    connectCommandFailure = 0
        else:
            print("ERROR: INCORRECT NUMBER OF ARGUMENTS FOR COMMAND.")

    elif parsedCommand[0].lower() == "download":
        if listOfRedisIPAddresses.__len__() != 0:
            if parsedCommand.__len__() == 4:
                retrievedData = csv_report(listOfRedisServers[parsedCommand[2]], parsedCommand[1])
                csvFile = open(parsedCommand[3], "w")
                csvFile.write(retrievedData)
                csvFile.close()
                print "Filed saved to " + os.path.abspath(parsedCommand[2])
            else:
                print("ERROR: INCORRECT NUMBER OF ARGUMENTS FOR COMMAND.")
        else:
            print("There are no redis server connections.")

    elif parsedCommand[0].lower() == "list":
        if listOfRedisIPAddresses.__len__() == 0:
            print("There are no connected redis servers.")
        else:
            print("Printing IP addresses and web addresses of connected redis servers...")
            for x in listOfRedisIPAddresses:
                print(x)

    elif parsedCommand[0].lower() == "connected":
        i = 0
        exists = 0
        if parsedCommand.__len__() != 2:
            print("ERROR: INCORRECT NUMBER OF ARGUMENTS FOR COMMAND.")
        elif listOfRedisIPAddresses.__sizeof__() == 0:
            print("There are no redis servers connected.")
        else:
            for x in listOfRedisIPAddresses:
                if parsedCommand[1] == x:

                    try:
                        listOfRedisServers[x].ping()
                        print("Server is connected.")
                        exists = 1
                        break
                    except redis.ConnectionError:
                        print("ERROR: CONNECTION FAILURE.")
                        # Remove the broken connection from the list of active connections.
                        del listOfRedisServers[listOfRedisIPAddresses[i]]
                        del listOfRedisIPAddresses[i]
                i = (i + 1)

            if exists == 0:
                print("Connection does not exist.")

    elif parsedCommand[0].lower() == "clear":
        os.system( 'cls' if os.name == 'nt' else 'clear')

    elif parsedCommand[0].lower() == "exit":
        print("Closing all Redis connections....")
        print("Exiting interface...")
        exit()

    else:
        print("Command '%s' unrecognized" % parsedCommand[0])
