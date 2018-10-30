#!/usr/bin/python2
import __init__
from api_server import main
import sys
import os
import signal
from database import manager as dm
from rpc import rpc_check
from utils.log import SELOG

#def test(signum, frame):
#    f = open("test.txt", "a")
#    f.writelines("receive:%s\n" %signum)
#    #print("receive:", signum)
#    f.close()
#    sys.exit(0)


def start():
    print "start service"
    pid = os.getpid()
    #print "pid:%d" %pid
    #print "__file__" 
    #print __file__
    #print os.path.split(os.path.realpath(__file__))
    path = os.path.split(os.path.realpath(__file__))[0]
    f = os.path.join(path, "api.pid")
    fp = open(f, "w")
    fp.writelines(str(pid))
    fp.close()
    print "pid in " + f
    #os.system("/root/pre-online/pre_online/pre_online_api/api_server.py &")
    main()

def check():
    SELOG.info("----------------------------------------------------------------------")
    SELOG.info("[api] check [start]")
    db = dm.Manager()
    db.api_check()
    rpc_check.start_check()
    SELOG.info("[api] check [end]")


if __name__ == "__main__":
    check()
    start()