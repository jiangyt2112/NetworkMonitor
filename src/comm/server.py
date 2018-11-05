#!/usr/bin/python2
import __init__
from utils.log import FALOG
import time
import pika
import sys

class Server(object):
    def __init__(self, exchange, binding_keys, username = 'network_monitor', passwd = '111111', vhost = 'network_monitor',
                host = '192.168.122.9', port = 5672):

        credentials = pika.PlainCredentials(username, passwd)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port, vhost, credentials))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange= exchange,
                                exchange_type='topic')

        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue


        for binding_key in binding_keys:
            self.channel.queue_bind(exchange=exchange,
                                    queue=queue_name,
                                    routing_key=binding_key)

        print(' [*] Waiting for logs. To exit press CTRL+C')

        #self.callback()
        self.channel.basic_qos(prefetch_count = 1)
        self.channel.basic_consume(self.callback,
                               queue=queue_name)

    def run(self):
        try:
            self.channel.start_consuming() 
        except Exception, e:
            print str(e)
            FALOG.error("network-monitor service down:%s" %(str(e)))
            sys.exit(1)

    def callback(self, ch, method, props, body):
        """
            body:message
            properties:prop.reply_to
        """
        if method.routing_key == "api_to_server":
            # other process
            response = {
                        "task_type": "start_re",
                        "exe_res": True,
                        "error_msg": "",
                        #"req_id": eval(body)['req_id'],
                        #"vm_id": eval(body)['vm_id'],
                        #"task_start_time": 
                        #time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eval(body)['start_time']))
                        }

        elif method.routing_key == "agent_to_server":
            # other process
            response = {
                        "task_type": "end_re",
                        "exe_res": True,
                        "error_msg": "",
                        #"req_id": eval(body)['req_id'],
                        #"vm_id": eval(body)['vm_id'],
                        #"task_end_time": 
                        #time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eval(body)['end_time']))
                        }
        else:
            response = "rpc routing_key"
 
            ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(" [x] %r:%r" % (method.routing_key, body))


class T(Server):
    def __init__(self, exchange, binding_keys):
        super(T, self).__init__(exchange, binding_keys)
    #def callback(self):
    #    print "aaaaa"
    # override callback    

if __name__ == "__main__":
    server = Server("server", ["api_to_server", "agent_to_server"])
    server.run()
    #t = T("top", ["bbb"])
