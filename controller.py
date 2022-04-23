import logging
import threading



def monitorLB(cmd):
    print("Monitoring LB")
    while True:


def createThreadInstance(targetfunc):
    logging.info("starting thread")
    thread = threading.Thread(target=targetfunc, args=())
    thread.start()
    logging.info("thread started")

if __name__ == "main":
    print('Scalling Controller started...')