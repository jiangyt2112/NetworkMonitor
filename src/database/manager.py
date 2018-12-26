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
                ret, status = self.get_status(project_name, req_id):
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
            if res[0] == "RECEIVED" or res[0] == "START" or res[0] == "RUNNING" or res[0] == "END" or res[0] == "EXPIRED":
                DBLOG.info("databtase.get_status - project-%s req-%s status: %s" %(project_name, req_id, res[0]))
                state = True
                result = res[0]
            else:
                DBLOG.error("databtase.get_status - project-%s req-%s unkown status: %s" %(project_name, req_id, res[0]))
                result = "unkown status:" + res[0]
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
# here
    def get_history(self, project_name, req_id):
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("database.query_history - vm-%s req-%s get result fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
             
        sql = "select * from history where vm_id = '%s' order by history_id desc;" %(vm_id)
        try:
            conn.execute(sql)
            # res = conn.fetchone()
            all_res = conn.fetchall()
            # print res
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.query_history - vm-%s req-%s get result fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
        # time.sleep(20)
        conn.close()

        history_num = len(all_res)
        # vm item column index map
        item_index_map = {
                            'vm_id': 1,
                            'start_time': 2,
                            'end_time': 3,
                            'status': 4,
                            'vcpu': 5,
                            'cpu_rate': 6,
                            'recommend_vcpu': 7,
                            'expect_cpu_rate': 8,
                            'maxmem': 9,
                            'usedmem': 10,
                            'memory_rate': 11,
                            'actual': 12,
                            'used': 13,
                            'recommend_mem': 14,
                            'expect_mem_rate': 15,
                            'nic_num': 16,
                            'nic_info': 17,
                            'expire_time': 18
                            }
        history_result = {
                            'history_num': history_num,
                            'history_info': []
        }
        
        for i in range(history_num):
            res = all_res[i]
            result = {
                        # 'vm_id': res[item_index_map['vm_id']],
                        'start_time': str(res[item_index_map['start_time']]),
                        'end_time': str(res[item_index_map['end_time']]),
                        'status': res[item_index_map['status']],
                        'vcpu': res[item_index_map['vcpu']],
                        'cpu_rate': '{:g}%'.format(res[item_index_map['cpu_rate']]*100),
                        'recommend_vcpu': res[item_index_map['recommend_vcpu']],
                        'expect_cpu_rate': '{:g}%'.format(res[item_index_map['expect_cpu_rate']]*100),
                        'maxmem': res[item_index_map['maxmem']],
                        'usedmem': res[item_index_map['usedmem']],
                        'memory_rate': '{:g}%'.format(res[item_index_map['memory_rate']] * 100),
                        'actual': res[item_index_map['actual']],
                        'used': res[item_index_map['used']],
                        'recommend_mem': res[item_index_map['recommend_mem']],
                        'expect_mem_rate': '{:g}%'.format(res[item_index_map['expect_mem_rate']] * 100),
                        'nic_num': res[item_index_map['nic_num']],
                        'nic_info': json.loads(res[item_index_map['nic_info']]),
                        'expire_time': str(res[item_index_map['expire_time']])
                    }
            history_result['history_info'].append(result)
        DBLOG.info("database.query_history - vm-%s req-%s get result success:%d items"
                %(vm_id, req_id, history_result['history_num']))
        return True, history_result

    def start_task(self):
        pass

    def stop_task(self):
        pass

    # def task_stop(self, vm_id, req_id, end_time, info, auto_exit = False):
    #     conn = None
    #     try:
    #         conn = connection.Connection(conf_dict = self.db_conf)
    #     except MySQLdb.Error, e:
    #         DBLOG.error("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
    #         return False, str(e)
            
    #     str_time = format_time(end_time)

    #     sql = "select * from vm where vm_id = '%s';" %(vm_id)
    #     res = None
    #     try:
    #         conn.execute(sql)
    #         res = conn.fetchone()
    #     except MySQLdb.Error, e:
    #         conn.close()
    #         DBLOG.info("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
    #         return False, str(e)

    #     start_time = str(res[1])
    #     expire_time = str(res[17])
    #     #status = res[3]
    #     print start_time
        
    #     if auto_exit:
    #         status = 'auto_end'
    #     else:
    #         status = 'end'
    #     # start transaction
    #     try:
    #         conn.execute('begin;')
        
    #         sql = ("insert into history set vm_id = '%s', start_time = '%s', end_time = '%s', status = '%s', vcpu = %d,"
    #                 "cpu_rate = %f,recommend_vcpu = %d, expect_cpu_rate = %f, maxmem = %d, usedmem = %d, "
    #                 "memory_rate=%f, actual=%d, used=%d, recommend_mem = %d, expect_mem_rate = %f,"
    #                 "nic_num = %d, nic_info = '%s', expire_time = '%s';") %(vm_id, start_time, str_time, status, 
    #                 info['vcpu'], info['cpu_rate'], info['recommend_vcpu'], info['expect_cpu_rate'], info['maxmem'], 
    #                 info['usedmem'], info['memory_rate'], info['actual'], info['used'], info['recommend_mem'], 
    #                 info['expect_mem_rate'], info['nic_num'], info['nic_info'], expire_time)
    #         # print sql
    #         conn.execute(sql)

    #         sql = ("update vm set end_time = '%s', status = '%s', vcpu = %d,"
    #                 "cpu_rate = %f,recommend_vcpu = %d, expect_cpu_rate = %f, maxmem = %d, usedmem = %d, "
    #                 "memory_rate=%f, actual=%d, used=%d, recommend_mem = %d, expect_mem_rate = %f,"
    #                 "nic_num = %d, nic_info = '%s' where vm_id = '%s';") %(str_time, status, info['vcpu'], 
    #                 info['cpu_rate'], info['recommend_vcpu'], info['expect_cpu_rate'], info['maxmem'], 
    #                 info['usedmem'], info['memory_rate'], info['actual'], info['used'], info['recommend_mem'], 
    #                 info['expect_mem_rate'], info['nic_num'], info['nic_info'], vm_id)

    #         conn.execute(sql)
    #         conn.commit()
    #     except MySQLdb.Error, e:
    #         # auto rollback
    #         conn.close()
    #         DBLOG.error("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
    #         return False, str(e)
    #     conn.close()

    #     DBLOG.info("database.task_end - vm-%s req-%s task_end:%s" %(vm_id, req_id, str_time))
    #     return True, None


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
        
        sql = "select count(*) from vm where status = 'running';"
        n = 0
        try:
            conn.execute(sql)
            # res = conn.fetchone()
            n = conn.fetchone()[0]
            # print res
        except MySQLdb.Error, e:
            conn.close()
            print "database error:%s" %(str(e))
            SELOG.error("database qeury vm fail:%s" %(str(e)))
            SELOG.info("[database] check [end]")
            sys.exit(1)
        
        if n == 0:
            SELOG.info("database items consistence")
        else:
            SELOG.info("database items inconsistence:%d items" %(n))
            sql = "update vm set status = 'end' where status = 'running';"
            try:
                conn.execute(sql)
                conn.commit()
                conn.close()
            except MySQLdb.Error, e:
                conn.close()
                SELOG.error("database update vm status fail:%s" %(str(e)))
                SELOG.info("[database] check [end]")
                print "database error:%s" %(str(e))
                sys.exit(1)
        SELOG.info("[database] check [end]")

if __name__ == "__main__":
    manager = Manager()
    manager.any_operation()
    # print manager.exist_item("1", "1")
    # manager.exist_item("3", "1")
    # print manager.task_start("2", "1", time.time(), time.time() + 10)
    # manager.task_start("3", "1", time.time())
    # manager.task_start("4", "1", time.time())
    # info = {
    #        'vcpu': 4,
    #        'cpu_rate': 20.9,
    #        'recommend_vcpu': 3,
    #        'expect_cpu_rate': 1.0,
    #        'maxmem': 65536
    #        'usedmem': 65536,
    #        'memory_rate': 1.0,
    #        'actual': 65536,
    #        'used':65536,
    #        'recommend_mem': 2048,
    #        'expect_mem_rate': 0.5,
    #        'nic_num': 2,
    #        'nic_info': json.dumps([{"mac":"123"},{'mac':"234"}])
    #        }

    # print manager.task_stop("2", "1", time.time(), info)
    
    # print manager.is_auto_exit("1", "1")
    # print manager.is_auto_exit("1", "1")
    # print manager.is_auto_exit("5", "1")

    # print manager.get_result("2", "1")
    # print manager.get_result("4", "1")
    # print manager.get_result("5", "1")
    
    # print manager.is_auto_end("1", "1")
    # print manager.is_auto_end("2", "1")
    # print manager.is_auto_end("5", "1")
    # print manager.query_status("1", "1")
    # print manager.query_history("1", "1")
    # manager.start_check()
