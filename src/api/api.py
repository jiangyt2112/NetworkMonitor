#!/usr/bin/python2
import __init__
from flask import Flask, request
from flask_restful import Resource, Api
import uuid
import time
from utils.log import APILOG
from utils.conf import CONF
from database.manager import Manager
from func import check_msg
from func import get_status
from func import check_auth

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    """
        test flask, hello world :)
    """
    def get(self):
        print "path:" + request.path
        print "method:" + request.method
        print "host:" + request.host
        print "remote_addr:" + request.remote_addr
        # print "headers:" + str(request.headers)#.__dict__
        # print "values:" + request.values.get()
        # print request.__dict__
        return {'hello': 'world'}
    
    def post(self):
        return {'hello': 'world'}

class NetworkMonitorCheck(Resource):
    """
        network monitor task start
    """
    def post(self, project_name):
        # the 
        #print "get vm_id"
        req_id = str(uuid.uuid4())
        #try:
        data = request.get_json()       
        print data

        if data == None or "token" not in data:
            response = {
                            'exe_result': False,
                            'task_type': 'check',        
                            'req_id': req_id,
                            'error_msg': "data format illegal"
                        }
            code = 400
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, code
            
        
        msg = {'req_id': req_id, 'project_name': project_name, 'token': data['token']}

        APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s api get request:check project start" %(req_id, project_name))
        
        # exception
        response = check_msg(msg)
        
        if response['exe_result'] == False:
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s check project:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400
        else:
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project_name-%s check project:success info:%s" %(req_id, project_name, response['error_msg']))
            return response, 200

class NetworkMonitorStatus(Resource):
    def post(self, project_name):
        # the vm resrource evalustion task post api
        #print "post vm_id" 
        req_id = str(uuid.uuid4())
        data = request.get_json()
        msg = {'req_id': req_id, 'vm_id': project_name, 'token': data['token']}

        APILOG.info("api.NetworkMonitorStatus.post - req-%s - project_name-%s api get request: get task status" %(req_id, project_name))
        
        # exception
        response = get_status(msg)

        if response['exe_result'] == False:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400
        else:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:success info:%s" %(req_id, project_name, response['error_msg']))
            return response, 200
        
class NetworkMonitorResult(Resource):
    """
        evaluation result api
    """
    def post(self, project_name):
        # write log
        req_id = str(uuid.uuid4())
        APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s api get request:get resource evaluation result" %(req_id, project_name))

        # read result from database
        # exception
        # 检查授权

        db_manager = Manager()
        res, msg = db_manager.get_result(project_name, req_id)

        if res:
            # true, success
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:success info:%s" %(req_id, project_name, str(msg)))
            response = {
                'task_type': 'get_result',
                'exe_res': True,
                'req_id': req_id,
                'project_name': project_name,
                'info': msg 
                        }
            return response, 200
        else:
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:fail info:%s" %(req_id, project_name, str(msg)))
            response = {
                'task_type': 'get_result',
                'exe_res': False,
                'req_id': req_id,
                'project_name': project_name,
                'error_msg': msg 
                        }
            return response, 400


class NetworkMonitorHistory(Resource):
    # query vm history info
    def post(self, vm_id):
        # write log
        req_id = str(uuid.uuid4())
        APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s api get request:get history" %(req_id, project_name))       

        # exception
        db_manager = Manager()
        res, msg = db_manager.query_history(vm_id, req_id)
        if res:
            response = {
                            'exe_res': True,
                            'task_type': 'query_history',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'info': msg
                        }
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s history:%d items" %(req_id, project_name, msg['history_num']))
            code = 200
        else:
            response = {
                            'exe_res': False,
                            'task_type': 'query_history',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': msg
                        }
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s history:%d items" %(req_id, project_name, msg['history_num']))
            code = 400
        return response, code


# api.add_resource(HelloWorld, '/')
api.add_resource(NetworkMonitorCheck, '/network_monitor/ckeck/<string:project_name>')
api.add_resource(NetworkMonitorStatus, '/network_monitor/status/<string:project_name>')
api.add_resource(NetworkMonitorResult, '/network_monitor/result/<string:project_name>')
api.add_resource(NetworkMonitorHistory, '/network_monitor/history/<string:project_name>')

if __name__ == '__main__':
	app.run(debug = True)