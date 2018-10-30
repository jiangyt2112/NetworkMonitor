#!/usr/bin/python2
import time

def format_time(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

if __name__ == "__main__":
    print format_time(time.time())