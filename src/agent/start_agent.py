#!/usr/bin/python2
import __init__
from agent import Server
from utils.log import SELOG
import os
import signal
import sys

global server

def sigint_callback(signum, frame):
    SELOG.info("-" * 71)
    SELOG.info("receive sigint, agent service stop")
    #re.re_manager.end_all()
    sys.exit(0)

def start():
    print "start service"
    pid = os.getpid()
    #print "pid:%d" %pid
    #print "__file__" 
    #print __file__
    #print os.path.split(os.path.realpath(__file__))
    path = os.path.split(os.path.realpath(__file__))[0]
    f = os.path.join(path, "agent.pid")
    fp = open(f, "w")
    fp.writelines(str(pid))
    fp.close()
    print "pid in " + f 
    global server
    server = Server()
    #signal.signal(signal.SIGINT, sigint_callback)
    signal.signal(signal.SIGTERM, sigint_callback)
    server.run()

def check():
    SELOG.info("----------------------------------------------------------------------")
    SELOG.info("[agent] check [start]")
    #rpc_check.start_check()
    SELOG.info("[agent] check [end]")

if __name__ == "__main__":
    # start()
    check()
    start()