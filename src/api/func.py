#!/usr/bin/python2
import __init__
from comm.client import api_to_server_msg
from utils.conf import CONF
from openstack.auth import check_auth as os_check_auth
from comm.client import api_to_server_msg

def check_auth(msg):
	auth_url = CONF.openstack_conf['auth_url']
	return os_check_auth(auth_url, msg['token'], msg['project_name'])

def check_msg(msg):
	response = {
            'task_type': 'check',
            'exe_result': False,
            'req_id': msg['req_id'],
            'project': msg['project_name'],
            'result': None,
            'error_msg': None 
            }
	# check auth
	if check_auth(msg) == False:
		response['error_msg'] = 'no authorization'
		return response

	# database
	# 数据库查和创建任务

	# dispatch task to back end
	task = {'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
	ret = api_to_server_msg(task)
	if ret[0] == False:
		response['error_msg'] = ret[1]
	else:
		response['exe_result'] = True
		response['result'] = 'run check task'
	return response

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
