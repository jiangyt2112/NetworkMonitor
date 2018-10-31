#!/usr/bin/python2
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')
channel.queue_declare(queue='hello1')
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
def callback1(ch, method, properties, body):
    print(" [x1] Received %r" %body)

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)
channel.basic_consume(callback1,
                      queue='hello1',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
