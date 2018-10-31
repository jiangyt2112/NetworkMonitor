#!/usr/bin/python2
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from api import app
import os
import multiprocessing
import sys
import signal
from utils.conf import CONF
from utils.log import APILOG

class ApiServer(object):
    """
        api server class
    """
    def __init__(self, port):
        self.port = port
    
    def run(self):
        # run api server 
        http_server = HTTPServer(WSGIContainer(app))
        try:
            http_server.listen(self.port)
        except Exception, e:
            print "Can not start api server!"
            print "Error:" + str(e)
            sys.exit()
        else:
            print "Start api server successfully, listen port:%d" %self.port
            print "Ctrl+C to stop"
            IOLoop.instance().start()

def handler(signum, frame):
    APILOG.info("sigterm")
    os.exit(0)

def run_server():
    signal.signal(signal.SIGTERM, handler)
    port = CONF.api_conf['port']
    api_server = ApiServer(port)
    api_server.run()

def main():
    run_server()

if __name__ == "__main__":
    main()