#!/usr/bin/python2
import __init__
from comm.client import api_to_server_msg
from utils.conf import CONF
from openstack import auth
from auth import check_auth as os_check_auth
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

    # call database api to create a check task entry
    db_manager = Manager()
    ret, result = db_manager.create_task(msg['project_name'], msg['req_id'])

    if ret == False:
        response['error_msg'] = result
        return response

    # dispatch task to back end
    task = {'type': 'check', 'req_id': msg['req_id'], 'project': msg['project_name'], 'token': msg['token']}
    ret, result = api_to_server_msg(task)
    if ret == False:
        response['error_msg'] = result
    else:
        response['exe_result'] = True
        response['result'] = 'run check task'

    return response

def get_status(msg):
    response = {
            'task_type': 'get_status',
            'exe_result': False,
            'req_id': msg['req_id'],
            'project': msg['project_name'],
            'result': None,
            'error_msg': None 
            }
    # check authority
    if check_auth(msg) == False:
        response['error_msg'] = 'no authorization'
        return response

    # call database api to obtain check task status
    db_manager = Manager()
    ret, result = db_manager.get_status(msg['project_name'], msg['req_id'])
    if ret == False:
        response['error_msg'] = result
    else:
        response['exe_result'] = True
        response['result'] = result

    return response

def get_result(msg):
    response = {
            'task_type': 'get_result',
            'exe_result': False,
            'req_id': msg['req_id'],
            'project': msg['project_name'],
            'result': None,
            'error_msg': None 
            }
    # check authority
    if check_auth(msg) == False:
        response['error_msg'] = 'no authorization'
        return response

    db_manager = Manager()
    ret, result = db_manager.get_result(msg['project_name'], msg['req_id'])
    if ret == False:
        response['error_msg'] = result
    else:
        response['exe_result'] = True
        response['result'] = result

    return response

def get_history(msg):
    response = {
            'task_type': 'get_history',
            'exe_result': False,
            'req_id': msg['req_id'],
            'project': msg['project_name'],
            'result': None,
            'error_msg': None 
            }
    # check authority
    if check_auth(msg) == False:
        response['error_msg'] = 'no authorization'
        return response

    # call database api to obtain project check task history
    db_manager = Manager()
    ret, result = db_manager.get_history(msg['project_name'], msg['req_id'])
    if ret == False:
        response['error_msg'] = result
    else:
        response['exe_result'] = True
        response['result'] = result

    return response
