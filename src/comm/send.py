#!/usr/bin/python2
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('10.10.150.28'))
channel = connection.channel()