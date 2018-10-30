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

    def exist_item(self, vm_id, req_id):
        conn = connection.Connection(conf_dict = self.db_conf)

        sql = "select 1 from vm where vm_id = '%s' limit 1;" %vm_id
        #sql = "select * from vm where vm_id = '%s';" %vm_id
        res = None
        try:
            conn.execute(sql)
            res = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.exist_item - vm-%s req-%s query item exist fail:%s" %(vm_id, req_id, str(e)))
            raise e
        result = None
        if res == None:
            result = False 
        else:
            result = True
        conn.close()

        # DBLOG.info("vm-" + vm_id + " " + "req-" + req_id + " " + "query item exist:" + str(result))
        DBLOG.info("database.exist_item - vm-%s req-%s query item exist:%s" %(vm_id, req_id, str(result)))
        return result

    def task_start(self, vm_id, req_id, start_time, expire_time):
        # str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        str_time = format_time(start_time)
        expire = format_time(expire_time)

        update_sql = ("update vm set start_time = '%s', end_time = NULL, status = 'running', vcpu = 0,"
                "cpu_rate = 0,recommend_vcpu = 0, expect_cpu_rate = 0, maxmem = 0, usedmem = 0,"
                "memory_rate = 0, actual = 0, used = 0, recommend_mem = 0, expect_mem_rate = 0,"
                "nic_num = 0, nic_info = '[]', expire_time = '%s'"
                " where vm_id = '%s';") %(str_time, expire, vm_id) 

        insert_sql = ("insert into vm set vm_id = '%s', start_time= '%s', end_time = NULL, status = 'running', vcpu = 0,"
                "cpu_rate = 0, recommend_vcpu = 0, expect_cpu_rate = 0, maxmem = 0, usedmem = 0, "
                "memory_rate = 0, actual = 0, used = 0, recommend_mem = 0, expect_mem_rate = 0,"
                "nic_num = 0, nic_info = '[]', expire_time = '%s';") %(vm_id, str_time, expire)

        # exception
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("database.task_start - vm-%s req-%s task_start fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
        try:
            if self.exist_item(vm_id, req_id):
                # update
                conn.execute(update_sql)
            else:
                # insert
                conn.execute(insert_sql)
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.error("database.task_start - vm-%s req-%s task_start fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
        else:
            conn.commit()
            conn.close()
            # DBLOG.info("vm-" + vm_id + " " + "req-" + req_id + " " + "task_start:" + str_time)
            DBLOG.info("database.task_start - vm-%s req-%s task_start:%s - %s" %(vm_id, req_id, str_time, expire))
            return True, None

    def task_stop(self, vm_id, req_id, end_time, info, auto_exit = False):
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
            
        str_time = format_time(end_time)

        sql = "select * from vm where vm_id = '%s';" %(vm_id)
        res = None
        try:
            conn.execute(sql)
            res = conn.fetchone()
        except MySQLdb.Error, e:
            conn.close()
            DBLOG.info("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)

        start_time = str(res[1])
        expire_time = str(res[17])
        #status = res[3]
        print start_time
        
        if auto_exit:
            status = 'auto_end'
        else:
            status = 'end'
        # start transaction
        try:
            conn.execute('begin;')
        
            sql = ("insert into history set vm_id = '%s', start_time = '%s', end_time = '%s', status = '%s', vcpu = %d,"
                    "cpu_rate = %f,recommend_vcpu = %d, expect_cpu_rate = %f, maxmem = %d, usedmem = %d, "
                    "memory_rate=%f, actual=%d, used=%d, recommend_mem = %d, expect_mem_rate = %f,"
                    "nic_num = %d, nic_info = '%s', expire_time = '%s';") %(vm_id, start_time, str_time, status, 
                    info['vcpu'], info['cpu_rate'], info['recommend_vcpu'], info['expect_cpu_rate'], info['maxmem'], 
                    info['usedmem'], info['memory_rate'], info['actual'], info['used'], info['recommend_mem'], 
                    info['expect_mem_rate'], info['nic_num'], info['nic_info'], expire_time)
            # print sql
            conn.execute(sql)

            sql = ("update vm set end_time = '%s', status = '%s', vcpu = %d,"
                    "cpu_rate = %f,recommend_vcpu = %d, expect_cpu_rate = %f, maxmem = %d, usedmem = %d, "
                    "memory_rate=%f, actual=%d, used=%d, recommend_mem = %d, expect_mem_rate = %f,"
                    "nic_num = %d, nic_info = '%s' where vm_id = '%s';") %(str_time, status, info['vcpu'], 
                    info['cpu_rate'], info['recommend_vcpu'], info['expect_cpu_rate'], info['maxmem'], 
                    info['usedmem'], info['memory_rate'], info['actual'], info['used'], info['recommend_mem'], 
                    info['expect_mem_rate'], info['nic_num'], info['nic_info'], vm_id)

            conn.execute(sql)
            conn.commit()
        except MySQLdb.Error, e:
            # auto rollback
            conn.close()
            DBLOG.error("database.task_end - vm-%s req-%s task_end fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)
        conn.close()

        DBLOG.info("database.task_end - vm-%s req-%s task_end:%s" %(vm_id, req_id, str_time))
        return True, None

    def get_result(self, vm_id, req_id):
        exist_flag = False
        try:
            exist_flag = self.exist_item(vm_id, req_id)
        except MySQLdb.Error, e:
            DBLOG.error("databtase.get_result - vm-%s req-%s get result fail:%s" %(vm_id, req_id, str(e)))
            return False, str(e)

        if exist_flag:
            conn = None
            try:
                conn = connection.Connection(conf_dict = self.db_conf)
            except MySQLdb.Error, e:
                DBLOG.error("databtase.get_result - vm-%s req-%s get result fail:%s" %(vm_id, req_id, str(e)))
                return False, str(e)

            sql = "select * from vm where vm_id = '%s';" %(vm_id)
            res = None
            try:
                conn.execute(sql)
                res = conn.fetchone()
            except MySQLdb.Error, e:
                DBLOG.error("databtase.get_result - vm-%s req-%s get result fail:%s" %(vm_id, req_id, str(e)))
                conn.close()
                return False, str(e)
            conn.close()
            # print res

            # vm item column index map
            item_index_map = {
                                'vm_id': 0,
                                'start_time': 1,
                                'end_time': 2,
                                'status': 3,
                                'vcpu': 4,
                                'cpu_rate': 5,
                                'recommend_vcpu': 6,
                                'expect_cpu_rate': 7,
                                'maxmem': 8,
                                'usedmem': 9,
                                'memory_rate': 10,
                                'actual': 11,
                                'used': 12,
                                'recommend_mem': 13,
                                'expect_mem_rate': 14,
                                'nic_num': 15,
                                'nic_info': 16,
                                'expire_time': 17
                            }
            
            if res[item_index_map['status']] == "running":
                DBLOG.info("databtase.get_result - vm-%s req-%s task is running and stop first." %(vm_id, req_id))
                left_date = res[item_index_map['expire_time']] - datetime.datetime.now()
                #res[item_index_map['start_time']]
                left_second = int(left_date.total_seconds())
                left_day = left_second / (24 * 60 * 60)
                left_second -= left_day * (24 * 60 * 60)
                left_hour = left_second / (60 * 60)
                left_second -= left_hour * (60 * 60)
                left_minute = left_second / 60
                left_second -= left_minute * 60
                 
                # print left_day, left_hour, left_minute, left_second

                left_time = "%02d:%02d:%02d:%02d" %(left_day, left_hour, left_minute, left_second)
                result = {
                            'start_time': str(res[item_index_map['start_time']]),
                            'status': res[item_index_map['status']],
                            'expire_time': str(res[item_index_map['expire_time']]),
                            'left_time': left_time
                            }
                return True, result
                # return False, "resource evaluation task is running, stop first."
            elif res[item_index_map['status']] == "end" or res[item_index_map['status']] == "auto_end":
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
                DBLOG.info("database.get_result - vm-%s req-%s get result success" %(vm_id, req_id))
                return True, result
        else:
            DBLOG.info("database.get_result - vm-%s req-%s not start task ever, return none" %(vm_id, req_id))
            return False, "Please start resource evaluation first."

    def is_auto_end(self, vm_id, req_id):
        result = False
        if self.exist_item(vm_id, req_id):
            conn = connection.Connection(conf_dict = self.db_conf)
             
            sql = "select status from vm where vm_id = '%s';" %(vm_id)
            conn.execute(sql)
            res = conn.fetchone()
            # print res[0]
            if res[0] == "running" or res[0] == 'end':
                DBLOG.info("databtase.auto_end - vm-%s req-%s task status is running and end, not end auto")
                result = False
            elif res[0] == "auto_end":
                DBLOG.info("databtase.auto_end - vm-%s req-%s task status is auto_end, end auto")

                # update RE task status:auto_end->end
                sql = "update vm set status = 'end' where vm_id = '%s';" %(vm_id)
                conn.execute(sql)
                # write log
                DBLOG.info("databtase.auto_end - vm-%s req-%s task status change, auto_end->end")
                result = True
            conn.commit()
            conn.close()
        else:
            DBLOG.info("database.auto_end - vm-%s req-%s no vm resource evaluation task,not end auto")
            result = False
        return result
    
    def query_status(self, vm_ids, req_id):
        status = []
        conn = None
        try:
            conn = connection.Connection(conf_dict = self.db_conf)
        except MySQLdb.Error, e:
            DBLOG.error("databtase.quety_status - req-%s query_status fail: %s" %(req_id, str(e)))
            return False, str(e)
        
        for vm_id in vm_ids:
            # query vm status for each vm_id
            result = None
            sql = "select status from vm where vm_id = '%s';" %(vm_id)
            res = None
            try:
                conn.execute(sql)
                res = conn.fetchone()
            except MySQLdb.Error, e:
                conn.close()
                DBLOG.error("databtase.quety_status - vm-%s req-%s query_status fail: %s" %(vm_id, req_id, str(e)))
                return False, str(e)
            if res != None:
                if res[0] == "running" or res[0] == "end" or res[0] == "auto_end":
                    DBLOG.info("databtase.quety_status - vm-%s req-%s status: %s" %(vm_id, req_id, res[0]))
                    result = res[0]
                else:
                    DBLOG.error("databtase.quety_status - vm-%s req-%s unkown status: %s" %(vm_id, req_id, res[0]))
                    result = "unkown"
            else:
                DBLOG.info("database.query_status - vm-%s req-%s status: not evaluate")
                result = "not_evaluate"
            status.append({'vm_id': vm_id, 'status': result})
        conn.close()
        return True, status
    
    def query_history(self, vm_id, req_id):
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
