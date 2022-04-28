import logging
import threading
import argparse
import csv
from time import sleep
import urllib.request
import codecs

'''
Before running this script:
Run commands manually for 
1) create container
2) update haproxy.cfg with the template file- haproxy.cfg provided  
3) Commit changes to container and configure web app to start with the container
----------------------------------------------------------------------------------
-- command line argument for the script - ip and port of the LB in string format
-- For example: python3 controller.py --haproxy_ip "127.0.0.1:9999"
'''

current_stats = []

HEADER_FIELD_NAMES = 'pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status,weight,act,bck,chkfail,chkdown,lastchg,downtime,qlimit,pid,iid,sid,throttle,lbtot,tracked,type,rate,rate_lim,rate_max,check_status,check_code,check_duration,hrsp_1xx,hrsp_2xx,hrsp_3xx,hrsp_4xx,hrsp_5xx,hrsp_other,hanafail,req_rate,req_rate_max,req_tot,cli_abrt,srv_abrt,comp_in,comp_out,comp_byp,comp_rsp,lastsess,last_chk,last_agt,qtime,ctime,rtime,ttime,agent_status,agent_code,agent_duration,check_desc,agent_desc,check_rise,check_fall,check_health,agent_rise,agent_fall,agent_health,addr,cookie,mode,algo,conn_rate,conn_rate_max,conn_tot,intercepted,dcon,dses,wrew,connect,reuse,cache_lookups,cache_hits,srv_icur,src_ilim,qtime_max,ctime_max,rtime_max,ttime_max,'

# function to parse output from CSV into a dictionary
def parse_haproxy_stats(stat_output):
    l = stat_output
    field_name_list = HEADER_FIELD_NAMES.split(',')
    haproxy_dict = {}

    i = 0
    for item in l:
        field_name = field_name_list[i]
        haproxy_dict[field_name] = item
        i = i + 1
    return haproxy_dict  

# function to create a new haproxy.cfg file in current directory as /config/haproxy.cfg
# To be used for updating active backend IPs and copy this file inside container
# usage: update_haproxy_cfg(['127.0.0.1:5000', '127.0.0.2:5000'])
def update_haproxy_cfg(ip_list=[]):
    appendContents = ""
    contents = ""
    i=1
    for ip in ip_list:
        server = "server web"+str(i)+" "+ip+" check"
        i += 1
        appendContents += "\n    "+server+"\n"
    readFile = open("haproxy.cfg", "r")
    if readFile.mode == 'r':
        contents = readFile.read()
        contents += appendContents
    # print(contents)
    writeFile = open("./config/haproxy.cfg", "w+")
    writeFile.write(contents)
    writeFile.close()

#creates and starts threads
#usage: createThreadInstance(functionname, arguments)
def createThreadInstance(targetfunc, cmd=''):
    logging.info("starting thread")
    thread = threading.Thread(target=targetfunc, args=(cmd,))
    thread.start()
    logging.info("thread started")
    return thread

# monitors LB backend to fetch stats in CSV format using the IP
# usage : monitorLB('127.0.0.1:9999')
def monitorLB(ip):
    print("Monitoring LB")
    global current_stats
    # print(current_stats)
    csvOutputURL = "http://"+ip+"/stats;csv"
    # print('csvOutput', csvOutputURL)
    while True:
        response = urllib.request.urlopen(csvOutputURL)
        cr = csv.reader(codecs.iterdecode(response, 'utf-8'))
        backend_stats = ''
        for row in cr:
            if len(row) == 95:
                if row[0].startswith('web') & row[1].startswith('web'):
                    backend_stats = row
                    current_stats.append(parse_haproxy_stats(backend_stats))
        # print(current_stats[0]['rtime'])
        sleep(2)

# function to start stop instances based on metrics from monitorLB
def autoScaler(stats):
    print("Auto-scaling instances")
    while True:
        print(current_stats)
        sleep(2)

# main function for scaling controller
def main():
    print('Scaling Controller started...')
    parser = argparse.ArgumentParser()
    parser.add_argument('--haproxy_ip', default = '', \
                        required = True, help = "Command to get haproxy stats", type=str)
    l = parser.parse_args()

    cmd = l.haproxy_ip
    print(type(cmd))
    # create thread for monitorLB
    monitorThread = createThreadInstance(monitorLB, cmd)
    #create thread for autoScalar
    autoScalar = createThreadInstance(autoScaler, current_stats)
    # wait for autoscalar to finish before monitoring again
    autoScalar.join()

main()

