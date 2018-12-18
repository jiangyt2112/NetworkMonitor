#!/usr/bin/python2
import __init__
from comm.client import api_to_server_msg

def check_auth(project_name, token):
	pass


def check_msg(msg):
	# 授权
	# 数据库
	# 通信
    # response = {
    #         'task_type': 'start_re',
    #         'exe_result': False,
    #         'req_id': req_id,
    #         'vm_id': vm_id,
    #         'error_msg': msg 
    #         }
	pass

def get_status(msg):
	# 授权
	# 数据库
	# response = {
    #             'task_type': 'end_re',
    #             'exe_result': False,
    #             'req_id': req_id,
    #             'vm_id': vm_id,
    #             'error_msg': msg 
    #             }
	pass

def get_result(msg):
	db_manager = Manager()
    res, msg = db_manager.get_result(project_name, req_id)
    # response = {
    #             'task_type': 'get_result',
    #             'exe_result': True,
    #             'req_id': req_id,
    #             'project_name': project_name,
    #             'result': msg 
    #                     }
	pass

def get_history(msg):
	db_manager = Manager()
    res, msg = db_manager.query_history(vm_id, req_id)
    # response = {
    #                         'exe_res': False,
    #                         'task_type': 'query_history',        
    #                         'req_id': req_id,
    #                         'project_name': project_name,
    #                         'error_msg': msg
    #                     }
	pass
