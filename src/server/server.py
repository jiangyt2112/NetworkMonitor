#!/usr/bin/python2
import __init__
from comm.server import Server as Base_Server
import pika
from utils.log import SELOG, SERVERLOG
from utils.conf import CONF
from utils.ftime import format_time
from database.manager import Manager
import json
import time
import threading 
from Queue import Queue as Q
from comm.client import server_to_agent_msg
from openstackapi.nova import get_project_server_info
from openstackapi.neutron import get_project_network_info
from func import check_delay
from func import evaluate_performace

class Task:
    def __init__(self, msg):
        #{'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
        self.type = msg['type']
        self.req_id = msg['req_id']
        self.project = msg['project']
        self.token = msg['token']
        self.item_flag = False
        self.get_info_from_openstack()
        self.status = None
        self.start_time = None
        self.receive_time = None
        self.stop_time = None
        self.max_task_time = CONF.server_conf['max_task_time']

    def get_info_from_openstack(self):
        self.network_info = None
        self.vm_info = None
        self.vm_num = 0
        self.receive_vm_num = 0
        self.network_num = 0
        self.receive_network_num = 0
        self.result = None
        # to do
        auth_url = CONF.openstack_conf["auth_url"]
        endpoint_url = CONF.openstack_conf["endpoint_url"]
        self.vm_info = get_project_server_info(self.token, auth_url, self.project)
        self.vm_num = len(self.vm_info)

        self.network_info = get_project_network_info(self.token, auth_url, endpoint_url)
        self.network_num = self.vm_num + 1
    
    def is_down(self):
        if self.vm_num == self.receive_vm_num and self.network_num == self.receive_network_num:
            return True
        elif time.time() - self.start_time > self.max_task_time:
            return True
        return False 

    def start_task(self):
        manager = Manager()
        self.start_time = time.time()
        self.status = "START"

        # send to agent
        msg = {
                'type': 'check', 
                'project': self.project, 
                'req_id': self.req_id, 
                'vm_info': self.vm_info,
                'network_info': self.network_info
            }
        ret, msg = server_to_agent_msg(msg)
        if ret == False:
            self.status = "ERROR"
            SERVERLOG.error("server.Task.start_task - project-%s - req_id-%s server_to_agent_msg return error:%s" 
                %(self.project, self.req_id, msg))
            return False

        #def start_task(self, project_name, req_id, start_time, network_info, vm_info, network_num, vm_num):
        ret, msg = manager.start_task(self.project, self.req_id, format_time(self.start_time), json.dumps(self.network_info), 
            json.dumps(self.vm_info), self.network_num, self.vm_num)
        if ret == False:
            self.status = "ERROR"
            SERVERLOG.error("server.Task.start_task - project-%s - req_id-%s manager.start_task return error:%s" 
                %(self.project, self.req_id, msg))
            return False
        else:
            SERVERLOG.info("server.Task.start_task - project-%s - req_id-%s task start success." %(self.project, self.req_id))
            return True

    def receive_item(self, item):
        manager = Manager()
        if self.item_flag == False:
            self.receive_time = time.time()
            self.item_flag = True
        #def receive_item(self, project_name, req_id, receive_vm_num, receive_network_num, info):
        item = self.process_item(item)
        print "item len: %s" %(len(item))
        ret, msg = manager.receive_item(self.project, self.req_id, self.receive_vm_num, self.receive_network_num, item)
        if ret == False:
            SERVERLOG.error("server.Task.receive_item - project-%s - req_id-%s manager.receive_item return error:%s" 
                %(self.project, self.req_id, msg))
            self.status = "ERROR"
            return False

        SERVERLOG.info("server.Task.receive_item - project-%s - req_id-%s receive item success." 
                %(self.project, self.req_id))
        return True

    def stop_task(self, status = "END"):
        manager = Manager()
        self.stop_time = time.time()
        self.status = status
        # def get_items(self, project_name, req_id):
        # def stop_task(self, project_name, req_id, status, result):
        ret, items = manager.get_items(self.project, self.req_id)

        # item_info struct
        # item_index_map = {
        #     'id': 0,
        #     'task_id': 1,
        #     'receive_time': 2,
        #     'info': 3
        # }
        # items struct
        # result = { 
        #         'item_num': item_num,
        #         'item_info': []
        # }

        if ret == False:
            self.status = "ERROR"
            SERVERLOG.error("server.Task.stop_task - project-%s - req_id-%s manager.get_items return error:%s" 
                %(self.project, self.req_id, items))
            return False
        SERVERLOG.info("server.Task.stop_task - project-%s - req_id-%s manager.get_items success:%d items" 
                %(self.project, self.req_id, items['item_num']))

        self.result = self.process_items(items)

        ret, msg = manager.stop_task(self.project, self.req_id, self.status, self.result)
        if ret == False:
            self.status = "ERROR"
            SERVERLOG.error("server.Task.stop_task - project-%s - req_id-%s manager.stop_task return error:%s" 
                %(self.project, self.req_id, msg))
            return False
        SERVERLOG.info("server.Task.stop_task - project-%s - req_id-%s task stop success." 
                %(self.project, self.req_id))
        return True

    def stop_task_expire(self):
        return self.stop_task("EXPIRED")

    def process_items(self, items):
        # process items into result
        # to do
        # items struct
        # { 
        #     'item_num': item_num,
        #     'item_info': [info]
        # }
        # info struct
        # {
        #     "vm_num": 0,
        #     "host": "ip_addr",
        #     "is_network_node": False,
        #     "topo": "topo_struct"
        # }
        result = {
            "project": self.project,
            "req_id": self.req_id,
            "item_num": items["item_num"],
            "info": None
        }
        info = []
        for i in items["item_info"]:
            info.append(json.loads(i))
        result["info"] = info
        check_delay(result)
        evaluate_performace(result)
        return json.dumps(result)

    def process_item(self, item):
        # process item to update receive_vm_num receive_network_num
        # to do
        SERVERLOG.info("server.Task.process_item - project-%s - req_id-%s process received item." 
                %(self.project, self.req_id))
        info = item.info
        # info struct
        # {
        #     "vm_num": 0,
        #     "host": "ip_addr",
        #     "is_network_node": False,
        #     "topo": "topo_struct"
        # }
        self.receive_vm_num += info["vm_num"]
        if info["node_type"] == "network":
            self.receive_network_num += info["vm_num"] + 1
        else:
            self.receive_network_num += info["vm_num"]
        return json.dumps(info)

class Tasks:
    def __init__(self):
        self.num = 0
        self.tasks = {} # project_name: task
        self.mutex = threading.Lock()
        self.run_flag = True

    def append(self, task):
        self.mutex.acquire()
        if task.project in self.tasks:
            SERVERLOG.error("server.Tasks.append - project-%s - req_id-%s task already in tasks." %(task.project, task.req_id))
        else:
            SERVERLOG.info("server.Tasks.append - project-%s - req_id-%s task append tasks." %(task.project, task.req_id))
            self.tasks[task.project] = task
            self.num += 1
        self.mutex.release()

    def update_task(self, item):
        self.mutex.acquire()
        print item.project
        print self.tasks
        if item.project not in self.tasks:
            SERVERLOG.error("server.Tasks.update_task - project-%s - req_id-%s task not in tasks." %(item.project, item.req_id))
        else:
            SERVERLOG.info("server.Tasks.update_task - project-%s - req_id-%s update task success." %(item.project, item.req_id))
            self.tasks[item.project].receive_item(item)
            if self.tasks[item.project].is_down() == True:
                self.tasks[item.project].stop_task()
                del self.tasks[item.project]
                self.num -= 1
        self.mutex.release()

    def task_expire(self):
        while self.run_flag:
            self.mutex.acquire()
            del_key = []
            for key in tasks:
                if tasks[key].is_down() == True:
                    tasks[key].stop_task_expire()
                    del_key.append(key)
            for key in del_key:
                del tasks[key]
                num -= 1
            self.mutex.release()
            time.sleep(1)

    def start_expire_check(self):
        t = threading.Thread(target = Tasks.task_expire, args=(self,))
        t.setDaemon(True)
        t.start()

    def stop_expire_check(self):
        self.run_flag = False

class Item:
    def __init__(self, msg):
        #{'type': 'item', 'req_id': msg['req_id'], 'project': msg['project_name'], 'info': msg['info']}
        self.type = msg['type']
        self.req_id = msg['req_id']
        self.project = msg['project']
        self.info = msg['info']

    def to_json(self):
        return {
            'type': self.type,
            'req_id': self.req_id,
            'project': self.project,
            'info': self.info
        }

class Worker(threading.Thread):
    def __init__(self, queue, tasks):
        threading.Thread.__init__(self)
        self.queue = queue
        self.tasks = tasks

    def run(self):
        print "worker is running"
        while True:
            task = self.queue.get()
            if isinstance(task, Task):
                SERVERLOG.info("server.Worker.run - project-%s - req_id-%s get a task type:%s." %(task.project, task.req_id, "Task"))
                ret = task.start_task()
                if ret:
                    self.tasks.append(task)
                    self.queue.task_done()
                else:
                    pass
            elif isinstance(task, Item):
                SERVERLOG.info("server.Worker.run - project-%s - req_id-%s get a task type:%s." %(task.project, task.req_id, "Item"))
                self.tasks.update_task(task)
                self.queue.task_done()
            elif isinstance(task, int) and task == 1:
                SERVERLOG.info("server.Worker.run worker exit.")
                self.queue.task_done()
                break
            else:
                SERVERLOG.error("server.Worker.run - unkown task type:%s." %(str(type(task))))
                break

    def stop(self):
        self.queue.put(1)

class WorkerPoll:
    def __init__(self):
        self.queue = Q()
        self.worker_num = CONF.server_conf['worker_num']
        self.worker_list = []
        self.tasks = Tasks()
        self.worker_poll_flag = True
        for i in range(self.worker_num):
            self.worker_list.append(Worker(self.queue, self.tasks))

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
    def __init__(self, worker_poll, exchange = "server", binding_keys = ["api_to_server.*", "agent_to_server.*"], 
                exchange_type = "topic"):
        rabbit_conf = CONF.rabbitmq_conf
        self.worker_poll = worker_poll
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
                    self.worker_poll.push_task(Task(msg))
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
                if msg['type'] == 'item':
                    self.worker_poll.push_task(Item(msg))
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
	#ser = Server()
	#ser.run()
    # msg_task = {'type': 'check', 'req_id': "1", 'project': "admin", 'token': "123456"}
    # msg_item = {'type': 'item', 'req_id': "1", 'project': "admin", 'info': "info"}
    # wp = WorkerPoll()
    # wp.run()
    # wp.push_task(Task(msg_task))
    # time.sleep(1)
    # wp.push_task(Item(msg_item))
    # wp.stop()


    wp = WorkerPoll()
    wp.run()
    server = Server(wp)
    server.run()