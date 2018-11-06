#!/usr/bin/python2
import __init__
from comm.server import Server as Base_Server
import pika
from utils.log import SELOG
from utils.conf import CONF
from utils.ftime import format_time
import json

class Server(Base_Server):
    def __init__(self, exchange = "agent", binding_keys = "", exchange_type = "fanout"):
        rabbit_conf = CONF.rabbitmq_conf
        host = rabbit_conf['host']
        port = rabbit_conf['port']
        username = rabbit_conf['username']
        passwd = rabbit_conf['passwd']
        vhost = rabbit_conf['vhost']
        super(Server, self).__init__(exchange, binding_keys, exchange_type, host = host, port = port, username = username, 
        							passwd = passwd, vhost = vhost)

    def callback(self, ch, method, props, body):
        """
            body:message
            properties:prop.reply_to
        """
        # FALOG.error("receive msg routing_key with wrong format[part 2].")
        
    
        print(" [x] %r:%r" % (method.routing_key, body))

if __name__ == "__main__":
	ser = Server()
	ser.run()