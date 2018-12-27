#!/usr/bin/python2
import logging
from logging.handlers import RotatingFileHandler
from conf import CONF

class Log(object):
    def __init__(self, log_name, log_file, max_size = 10, backup_num = 5):
        self.log_file = log_file
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = 0
        #handler = logging.FileHandler(self.log_file)
        #handler.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(log_file, maxBytes= max_size*1024*1024, backupCount = backup_num)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        #print "log_name" + log_name + "log_file" + log_file

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
# must be the global var, otherwise will occurr repeat logs
DBLOG = Log("db_log", CONF.log_conf['database_log'], CONF.log_conf['database_log_max_size'],
            CONF.log_conf['database_log_backup_num'])
SERVERLOG = Log("server_log", CONF.log_conf['server_log'], CONF.log_conf['server_log_max_size'],
            CONF.log_conf['server_log_backup_num'])
APILOG = Log("api_log", CONF.log_conf['api_log'], CONF.log_conf['api_log_max_size'],
            CONF.log_conf['api_log_max_size'])
AGENTLOG = Log("agent_log", CONF.log_conf['agent_log'], CONF.log_conf['agent_log_max_size'],
            CONF.log_conf['agent_log_max_size'])
FALOG = Log("fatal_log", CONF.log_conf['fatal_log'], CONF.log_conf['fatal_log_max_size'],
            CONF.log_conf['fatal_log_max_size'])
SELOG = Log("service_log", CONF.log_conf['service_log'], CONF.log_conf['service_log_max_size'],
            CONF.log_conf['service_log_max_size'])



if __name__ == "__main__":
    DBLOG.info("aaaa")
    FALOG.info("aaa")
    SELOG.info("bbb")
