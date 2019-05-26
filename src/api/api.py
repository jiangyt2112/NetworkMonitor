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
from func import get_result
from func import get_history
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
        token = request.args.get("token")
        project = request.args.get("project")
        print token
        print project
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
        data = request.get_json()       
        #print data

        if data == None or "token" not in data:
            response = {
                            'exe_result': False,
                            'task_type': 'check',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "data format illegal"
                        }
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400
            
        
        msg = {'req_id': req_id, 'project_name': project_name, 'token': data['token']}

        print "api.NetworkMonitorCheck.post - req-%s - project-%s api get request:check project start" %(req_id, project_name)
        APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s api get request:check project start" %(req_id, project_name))
        
        # exception
        response = check_msg(msg)
        print "send task msg: %s" %(msg)

        if response['exe_result'] == False:
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s check project:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400
        else:
            print "api.NetworkMonitorCheck.post - req-%s - project-%s check project:success info:%s" %(req_id, project_name, response['result'])
            APILOG.info("api.NetworkMonitorCheck.post - req-%s - project-%s check project:success info:%s" %(req_id, project_name, response['result']))
            return response, 200

class NetworkMonitorStatus(Resource):
    def post(self, project_name):
        # the vm resrource evalustion task post api
        #print "post vm_id" 
        req_id = str(uuid.uuid4())
        data = request.get_json()

        if data == None or "token" not in data:
            response = {
                            'exe_result': False,
                            'task_type': 'get_status',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "data format illegal"
                        }
            APILOG.info("api.NetworkMonitorStatus.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400
        
        msg = {'req_id': req_id, 'project_name': project_name, 'token': data['token']}

        APILOG.info("api.NetworkMonitorStatus.post - req-%s - project_name-%s api get request: get task status" %(req_id, project_name))
        
        # exception
        response = get_status(msg)

        if response['exe_result'] == False:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400
        else:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:success info:%s" %(req_id, project_name, response['result']))
            return response, 200

    def get(self, project_name):
        # the vm resrource evalustion task post api
        #print "post vm_id" 
        token = request.args.get("token")
        #project_name = request.args.get("project")
        req_id = str(uuid.uuid4())

        if token == None or project_name == None:
            response = {
                            'exe_result': False,
                            'task_type': 'get_status',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "url format illegal"
                        }
            APILOG.info("api.NetworkMonitorStatus.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400
        
        msg = {'req_id': req_id, 'project_name': project_name, 'token': token}

        APILOG.info("api.NetworkMonitorStatus.post - req-%s - project_name-%s api get request: get task status" %(req_id, project_name))
        
        # exception
        response = get_status(msg)

        if response['exe_result'] == False:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400
        else:
            APILOG.info("api.ResourceEvaluate.post - req-%s - project_name-%s get status:success info:%s" %(req_id, project_name, response['result']))
            return response, 200
        
class NetworkMonitorResult(Resource):
    """
        result api
    """
    def post(self, project_name):
        # write log
        req_id = str(uuid.uuid4())
        data = request.get_json()

        if data == None or "token" not in data:
            response = {
                            'exe_result': False,
                            'task_type': 'get_result',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "data format illegal"
                        }
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400

        msg = {"project_name": project_name, "req_id": req_id, "token": data["token"]}

        APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s api post request:get result" %(req_id, project_name))

        response = get_result(msg)
        
        if response['exe_result']:
            # true, success
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:success info:%s" %(req_id, project_name, response['result']))
            return response, 200
        else:
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400

    def get(self, project_name):
        # write log
        req_id = str(uuid.uuid4())
        token = request.args.get("token")
        #project_name = request.args.get("project")

        if token == None or project_name == None:
            response = {
                            'exe_result': False,
                            'task_type': 'get_result',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "url format illegal"
                        }
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400

        msg = {"project_name": project_name, "req_id": req_id, "token": token}

        APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s api get request:get result" %(req_id, project_name))

        response = get_result(msg)
        
        if response['exe_result']:
            # true, success
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:success info:%s" %(req_id, project_name, response['result']))
            return response, 200
        else:
            APILOG.info("api.NetworkMonitorResult.post - req-%s - project-%s get result:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400


class NetworkMonitorHistory(Resource):
    # query vm history info
    def post(self, project_name):
        # write log
        req_id = str(uuid.uuid4())
        data = request.get_json()

        if data == None or "token" not in data:
            response = {
                            'exe_result': False,
                            'task_type': 'get_history',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "data format illegal"
                        }
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400

        msg = {"project_name": project_name, "req_id": req_id, "token": data["token"]}

        APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s api post request:get history" %(req_id, project_name))       

        # exception
        response = get_history(msg)
        
        if response['exe_result']:
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s get history:success info:%s" %(req_id, project_name, response['result']))
            return response, 200
        else:
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s get history:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400

    def get(self, project_name):
        # write log
        req_id = str(uuid.uuid4())
        token = request.args.get("token")
        #project_name = request.args.get("project")


        if token == None or project_name == None:
            response = {
                            'exe_result': False,
                            'task_type': 'get_history',        
                            'req_id': req_id,
                            'project_name': project_name,
                            'error_msg': "url format illegal"
                        }
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s request data format illegal" %(req_id, project_name))
            return response, 400

        msg = {"project_name": project_name, "req_id": req_id, "token": token}

        APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s api get request:get history" %(req_id, project_name))       

        # exception
        response = get_history(msg)
        
        if response['exe_result']:
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s get history:success info:%s" %(req_id, project_name, response['result']))
            return response, 200
        else:
            APILOG.info("api.NetworkMonitorHistory.post - req-%s - project-%s get history:fail info:%s" %(req_id, project_name, response['error_msg']))
            return response, 400

api.add_resource(HelloWorld, '/')
api.add_resource(NetworkMonitorCheck, '/network_monitor/check/<string:project_name>')
api.add_resource(NetworkMonitorStatus, '/network_monitor/status/<string:project_name>')
api.add_resource(NetworkMonitorResult, '/network_monitor/result/<string:project_name>')
api.add_resource(NetworkMonitorHistory, '/network_monitor/history/<string:project_name>')

if __name__ == '__main__':
	app.run(debug = True)