import logging
import threading
import argparse
import csv
import time
from threading import Event
import urllib.request
import codecs
from podman import PodmanClient
import os
import tarfile


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

# metrics for calibration
MAX_RTIME = 300 # in ms
MAX_ECON = 5
MAX_QCUR = 5
MIN_QCUR = 1

# src and dst for haproxy
SRC_HAPROXYCFG = "/haproxy.cfg"
DST_HAPROXY = "myhaproxy:/etc/haproxy/haproxy.cfg"

# reload haproxy lb command
RELOAD_HAPROXY_CMD = "podman exec -d myhaproxy haproxy -f /etc/haproxy/haproxy.cfg"
# kill all the haproxy process
KILL_ALL_HAPROXY = "podman exec myhaproxy killall haproxy"
# headers
HEADER_FIELD_NAMES = 'pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status,weight,act,bck,chkfail,chkdown,lastchg,downtime,qlimit,pid,iid,sid,throttle,lbtot,tracked,type,rate,rate_lim,rate_max,check_status,check_code,check_duration,hrsp_1xx,hrsp_2xx,hrsp_3xx,hrsp_4xx,hrsp_5xx,hrsp_other,hanafail,req_rate,req_rate_max,req_tot,cli_abrt,srv_abrt,comp_in,comp_out,comp_byp,comp_rsp,lastsess,last_chk,last_agt,qtime,ctime,rtime,ttime,agent_status,agent_code,agent_duration,check_desc,agent_desc,check_rise,check_fall,check_health,agent_rise,agent_fall,agent_health,addr,cookie,mode,algo,conn_rate,conn_rate_max,conn_tot,intercepted,dcon,dses,wrew,connect,reuse,cache_lookups,cache_hits,srv_icur,src_ilim,qtime_max,ctime_max,rtime_max,ttime_max,eint,idle_conn_cur,safe_conn_cur,used_conn_cur,need_conn_est,uweight,agg_server_check_status,-,ssl_sess,ssl_reused_sess,ssl_failed_handshake,h2_headers_rcvd,h2_data_rcvd,h2_settings_rcvd,h2_rst_stream_rcvd,h2_goaway_rcvd,h2_detected_conn_protocol_errors,h2_detected_strm_protocol_errors,h2_rst_stream_resp,h2_goaway_resp,h2_open_connections,h2_backend_open_streams,h2_total_connections,h2_backend_total_streams,'
#initialize PodmanClient
client = PodmanClient(base_url="unix:///run/podman/podman.sock")
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

# function to create a new haproxy.cfg file in current directory as haproxy.cfg using template from ./config/haproxy.cfg
# To be used for updating active backend IPs and copy this file inside container
# usage: update_haproxy_cfg(['127.0.0.1:5000', '127.0.0.2:5000'])
def update_haproxy_cfg(ip_list=[]):
    appendContents = ""
    contents = ""
    i=1
    for ip in ip_list:
        server = "server web"+str(i)+" "+ip+":5000 check"
        i += 1
        appendContents += "\n    "+server+"\n"
    readFile = open("./template.cfg", "r")
    if readFile.mode == 'r':
        contents = readFile.read()
        contents += appendContents
    # print(contents)
    writeFile = open("./haproxy.cfg", "w+")
    writeFile.write(contents)
    writeFile.close()

#creates and starts threads
#usage: createThread(functionname, arguments)
def createThread(targetfunc, cmd=''):
    logging.info("starting thread")
    thread = threading.Thread(target=targetfunc, args=(cmd,))
    thread.setDaemon(True)
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
        try:
            response = urllib.request.urlopen(csvOutputURL)
            cr = csv.reader(codecs.iterdecode(response, 'utf-8'))
            backend_stats = ''
            for row in cr:
                if row[0].startswith('web') & row[1].startswith('web'):
                    backend_stats = row
                    current_stats.append(parse_haproxy_stats(backend_stats))
        except Exception as e:
            print(e)
        # print(current_stats[0]['svname'], "monitor")
        # wait for stats to update based on number of requests
        time.sleep(10)

def perform_reset():
    IP_list = []
    # for getting a list of running webservers containers
    for c in client.containers.list(filters={'ancestor': 'testcontainer'}):
        x = client.containers.get(c.name)
        if x.status == "running":
            IPconts = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
            IP_list.append(IPconts)
            print(IP_list)
    #------------------------ updating the config file
    update_haproxy_cfg(IP_list)
    #--------------------------copy the config file to the HAproxy container
    Event().wait(2)
    print("Copying HAproxy from", SRC_HAPROXYCFG, "to", DST_HAPROXY)
    copy_to(SRC_HAPROXYCFG,DST_HAPROXY)
    #-------------------------- restart Haproxy
    Event().wait(5)
    print("Copied")
    #kill existing reload processes
    print("Killing all haproxy services")
    os.system(KILL_ALL_HAPROXY)
    # give enough time to kill before reloading
    Event().wait(5)
    #restart haproxy service
    print("Reloading HAproxy")
    os.system(RELOAD_HAPROXY_CMD)
    # give enough time to reload
    Event().wait(10)
    print("Reloaded")


# function to start stop instances based on metrics from monitorLB
def autoScaler(stats):
    print("Auto-scaling instances")
    while True:
        for webserver in current_stats:   # we check the metrics for each webserver in our HAproxy config file
            print("Checking existing webserver", webserver['svname'])
            if int(webserver["rtime"]) > MAX_RTIME:  # scale up 
                z = client.containers.run('testcontainer', detach=True, auto_remove=True,   # running  a container with predefined image and do the mounting for storing objects
                                        volumes={'objecttt': {'bind': "/objects"}})
                Event.wait(2)
                x = client.containers.get(z.name)
                if x.status == "running":
                    IPcont = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
                    print('MAX_RTIME reached Scaling up with', IPcont)
                perform_reset()
                break

            if int(webserver['econ']) > MAX_ECON:  # scale up if number of requests that encountered an error trying to connect to a backend server
                z = client.containers.run('testcontainer', detach=True, auto_remove=True,
                                        volumes={'objecttt': {'bind': "/objects"}})
                Event.wait(2)
                x = client.containers.get(z.name)
                if x.status == "running":
                    IPcont = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
                    print('MAX_ECON reached Scaling up with', IPcont)
                perform_reset()
                break

            if int(webserver['qcur']) > MAX_QCUR:  # scale up 
                z = client.containers.run('testcontainer', detach=True, auto_remove=True,
                                        volumes={'objecttt': {'bind': "/objects"}})
                Event.wait(2)
                x = client.containers.get(z.name)
                if x.status == "running":
                    IPcont = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
                    print('MAX_QCUR reached Scaling up with', IPcont)
                perform_reset()
                break
            
            #perform downscaling only when the available number of containers is more than 1
            if len(current_stats) > 1:
                if int(webserver['qcur']) < MIN_QCUR:  # scale down if there are no requests in queue
                    for c in client.containers.list(filters={'ancestor': 'testcontainer'}):
                        x = client.containers.get(c.name)
                    if x.status == "running":
                        x.stop()
                        Event.wait(2)
                        IPconts = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
                        print('MIN_QCUR reached Scaling down', IPconts)
                    perform_reset()
                    break

                if int(webserver['bin']) == 0 and int(webserver['bout']) == 0:  # scale down
                    for c in client.containers.list(filters={'ancestor': 'testcontainer'}):
                        y = client.containers.get(c.name)
                    if y.status == "running":
                        y.stop()
                        Event.wait(2)
                        IPconts = y.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
                        print('bin is zero reached Scaling down', IPconts)
                    perform_reset()
                    break
        # wait for some time before rechecking the containers 
        time.sleep(10)


def copy_to(src, dst):  # to copy the config file from controller to HAproxy container
    name, dst = dst.split(':')
    container = client.containers.get(name)
    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()

    data = open(src + '.tar', 'rb').read()
    container.put_archive(os.path.dirname(dst), data)


# main function for scaling controller
def main():
    print('Scaling Controller started...')
    parser = argparse.ArgumentParser()
    parser.add_argument('--haproxy_ip', default = '', \
                        required = True, help = "Command to get haproxy stats", type=str)
    l = parser.parse_args()

    cmd = l.haproxy_ip
    # create thread for monitorLB
    monitorThread = createThread(monitorLB, cmd)
    #wait for monitoring thread to start and update current_stats
    time.sleep(1)
    #create thread for autoScalar
    autoScalarThread = createThread(autoScaler)
    monitorThread.join()
    autoScalarThread.join()

main()
