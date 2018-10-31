#!/usr/bin/python2
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')
channel.queue_declare(queue='hello1')
channel.basic_publish(exchange='',
                      routing_key='hello',
                      body='Hello World!')
channel.basic_publish(exchange='',
                      routing_key='hello1',
                      body='Hello World1!')
print(" [x] Sent 'Hello World!'")
connection.close()
