#!/usr/bin/python2
import __init__
import MySQLdb

class Connection(object):
    def __init__(self, host = "localhost", port = 3306, user = "network_monitor", 
                passwd = "111111", db = "network_monitor", charset = "utf8", conf_dict = None):
        if conf_dict == None:
            self.host = host
            self.port = port
            self.user = user
            self.passwd = passwd
            self.db = db
            self.charset = charset
        else:
            self.host = conf_dict['host']
            self.port = conf_dict['port']
            self.user = conf_dict['user']
            self.passwd = conf_dict['passwd']
            self.db = conf_dict['db']
            self.charset = conf_dict['charset']

        self.conn = MySQLdb.connect(host = self.host, port = self.port, user = self.user, passwd = self.passwd,
                                db = self.db, charset = self.charset)

    def execute(self, sql):
        self.cursor = self.conn.cursor()
        self.cursor.execute(sql)

    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close() 

if __name__ == "__main__":
    conf_dict = {
        'host' : "10.10.150.28",
        'user' : "network_monitor",
        'port' : 3306,
        'passwd' : "111111",
        'db' : "network_monitor",
        'charset' : "utf8"
    }
    conn = Connection(conf_dict = conf_dict)
    conn.connect()
    conn.close()