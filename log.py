#!/usr/bin/env python
import pika
import datetime


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct', exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='direct', queue=queue_name,routing_key="#")

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    # routing_key, message, date
    print(f" {datetime.datetime.now().strftime('%H:%M:%S')} channel : {method.routing_key} {body.decode()}")
    with open("logs.txt", "a") as file:
        file.write(f"{datetime.datetime.now().strftime('%H:%M:%S')} channel : {method.routing_key} {body.decode()}\n")

channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()