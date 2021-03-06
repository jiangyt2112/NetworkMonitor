#!/usr/bin/python2
import __init__
from comm.server import Server as Base_Server
import pika
from utils.log import SELOG
from utils.log import AGENTLOG
from utils.log import SERVERLOG
from utils.conf import CONF
from utils.ftime import format_time
import json
import time
import threading 
from Queue import Queue as Q
from comm.client import agent_to_server_msg
from func import get_vm_uuids
from func import get_hostname
from func import get_host_ip
from func import is_network_node
from func import get_topo
from func import check_service_status
from func import check_network_config
from func import check_network_connection
#from func import get_vm_topo
from func import health_flag# = True
from func import function_fault# = []
from func import performance_fault# = []
from func import get_mem_rate
from func import get_cpu_rate


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
        # [{"id": 1}, {}, {}]
        self.vm_info = msg['vm_info']
        self.valid_vm_info = None
        self.network_info = msg["network_info"]
        self.info = None  
        self.status = None
        self.start_time = None
        self.stop_time = None

    def start_task(self):

        if self.is_consumer():
            AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s receive task and is consumer." 
                %(self.project, self.req_id))
        else:
            AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s receive task and not the task's consumer, return." 
                %(self.project, self.req_id))
            return True

        self.start_time = time.time()
        self.status = "START"

        # send to server
        msg = {
                'type': 'item', 
                'project': self.project, 
                'req_id': self.req_id,
                'info': None 
            }
        
        AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s get_info start." %(self.project, self.req_id))
        ret, info = self.get_info()
        AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s get_info done." %(self.project, self.req_id))

        if ret == False:
            self.status = "ERROR"
            AGENTLOG.error("agent.Task.start_task - project-%s - req_id-%s get_info return error:%s" 
                %(self.project, self.req_id, info))
            return False

        self.status = "STOP"
        # self.stop_time = time.time()
        # self.process

        msg["info"] = info

        AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s agent_to_server_msg start."
          %(self.project, self.req_id))
        ret, info = agent_to_server_msg(msg)
        AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s agent_to_server_msg done."
          %(self.project, self.req_id))

        if ret == False:
            self.status = "ERROR"
            AGENTLOG.error("agent.Task.start_task - project-%s - req_id-%s agent_to_server_msg return error:%s" 
                %(self.project, self.req_id, info))
            return False
        else:
            AGENTLOG.info("agent.Task.start_task - project-%s - req_id-%s task start success." %(self.project, self.req_id))
            return True

    def is_consumer(self):
        ret, uuids = get_vm_uuids()
        if ret == False:
            AGENTLOG.info("agent.Task.is_consumer - project-%s - req_id-%s get uuids error:%s." %(self.project, self.req_id, uuids))
            return False
        #print uuids 
        self.valid_vm_info = []
        for info in self.vm_info:
            #print info["id"]
            if info["id"] in uuids:
                self.valid_vm_info.append(info)

        return len(self.valid_vm_info) > 0

    def get_info(self):
        # to do
        hostname = get_hostname()
        ips = get_host_ip()
        network_node_flag = is_network_node()
        cpu_rate = get_cpu_rate()
        mem_rate = get_mem_rate()
    
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s check_service start." 
        %(self.project, self.req_id))
        ret, service_status = check_service_status()
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s check_service done." 
                %(self.project, self.req_id))

        print "monitor project %s: get project network data model." %(self.project)
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s get topo start." 
                %(self.project, self.req_id))
        ret, topo = get_topo(self.valid_vm_info, self.network_info)
        if ret == False:
            AGENTLOG.error("agent.Task.get_info - project-%s - req_id-%s get topo error:%s." 
                %(self.project, self.req_id, topo))
            return False, topo
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s get topo done." 
                %(self.project, self.req_id))

        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s check_network_config start." 
                %(self.project, self.req_id))
        print "monitor project %s: check network config." %(self.project)
        check_network_config(topo)
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s gcheck_network_config done." 
                %(self.project, self.req_id))
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s check_network_connection start." 
                %(self.project, self.req_id))
        print "monitor project %s: check network connection." %(self.project)
        check_network_connection(topo)
        AGENTLOG.info("agent.Task.get_info - project-%s - req_id-%s check_network_connection done." 
                %(self.project, self.req_id))
        
        if network_node_flag:
            node_type = "network"
        else:
            node_type = "compute"

        info = {
            'vm_num': len(self.valid_vm_info),
            'hostname': hostname,
            'host': ips,
            'node_type': node_type,
            'topo': topo,
            'check': {"cpu_rate": cpu_rate, "mem_rate": mem_rate, "service": service_status, "error_msg": ""},
            'summary':{'health_flag': health_flag, 'function_fault': function_fault, 
                'performance_fault': performance_fault}
        }
        return True, info


class Worker(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        #print "worker is running"
        while True:
            task = self.queue.get()

            if isinstance(task, int) and task == 1:
                AGENTLOG.info("agent.Worker.run - receive int 1, worker exit.")
                self.queue.task_done()
                break
            elif isinstance(task, Task):
                AGENTLOG.info("agent.Worker.run - project-%s - req_id-%s get a task type:%s." %(task.project, task.req_id, task.type))
                ret = task.start_task()
                self.queue.task_done()
                # print ret
            else:
                AGENTLOG.info("agent.Worker.run - unknown task type, worker exit.")
                self.queue.task_done()
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
        AGENTLOG.info("agent.Server.callback - receive server to agent msg: %s" %(body))

        msg = json.loads(body)
        # {'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
        print "receive server to agent msg: monitor project %s."
        if msg['type'] == 'check':
            AGENTLOG.info("agent.Server.callback - project-%s - req_id-%s get a task type:check." 
                %(msg['project'], msg['req_id']))
            self.worker_poll.push_task(Task(msg))
        else:
            AGENTLOG.error("agent.Server.callback - receive server to agent msg: invalid msg type:%s." %(msg['type']))

        #print(" [x] %r:%s - %s" % (method.routing_key, msg['type'], msg['project']))

if __name__ == "__main__":
	#ser = Server()
	#ser.run()

    # msg = {"type": "Item", "req_id": "1", "project": "admin", "vm_info": "None", "network_info": "None"} 

    # wp = WorkerPoll()
    # wp.run()
    # wp.push_task(Task(msg))
    # wp.push_task(Task(msg))
    # wp.push_task(Task(msg))
    # print "down"
    # # wp.stop()
    # print "stop"


    wp = WorkerPoll()
    wp.run()
    
    server = Server(wp)
    #signal.signal(signal.SIGINT, sigint_callback)
    # signal.signal(signal.SIGTERM, sigint_callback)
    server.run()
