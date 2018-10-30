#!/usr/bin/python2
import __init__
from flask import Flask, request
from flask_restful import Resource, Api
#from start_re import start_re_rpc
#from end_re import end_re_rpc
import uuid
import time
from utils.log import APILOG
from utils.conf import CONF
from database.manager import Manager

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

class ResourceEvaluateStart(Resource):
    """
        evaluate the vm resource
    """

    def post(self, vm_id):
        # the vm resource get api, return evaluation results
        #print "get vm_id"
        req_id = str(uuid.uuid4())
        #try:
        data = request.get_json()       
        print data

        if data == None or "time_out" not in data:
            response = {
                            'exe_res': False,
                            'task_type': 're_start',        
                            'req_id': req_id,
                            'error_msg': "data format illegal"
                        }
            code = 400
            return response, code
            APILOG.info("api.ResourceEvaluationStart.post - req-%s request data format illegal" %(req_id))
        
        time_out = data['time_out']
        expire_second = 0
        if time_out:
            try:
                day = int(data['day'])
                hour = int(data['hour'])
                minute = int(data['minute'])
                second = int(data['second'])
            except Exception, e:
                return {"error": "data format illegal"}, 400
            expire_second = day * 24 * 3600 + hour * 3600 + minute * 60 + second

        print expire_second
        msg = {'req_id': req_id, 'vm_id': vm_id, 'time_out': time_out, 'expire_second': expire_second}

        APILOG.info("api.ResourceEvaluate.get - vm-%s - req-%s api get request:resource evaluate start" %(vm_id, req_id))
        
        # exception
        res, msg = start_re_rpc(msg)
        if res:
            if msg['exe_res'] == False:
                APILOG.info("api.ResourceEvaluate.get - vm-%s - req-%s RE start result:fail info:%s" %(vm_id, req_id, str(msg)))
                return msg, 400
            else:
                APILOG.info("api.ResourceEvaluate.get - vm-%s - req-%s RE start result:success info:%s" %(vm_id, req_id, str(msg)))
                return msg, 200
        else:
            response = {
                    'task_type': 'start_re',
                    'exe_res': False,
                    'req_id': req_id,
                    'vm_id': vm_id,
                    'error_msg': msg 
                    }
            return response, 400

class ResourceEvaluateEnd(Resource):
    def post(self, vm_id):
        # the vm resrource evalustion task post api
        #print "post vm_id" 
        req_id = str(uuid.uuid4())
        msg = {'req_id': req_id, 'vm_id': vm_id}

        APILOG.info("api.ResourceEvaluate.post - vm-%s - req-%s api get request:resource evaluate end" %(vm_id, req_id))
        
        # exception
        res, msg = end_re_rpc(msg)
        if res:
            if msg['exe_res'] == False:
                APILOG.info("api.ResourceEvaluate.post - vm-%s - req-%s RE end result:fail info:%s" %(vm_id, req_id, str(msg)))
                return msg, 400
            else:
                APILOG.info("api.ResourceEvaluate.post - vm-%s - req-%s RE end result:success info:%s" %(vm_id, req_id, str(msg)))
                return msg, 200
        else:
            response = {
                        'task_type': 'end_re',
                        'exe_res': False,
                        'req_id': req_id,
                        'vm_id': vm_id,
                        'error_msg': msg 
                        }
            return response, 400

class ResourceEvaluateResult(Resource):
    """
        evaluation result api
    """
    def get(self, vm_id):
        # write log
        req_id = str(uuid.uuid4())
        APILOG.info("api.EvaluateResult.get - vm-%s - req-%s api get request:get resource evaluation result" %(vm_id, req_id))

        # read result from database
        # exception
        db_manager = Manager()
        res, msg = db_manager.get_result(vm_id, req_id)

        if res:
            # true, success
            APILOG.info("api.EvaluateResult.get - vm-%s - req-%s get RE result:success info:%s" %(vm_id, req_id, str(msg)))
            response = {
                'task_type': 'get_re_result',
                'exe_res': True,
                'req_id': req_id,
                'vm_id': vm_id,
                'info': msg 
                        }
            return response, 200
        else:
            APILOG.info("api.EvaluateResult.get - vm-%s - req-%s get RE result:fail info:%s" %(vm_id, req_id, str(msg)))
            response = {
                'task_type': 'get_re_result',
                'exe_res': False,
                'req_id': req_id,
                'vm_id': vm_id,
                'error_msg': msg 
                        }
            return response, 400


class QueryStatus(Resource):

    def post(self):
        # write log
        req_id = str(uuid.uuid4())
        APILOG.info("api.QueryStatus.post - req-%s api post request:get vms status" %(req_id))

        vms = request.get_json()       

        if vms == None or "vm_ids" not in vms:
            response = {
                            'exe_res': False,
                            'task_type': 'query_status',        
                            'req_id': req_id,
                            'error_msg': "data format illegal"
                        }
            code = 400
            APILOG.info("api.QueryStatus.post - req-%s request data format illegal" %(req_id))
        else:
            
            # read result from database
            #res = []
            vm_ids = vms["vm_ids"]
            # n = len(vm_ids)
            db_manager = Manager()
            # rewrite query_status
            res, msg = db_manager.query_status(vm_ids, req_id)
            #for i in range(n):
            #    status = db_manager.query_status(vm_ids[i], req_id)
            #    res.append({"vm_id": vm_ids[i], "status": status})
            if res:
                APILOG.info("api.QueryStatus.post - req-%s status result success: %s " %(req_id, str(msg)))
                response = {
                                'exe_res': True,
                                'task_type': 'query_status',
                                'req_id': req_id,
                                'result': msg
                            }
                code = 200
            else:
                APILOG.info("api.QueryStatus.post - req-%s status result fail: %s " %(req_id, msg))
                response = {
                                'exe_res': False,
                                'task_type': 'query_status',
                                'req_id': req_id,
                                'error_msg': msg
                            }
                code = 400
                
        return response, code


class QueryHistory(Resource):
    # query vm history info
    def get(self, vm_id):
        # write log
        req_id = str(uuid.uuid4())
        APILOG.info("api.QueryHistory.get - vm-%s - req-%s api get request:get vms history" %(vm_id, req_id))       

        # exception
        db_manager = Manager()
        res, msg = db_manager.query_history(vm_id, req_id)
        if res:
            response = {
                            'exe_res': True,
                            'task_type': 'query_history',        
                            'req_id': req_id,
                            'vm_id': vm_id,
                            'info': msg
                        }
            APILOG.info("api.QueryHistory.get - vm-%s req-%s history:%d items" %(vm_id, req_id, msg['history_num']))
            code = 200
        else:
            response = {
                            'exe_res': False,
                            'task_type': 'query_history',        
                            'req_id': req_id,
                            'vm_id': vm_id,
                            'error_msg': msg
                        }
            APILOG.info("api.QueryHistory.get - vm-%s req-%s history:%d items" %(vm_id, req_id, msg['history_num']))
            code = 400
        return response, code


api.add_resource(HelloWorld, '/')
# api.add_resource(ResourceEvaluateStart, '/pre_online/resource_evaluate/start/<string:vm_id>')
# api.add_resource(ResourceEvaluateEnd, '/pre_online/resource_evaluate/end/<string:vm_id>')
# api.add_resource(ResourceEvaluateResult, '/pre_online/resource_evaluate/result/<string:vm_id>')
# api.add_resource(QueryStatus, '/pre_online/resource_evaluate/query_status')
# api.add_resource(QueryHistory, '/pre_online/resource_evaluate/history/<string:vm_id>')

if __name__ == '__main__':
	app.run(debug = True)