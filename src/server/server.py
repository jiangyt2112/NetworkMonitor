#!/usr/bin/python2
import __init__
from comm.server import Server as Base_Server
import pika
from utils.log import SELOG, SERVERLOG
from utils.conf import CONF
from utils.ftime import format_time
import json
import threading 
import Queue as q

class Task:
    def __init__(self, msg):
        #{'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
        self.type = msg['type']
        self.req_id = msg['req_id']
        self.project = msg['project']
        self.token = msg['token']
        self.get_info_from_openstack()
        self.status = None
        self.start_time = None

    def get_info_from_openstack(self):
        self.network_info = None
        self.vm_info = None
        self.vm_num = 0
        self.receive_vm_num = 0
        self.receive_network_num = 0
        self.result = None
    
    def is_down(self):
        return False    

    def start_task(self):
        pass

    def stop_task(self):
        pass

class Tasks:
    def __init__(self):
        self.num = 0
        self.tasks = {}

    def append(self, task):
        pass

    def update_task(self, item):
        pass

    


class Item:
    def __init__(self):
        pass

class Worker:
    def __init__(self):
        pass

class WorkerPoll:
    def __init__(self):
        pass

class Server(Base_Server):
    def __init__(self, exchange = "server", binding_keys = ["api_to_server.*", "agent_to_server.*"], exchange_type = "topic"):
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
        msg_type = method.routing_key.split(".")
        if len(msg_type) != 2:
            FALOG.error("receive msg routing_key with wrong format.")

        if msg_type[0] == "api_to_server":
            # other process
            if msg_type[1] == "rpc":
                response = {
                        "task_type": "test",
                        "exe_res": True,
                        "error_msg": "",
                        #"req_id": eval(body)['req_id'],
                        #"vm_id": eval(body)['vm_id'],
                        #"task_start_time": 
                        #time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eval(body)['start_time']))
                        }
                ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response))
            elif msg_type[1] == "msg":
                SERVERLOG.info("receive api to server msg: %s" %(body))
                msg = json.loads(body)
                # {'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
                if msg['type'] == 'check':
                    pass
                    # 建立对象，加入队列
                else:
                    SERVERLOG.error("receive api to server msg: invalid msg type %s" %(msg['type']))
            else:
                FALOG.error("receive msg routing_key with wrong format[part 2].")
            
        elif msg_type[0] == "agent_to_server":
            if msg_type[1] == "rpc":
                response = {
                        "task_type": "test",
                        "exe_res": True,
                        "error_msg": "",
                        #"req_id": eval(body)['req_id'],
                        #"vm_id": eval(body)['vm_id'],
                        #"task_end_time": 
                        #time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eval(body)['end_time']))
                        }
                ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response))
            elif msg_type[1] == "msg":
                SERVERLOG.info("receive agent to server msg: %s" %(body))
                msg = json.loads(body)
                # {'type': 'item', 'req_id': msg['req_id'], 'project': msg['project_name'], 'info': msg['info']}
                if msg['type'] == 'check':
                    pass
                    # 建立对象，加入队列
                else:
                    SERVERLOG.error("receive agent to server msg: invalid msg type %s" %(msg['type']))
            else:
                FALOG.error("receive msg routing_key with wrong format[part 2].")
            # other process
        else:
            FALOG.error("receive msg routing_key with wrong format[part 1].")
            
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print(" [x] %r:%r" % (method.routing_key, body))

if __name__ == "__main__":
	ser = Server()
	ser.run()
