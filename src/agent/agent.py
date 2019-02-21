#!/usr/bin/python2
import __init__
from comm.server import Server as Base_Server
import pika
from utils.log import SELOG
from utils.log import AGENTLOG
from utils.conf import CONF
from utils.ftime import format_time
import json
import time
import threading 
from Queue import Queue as Q
from comm.client import agent_to_server_msg

class Task:
    def __init__(self, msg):
        #{'type': 'item', 'req_id': msg['req_id'], 'project': msg['project_name'], 'info': msg['info']}
        #{'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
        # msg = {
        # 'type': 'check', 
        # 'project': self.project, 
        # 'req_id': self.req_id, 
        # "vm_info": self.vm_info,
        # "network_info": self.network_info
        # }
        self.type = msg['type']
        self.req_id = msg['req_id']
        self.project = msg['project']
        self.vm_info = msg['vm_info']
        self.network_info = msg["network_info"]
        self.info = None  
        self.status = None
        self.start_time = None
        self.stop_time = None

    def start_task(self):
        self.start_time = time.time()
        self.status = "START"

        # send to server
        msg = {
                'type': 'item', 
                'project': self.project, 
                'req_id': self.req_id, 
                "info": None
            }

        ret, info = self.get_info()
        if ret == False:
            self.status = "ERROR"
            AGENTLOG.error("agent.Task.start_task - project-%s - req_id-%s get_info return error:%s" 
                %(self.project, self.req_id, info))
            return False

        self.status = "STOP"
        # self.stop_time = time.time()
        # self.process

        msg["info"] = info
        ret, info = agent_to_server_msg(msg)
        
        if ret == False:
            self.status = "ERROR"
            AGENTLOG.error("agent.Task.start_task - project-%s - req_id-%s agent_to_server_msg return error:%s" 
                %(self.project, self.req_id, info))
            return False
        else:
            AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s task start success." %(self.project, self.req_id))
            return True

    def get_info(self):
        # to do
        return True, "info"


class Worker(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            task = self.queue.get()
            if type(task) == int and task == 1:
                AGENTLOG.info("agent.Worker.run - receive int 1, worker exit.")
                break
            elif type(task) == Task:
                AGENTLOG.info("agent.Worker.run - project-%s - req_id-%s get a task type:%s." %(task.project, task.req_id, task.type))
                ret = task.start_task()
                print ret
            else:
                # AGENTLOG.error("agent.Worker.run - project-%s - req_id-%s unkown task type:%s." %(task.project, task.req_id, task.type))
                AGENTLOG.info("agent.Worker.run - unknown task type, worker exit.")
                break

    def stop(self):
        self.queue.put(1)

class WorkerPoll:
    def __init__(self):
        self.queue = Q()
        self.worker_num = CONF.agent_conf['worker_num']
        self.worker_list = []
        self.worker_poll_flag = True
        for i in range(self.worker_num):
            self.worker_list.append(Worker(self.queue))

    def run(self):
        for w in self.worker_list:
            w.setDaemon(True)
            w.start()

    def stop(self):
        self.worker_poll_flag = False
        self.queue.join()
        for w in self.worker_list:
            w.stop()

    def push_task(self, task):
        if self.worker_poll_flag == True:
            self.queue.put(task)
            return True
        else:
            return False


class Server(Base_Server):
    def __init__(self, worker_poll, exchange = "agent", binding_keys = "", exchange_type = "fanout"):
        rabbit_conf = CONF.rabbitmq_conf
        host = rabbit_conf['host']
        port = rabbit_conf['port']
        username = rabbit_conf['username']
        passwd = rabbit_conf['passwd']
        vhost = rabbit_conf['vhost']
        self.worker_poll = worker_poll
        super(Server, self).__init__(exchange, binding_keys, exchange_type, host = host, port = port, username = username, 
        							passwd = passwd, vhost = vhost)

    def callback(self, ch, method, props, body):
        """
            body:message
            properties:prop.reply_to
        """
        # FALOG.error("receive msg routing_key with wrong format[part 2].")
        SERVERLOG.info("receive server to agent msg: %s" %(body))
        msg = json.loads(body)
        # {'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
        if msg['type'] == 'Item':
            self.worker_poll.push_task(Task(msg))
        else:
            SERVERLOG.error("receive api to server msg: invalid msg type %s" %(msg['type']))

        print(" [x] %r:%r" % (method.routing_key, body))

if __name__ == "__main__":
	#ser = Server()
	#ser.run()

    msg = {"type": "Item", "req_id": "1", "project": "admin", "vm_info": "None", "network_info": "None"} 

    wp = WorkerPoll()
    wp.run()
    wp.push_task(Task(msg))
    wp.push_task(Task(msg))
    wp.push_task(Task(msg))
    wp.stop()
