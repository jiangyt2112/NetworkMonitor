#!/usr/bin/python2
import __init__
import connection
from utils.conf import CONF
import sys
from utils.log  import DBLOG
from utils.log  import SELOG
from utils.ftime import format_time
import time
import json
import datetime
import MySQLdb

class Manager(object):
    def __init__(self, conf = CONF):
        """
        conf:the conf object that have database connection params
        """
        self.db_conf = CONF.db_conf

    def any_operation(self):
        conn = connection.Connection(conf_dict = self.db_conf)
        sql = "show tables;"
        conn.execute(sql)
        #res = conn.fetchone()
        #print res
        # remember the ";"!!!!
        res = conn.fetchall()
        print res
        conn.commit()
        conn.close()

    def exist_item(self, project_name, req_id):
        conn = connection.Connection(conf_dict = self.db_conf)

        sql = "select 1 from task where project = '%s' limit 1;" %project_name

        ret = None
        try:
            conn.execute(sql)
            ret = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.exist_item - project-%s req-%s query item exist fail:%s" %(project_name, req_id, str(e)))
            raise e

        result = None
        if ret == None:
            result = False 
        else:
            result = True
        conn.close()

        DBLOG.info("database.exist_item - project-%s req-%s query item exist:%s" %(project_name, req_id, str(result)))
        return result


    def create_task(self, project_name, req_id):
        receive_time = format_time(time.time())

        update_sql = ("update task set req_id = '%s', status = 'RECEIVED', receive_time = '%s',"
                "start_time = NULL, stop_time = NULL, network_info = NULL, vm_info = NULL, vm_num = NULL,"
                "receive_vm_num = 0, network_num = NULL, receive_network_num = 0, result = NULL"
                " where project = '%s';") %(req_id, receive_time, project_name) 

        insert_sql = ("insert into task set project = '%s', req_id = '%s', status = 'RECEIVED',"
                "receive_time= '%s', start_time = NULL, stop_time = NULL, network_info = NULL,"
                "vm_info = NULL, vm_num = NULL, receive_vm_num = 0, network_num = NULL, receive_network_num = 0,"
                "result = NULL;") %(project_name, req_id, receive_time)

        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("database.create_task - project-%s req-%s task_start fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        try:
            if self.exist_item(project_name, req_id):
                # update
                ret, status = self.get_status(project_name, req_id)
                if ret == False:
                    conn.close()
                    DBLOG.error("database.create_task - project-%s req-%s create start fail:%s" %(project_name, req_id, status))
                    return False, status
                else:
                    if status != "END" and status != "EXPIRED":
                        conn.close()
                        DBLOG.error("database.create_task - project-%s req-%s create start fail:\
                            the project status is %s" %(project_name, req_id, status))
                        return False, "task create fail, the project task is running."
                conn.execute(update_sql)
            else:
                # insert
                conn.execute(insert_sql)
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.create_task - project-%s req-%s create task fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        else:
            conn.commit()
            conn.close()
            # DBLOG.info("vm-" + vm_id + " " + "req-" + req_id + " " + "task_start:" + str_time)
            DBLOG.info("database.create_task - project-%s req-%s create task:%s" %(project_name, req_id, receive_time))
            return True, None


    def get_status(self, project_name, req_id):
        status = None
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("databtase.get_status - project-%s req-%s get status fail: %s" %(project_name, req_id, str(e)))
            return False, str(e)
        
        # query task status for project
        sql = "select status from task where project = '%s';" %(project_name)
        ret = None
        try:
            conn.execute(sql)
            ret = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("databtase.get_status - project-%s req-%s get status fail: %s" %(project_name, req_id, str(e)))
            return False, str(e)
        conn.close()

        state = False
        if ret != None:
            if ret[0] == "RECEIVED" or ret[0] == "START" or ret[0] == "RUNNING" or ret[0] == "END" or ret[0] == "EXPIRED":
                DBLOG.info("databtase.get_status - project-%s req-%s status: %s" %(project_name, req_id, ret[0]))
                state = True
                result = ret[0]
            else:
                DBLOG.error("databtase.get_status - project-%s req-%s unkown status: %s" %(project_name, req_id, ret[0]))
                result = "unkown status:" + ret[0]
        else:
            DBLOG.info("database.get_status - project--%s req-%s status: there is no the task" %(project_name, req_id))
            result = "no task"
        return state, result

    def get_result(self, project_name, req_id):
        ret, status = self.get_status(project_name, req_id)
        if ret == False:
            DBLOG.error("databtase.get_result - project-%s req-%s get result fail:%s" %(project_name, req_id, status))
            return ret, status

        if status != "END" and status != "EXPIRED":
            DBLOG.error("databtase.get_result - project-%s req-%s get result fail:task not end(%s)" %(project_name, req_id, status))
            return False, "task not end:" + status
        
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("databtase.get_result - project-%s req-%s get status fail: %s" %(project_name, req_id, str(e)))
            return False, str(e)
        
        # query task status for project
        sql = "select result from task where project = '%s';" %(project_name)
        ret = None
        try:
            conn.execute(sql)
            ret = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("databtase.get_result - project-%s req-%s get result fail: %s" %(project_name, req_id, str(e)))
            return False, str(e)
        conn.close()

        DBLOG.info("database.get_result - vm-%s req-%s result:%s" %(project_name, req_id, ret[0]))
        return True, ret[0]

    def get_history(self, project_name, req_id):
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("database.get_history - project-%s req-%s get result fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
             
        sql = "select * from history where project = '%s' order by id desc;" %(project_name)
        try:
            conn.execute(sql)
            all_res = conn.fetchall()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.get_history - project-%s req-%s get result fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        conn.close()

        history_num = len(all_res)
        # vm item column index map
        history_index_map = {
                            'id': 0,
                            'project': 1,
                            'req_id': 2,
                            'status': 3,
                            'receive_time': 4,
                            'start_time': 5,
                            'stop_time': 6,
                            'network_info': 7,
                            'vm_info': 8,
                            'result': 9
                            }
        history_result = {
                            'history_num': history_num,
                            'history_info': []
        }
        
        for i in range(history_num):
            res = all_res[i]
            result = {"index": i, "result": res[history_index_map['result']]}
            history_result['history_info'].append(result)
        DBLOG.info("database.get_history - project-%s req-%s get result success:%d items"
                %(project_name, req_id, history_result['history_num']))
        return True, history_result

    def start_task(self, project_name, req_id, start_time, network_info, vm_info, network_num, vm_num):
        # start_time = format_time(time.time())
        update_sql = ("update task set status = 'START', start_time = '%s',"
                "network_info = '%s', vm_info = '%s', vm_num = %d, network_num = %d "
                "where project = '%s';") %(start_time, network_info, vm_info, network_num, vm_num, project_name)

        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
            conn.execute(update_sql)
            conn.commit()
            conn.close()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.start_task - project-%s req-%s start task fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        else:
            DBLOG.info("database.start_task - project-%s req-%s start task:%s" %(project_name, req_id, start_time))
            return True, None

    def receive_item(self, project_name, req_id, receive_vm_num, receive_network_num, info):
        receive_time = format_time(time.time())
        get_id_sql = ("select id from task where project = '%s';") %(project_name)
        
        conn = None
        task_id = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
            conn.execute(get_id_sql)
            ret = conn.fetchone()
            task_id = ret[0]
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.receive_item - project-%s req-%s receive item fail, "
                "can't get task id:%s" %(project_name, req_id, str(e)))
            return False, str(e)

        set_task_sql = ("update task set status = 'RUNNING', "
                "receive_vm_num = %d, receive_network_num = %d "
                "where project = '%s';") %(receive_vm_num, receive_network_num, project_name)
        store_item_sql = ("insert into item set task_id = %d, receive_time = '%s', "
            "info = '%s';") %(task_id, receive_time, info)

        try:
            conn.execute(set_task_sql)
            conn.execute(store_item_sql)
            conn.commit()
            conn.close()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.receive_item - project-%s req-%s receive item fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        else:
            DBLOG.error("database.receive_item - project-%s req-%s receive item:%s" %(project_name, req_id, receive_time))
            return True, None
        
    def stop_task(self, project_name, req_id, status, result):
        stop_time = format_time(time.time())
        get_task_sql = ("select * from task where project = '%s';") %(project_name)
        
        conn = None
        task_info = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
            conn.execute(get_task_sql)
            task_info = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.stop_task - project-%s req-%s stop task fail, "
                "can't get task info:%s" %(project_name, req_id, str(e)))
            return False, str(e)

        task_index_map = {
                    'id': 0,
                    'project': 1,
                    'req_id': 2,
                    'status': 3,
                    'receive_time': 4,
                    'start_time': 5,
                    'stop_time': 6,
                    'network_info': 7,
                    'vm_info': 8,
                    'vm_num': 9,
                    'receive_vm_num': 10,
                    'network_num': 11,
                    'receive_network_num': 12,
                    'result': 13
                    }

        set_task_sql = ("update task set status = '%s', stop_time = '%s', result = '%s' "
                "where project = '%s';") %(status, stop_time, result, project_name)

        store_history_sql = ("insert into history set project = '%s', req_id = '%s', status = '%s',"
                            "receive_time = '%s', start_time = '%s', stop_time = '%s', network_info = '%s',"
                            "vm_info = '%s', result = '%s';") %(task_info[task_index_map['project']],
                            task_info[task_index_map['req_id']], status, task_info[task_index_map['receive_time']],
                            task_info[task_index_map['start_time']], stop_time, task_info[task_index_map['network_info']],
                            task_info[task_index_map['vm_info']], result)
        
        delete_item_sql = ("delete from item where task_id = %d;" %(task_info[task_index_map['id']]))

        try:
            conn.execute(set_task_sql)
            conn.execute(store_history_sql)
            conn.execute(delete_item_sql)
            conn.commit()
            conn.close()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.stop_task - project-%s req-%s stop task fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        else:
            DBLOG.error("database.stop_task - project-%s req-%s stop task item:%s" %(project_name, req_id, stop_time))
            return True, None

    def get_items(self, project_name, req_id):
        task_id_sql = ("select id from task where project = '%s';") %(project_name)
        
        conn = None
        task_id = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
            conn.execute(task_id_sql)
            ret = conn.fetchone()
            task_id = ret[0]
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.get_items - project-%s req-%s get items fail, "
                "can't get task id:%s" %(project_name, req_id, str(e)))
            return False, str(e)

        get_items_sql = ("select * from item where task_id = %d;") %(task_id)

        try:
            conn.execute(get_items_sql)
            ret = conn.fetchall()
            conn.commit()
            conn.close()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.get_items - project-%s req-%s get items fail:%s" %(project_name, req_id, str(e)))
            return False, str(e)
        else:
            # process data
            item_num = len(ret)
            item_index_map = {
                        'id': 0,
                        'task_id': 1,
                        'receive_time': 2,
                        'info': 3
            }
            result = {
                    'item_num': item_num,
                    'item_info': []
            }
            for item in ret:
                result['item_info'].append(item[item_index_map['info']])
            DBLOG.error("database.get_items - project-%s req-%s get items:%d" %(project_name, req_id, item_num))
            return True, result

    def api_check(self):
        SELOG.info("[database] check [start]")
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
            conn.close()
        except MySQLdb.Error, e:
            print "database error:%s" %(str(e))
            SELOG.error("database connection fail:%s" %(str(e)))
            SELOG.info("[database] check [end]")
            sys.exit(1)
        SELOG.info("[database] check [end]")

    def start_check(self):
        # check the database consistence when service start
        # the task status must be end or auto_end, change running to stop
        SELOG.info("[database] check [start]")
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            print "database error:%s" %(str(e))
            SELOG.error("database connection fail:%s" %(str(e)))
            SELOG.info("[database] check [end]")
            sys.exit(1)

        SELOG.info("database connection success")
        
        sql = "select count(*) from task where status = 'RUNNING' or status = 'START' or status = 'RECEIVED';"
        n = 0
        try:
            conn.execute(sql)
            # res = conn.fetchone()
            n = conn.fetchone()[0]
            # print res
        except MySQLdb.Error, e:
            conn.close()
            print "database error:%s" %(str(e))
            SELOG.error("database qeury task fail:%s" %(str(e)))
            SELOG.info("[database] check [end]")
            sys.exit(1)
        
        if n == 0:
            SELOG.info("database items consistence")
        else:
            SELOG.info("database items inconsistence:%d items" %(n))
            sql = "update task set status = 'ERROR' where status = 'RUNNING' or status = 'START' or status = 'RECEIVED';"
            try:
                conn.execute(sql)
                conn.commit()
                conn.close()
            except MySQLdb.Error, e:
                conn.close()
                SELOG.error("database update task status fail:%s" %(str(e)))
                SELOG.info("[database] check [end]")
                print "database error:%s" %(str(e))
                sys.exit(1)
        SELOG.info("[database] check [end]")

if __name__ == "__main__":
    manager = Manager()
    manager.any_operation()
    print manager.exist_item("admin", "1")
    print manager.create_task("root", "2")
    #print manager.get_status("root", "2")
    #print manager.get_result("root", "2")

    #print manager.get_history("root", "2")
    #print manager.start_task("root", "2", "2018-10-09 16:43:00", "none", "none", 0, 0)

    print manager.receive_item("root", "2", 2, 3, "info")
    #print manager.stop_task("root", "2", "END", "result")

    print manager.get_items("root", "2")




