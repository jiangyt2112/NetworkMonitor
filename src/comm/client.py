#!/usr/bin/python2

import pika
import sys
import uuid

class Client(object):
    def __init__(self, exchange, routing_key, message = "", username = 'network_monitor', passwd = '111111', vhost = "network_monitor",
                host = '192.168.122.9', port = 5672):
        self.credentials = pika.PlainCredentials(username, passwd)
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port, '/', credentials))
        # self.channel = self.connection.channel()
        self.host = host
        self.port = port
        self.vhost = vhost
        self.message = str(message)
        self.exchange = exchange
        self.routing_key = routing_key

    def connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host, self.port, self.vhost, self.credentials))
        self.channel = self.connection.channel()

    def rpc_call(self):
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response, no_ack=True,
                            queue= self.callback_queue) 

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            # print body 
            self.response = body

    def __call__(self):
        try:
            self.connect()
        except Exception, e:
            print str(e)
            self.close()
            return False, str(e)

        self.response = None
        if False and self.routing_key.split('.')[1] == rpc:
            self.corr_id = str(uuid.uuid4())
            self.rpc_call()
            try:
                self.channel.basic_publish(exchange = self.exchange,
                                    routing_key = self.routing_key,
                                    properties = pika.BasicProperties(
                                                    reply_to = self.callback_queue,
                                                    correlation_id = self.corr_id),
                                    body = self.message)
            
                while self.response is None:
                    self.connection.process_data_events()
                self.close()
            except Exception, e:
                print str(e)
                self.close()
                return False, str(e)
            return True, self.response
        else:
            try:
                self.channel.basic_publish(exchange = self.exchange,
                                        routing_key = self.routing_key,
                                        body = self.message)
                self.close()
            except Exception, e:
                print str(e)
                self.close()
                return False, str(e)
            return True, None

    def close(self):
        print "close connection"
        try:
            self.channel.close()
            self.connection.close()
        except Exception, e:
            pass

    def __del__(self):
        pass

def start_re_rpc(vm_id):
    # start resource evaluation rpc
    req_id = "req-" + str(uuid.uuid4())
    msg = {"req_id": req_id, "vm_id": vm_id}
    rpc_client("network_monitor", "start_re", msg)
    

def end_re_rpc(vm_id):
    # end resource evaluation rpc
    req_id = "req-" + str(uuid.uuid4())
    msg = {"req_id": req_id, "vm_id": vm_id}
    rpc_client("network_monitor", "end_re", msg)

if __name__ == "__main__":
    req_id = str(uuid.uuid4())
    vm_id = str(uuid.uuid4()) 
    msg = {"req_id": req_id, "vm_id": vm_id}
    rpc_client = Client("server", "api_to_server", msg)
    rpc_client()
    # rpc_client()

