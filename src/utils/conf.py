#!/usr/bin/python2
from ConfigParser import ConfigParser
import os, sys
from os.path import dirname

class Conf(object):
    def __init__(self):
        self.conf_file_dir = dirname(dirname(os.path.split(os.path.realpath(__file__))[0]))
        self.conf_file_dir = os.path.join(self.conf_file_dir, "config/")
        # print self.conf_file_dir
        # self.conf_file = os.path.join(conf_file_dir, "etc/pre_online.conf")
        
        self.cf = ConfigParser()
        self.db_parse()
        self.server_parse()
        self.log_parse()
        self.api_parse()
        self.agent_parse()
        self.rabbitmq_parse()
        self.openstack_parse()
    
    def db_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "mysql.conf"))
        section = "mysql"
        self.host = self.cf.get(section, 'host')
        self.port = int(self.cf.get(section, 'port'))
        self.user = self.cf.get(section, 'user')
        self.passwd = self.cf.get(section, 'passwd')
        self.db = self.cf.get(section, 'db')
        self.charset = self.cf.get(section, 'charset')
        self.db_conf = {
                            "host": self.host,
                            "port": self.port,
                            "user": self.user,
                            "passwd": self.passwd,
                            "db": self.db,
                            "charset": self.charset,
                        }
    
    def server_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "server.conf"))
        section = "server"
        # self.max_days = int(self.cf.get(section, 'max_days'))
        self.worker_num = int(self.cf.get(section, 'worker_num'))
        self.max_task_time = int(self.cf.get(section, 'max_task_time'))

        self.server_conf = {
						      "worker_num": self.worker_num,
                              "max_task_time": self.max_task_time
						}
        
    def log_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "log.conf"))
        base_file_dir = dirname(dirname(os.path.split(os.path.realpath(__file__))[0]))
        base_file_dir = os.path.join(base_file_dir, "log/")
        section = "log"
        self.database_log = os.path.join(base_file_dir,self.cf.get(section, 'database_log'))
        self.database_log_max_size = int(self.cf.get(section, 'database_log_max_size'))
        self.database_log_backup_num = int(self.cf.get(section, 'database_log_backup_num'))
        self.api_log = os.path.join(base_file_dir, self.cf.get(section, 'api_log'))
        self.api_log_max_size = int(self.cf.get(section, 'api_log_max_size'))
        self.api_log_backup_num = int(self.cf.get(section, 'api_log_backup_num'))
        self.server_log = os.path.join(base_file_dir, self.cf.get(section, 'server_log'))
        self.server_log_max_size = int(self.cf.get(section, 'server_log_max_size'))
        self.server_log_backup_num = int(self.cf.get(section, 'server_log_backup_num'))
        self.agent_log = os.path.join(base_file_dir, self.cf.get(section, 'agent_log'))
        self.agent_log_max_size = int(self.cf.get(section, 'agent_log_max_size'))
        self.agent_log_backup_num = int(self.cf.get(section, 'agent_log_backup_num'))
        self.fatal_log = os.path.join(base_file_dir, self.cf.get(section, 'fatal_log'))
        self.fatal_log_max_size = int(self.cf.get(section, 'fatal_log_max_size'))
        self.fatal_log_backup_num = int(self.cf.get(section, 'fatal_log_backup_num'))
        self.service_log = os.path.join(base_file_dir, self.cf.get(section, 'service_log'))
        self.service_log_max_size = int(self.cf.get(section, 'service_log_max_size'))
        self.service_log_backup_num = int(self.cf.get(section, 'service_log_backup_num'))
        self.log_conf = {
                            "database_log": self.database_log,
                            "database_log_max_size": self.database_log_max_size,
                            "database_log_backup_num": self.database_log_backup_num,
                            "api_log": self.api_log,
                            "api_log_max_size": self.api_log_max_size,
                            "api_log_backup_num": self.api_log_backup_num,
                            "server_log": self.server_log,
                            "server_log_max_size": self.server_log_max_size,
                            "server_log_backup_num": self.server_log_backup_num,
                            "agent_log": self.agent_log,
                            "agent_log_max_size": self.agent_log_max_size,
                            "agent_log_backup_num": self.agent_log_backup_num,
                            "fatal_log": self.fatal_log,
                            "fatal_log_max_size": self.fatal_log_max_size,
                            "fatal_log_backup_num": self.fatal_log_backup_num,
                            "service_log": self.service_log,
                            "service_log_max_size": self.service_log_max_size,
                            "service_log_backup_num": self.service_log_backup_num
                        }

    def api_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "api.conf"))
        section = "api"
        self.api_port = int(self.cf.get(section, 'port'))
        self.api_conf = {
                            "port": self.api_port
                        }

    def agent_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "agent.conf"))
        section = 'agent'
        self.worker_num = int(self.cf.get(section, 'worker_num'))
       
        self.agent_conf = {
                                "worker_num": self.worker_num
                                # "username": self.zabbix_username,
                                # "password": self.zabbix_password,
                                # "jsonrpc": self.zabbix_jsonrpc,
                                # "key": self.zabbix_key
                               # "frequency_secs": self.zabbix_frequency_secs
                            }

    def rabbitmq_parse(self):
    	self.cf.read(os.path.join(self.conf_file_dir, "rabbitmq.conf"))
        section = 'rabbitmq'
        self.rabbitmq_username = self.cf.get(section, 'username')
        self.rabbitmq_passwd = self.cf.get(section, 'passwd')
        self.rabbitmq_host = self.cf.get(section, 'host')
        self.rabbitmq_vhost = self.cf.get(section, 'vhost')
        self.rabbitmq_port = int(self.cf.get(section, 'port'))
        self.rabbitmq_conf = {
                                "username": self.rabbitmq_username,
                                "passwd": self.rabbitmq_passwd,
                                "vhost" : self.rabbitmq_vhost,
                                "host": self.rabbitmq_host,
                                "port": self.rabbitmq_port
                            }

    def openstack_parse(self):
        self.cf.read(os.path.join(self.conf_file_dir, "openstack.conf"))
        section = 'keystone'
        self.openstack_auth_url = self.cf.get(section, 'auth_url')
        self.openstack_endpoint = self.cf.get(section, 'endpoint')
        self.openstack_endpoint_url = self.cf.get(section, 'endpoint_url')
        self.openstack_conf = {
                                "auth_url": self.openstack_auth_url,
                                "endpoint": self.openstack_endpoint,
                                "endpoint_url": self.openstack_endpoint_url
                            }

CONF = Conf()

if __name__ == "__main__":
    print CONF.db_conf
    print CONF.log_conf
    print CONF.server_conf
    print CONF.api_conf
    print CONF.agent_conf
    print CONF.rabbitmq_conf
    print CONF.openstack_conf

