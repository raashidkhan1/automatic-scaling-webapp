import logging
import threading
import subprocess
import argparse

HEADER_FIELD_NAMES = 'pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status,weight,act,bck,chkfail,chkdown,lastchg,downtime,qlimit,pid,iid,sid,throttle,lbtot,tracked,type,rate,rate_lim,rate_max,check_status,check_code,check_duration,hrsp_1xx,hrsp_2xx,hrsp_3xx,hrsp_4xx,hrsp_5xx,hrsp_other,hanafail,req_rate,req_rate_max,req_tot,cli_abrt,srv_abrt,comp_in,comp_out,comp_byp,comp_rsp,lastsess,last_chk,last_agt,qtime,ctime,rtime,ttime,'
current_stats = None

# command line argument for the script
# python controller --haproxy_stats_cmd "echo 'show stat' | nc -U /var/run/haproxy/haproxy.sock | grep 'backend-https,BACKEND'"

def parse_haproxy_stats(stat_output):
    l = stat_output.split(',')
    field_name_list = HEADER_FIELD_NAMES.split(',')
    haproxy_dict = {}

    i = 0
    for item in l:
        field_name = field_name_list[i]
        haproxy_dict[field_name] = item
        i = i + 1
    return haproxy_dict

def monitorLB(cmd):
    print("Monitoring LB")
    while True:
        exitcode, output = subprocess.getstatusoutput(cmd)
        current_stats = parse_haproxy_stats(output.strip())
        print("Status code", exitcode)

def autoScaler():
    print("Auto-scaling instances")

def createThreadInstance(targetfunc):
    logging.info("starting thread")
    thread = threading.Thread(target=targetfunc, args=())
    thread.start()
    logging.info("thread started")
    return thread

if __name__ == "main":
    print('Scaling Controller started...')
    parser = argparse.ArgumentParser()
    parser.add_argument('--haproxy_stats_cmd', default = '', \
                        required = True, help = "Command to get haproxy stats", type=str)
    l = parser.parse_args()

    cmd = l.haproxy_stats_cmd
    # create thread for monitorLB
    monitorThread = createThreadInstance(monitorLB)
    autoScalar = createThreadInstance(autoScaler)
