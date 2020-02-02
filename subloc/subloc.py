#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import StreamHandler
import urllib.request, json, os, sys
import paho.mqtt.client as mqtt


# setup logger
logger = logging.getLogger()
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s %(funcName)s(%(lineno)d) : %(message)s'
)
handler = TimedRotatingFileHandler(
    filename="log/subloc.log",
    when="D",
    interval=1,
    backupCount=7,
)
#handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# argparse
parser = argparse.ArgumentParser(description='')
parser.add_argument('--mqtt_host', help='')
parser.add_argument('--mqtt_port', type=int, help='')
parser.add_argument('--mqtt_ca_certs', help='')
parser.add_argument('--mqtt_token', help='')
parser.add_argument('--mqtt_topic', help='')
parser.add_argument('--ss_url', help='')
parser.add_argument('--ss_key', help='')
parser.add_argument('--ss_statusId', help='')
args = parser.parse_args()

logging.info('args.mqtt_host     : {}'.format(args.mqtt_host))
logging.info('args.mqtt_port     : {}'.format(args.mqtt_port))
logging.info('args.mqtt_ca_certs : {}'.format(args.mqtt_ca_certs))
logging.info('args.mqtt_token    : {}'.format(args.mqtt_token))
logging.info('args.mqtt_topic    : {}'.format(args.mqtt_topic))
logging.info('args.ss_url        : {}'.format(args.ss_url))
logging.info('args.ss_key        : {}'.format(args.ss_key))
logging.info('args.ss_statusId   : {}'.format(args.ss_statusId))


# on_connect triggered by MQTT client
def on_connect(client, userdata, flags, respons_code):
    logger.info('MQTT status: {0}'.format(respons_code))
    client.subscribe(args.mqtt_topic)
    logger.info('MQTT subscribed: {}'.format(args.mqtt_topic))


# on_message triggered by MQTT client
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode("utf-8"))
    logger.info('MQTT recieved payload: {}'.format(payload))
    postStatus(json.dumps(payload))


# send IFTTT webhook event
def postStatus(status):
    url = args.ss_url
    key = args.ss_key
    statusId = args.ss_statusId

    data = {
        "statusId" : statusId,
        "status" : status
    }
    json_data = json.dumps(data).encode("utf-8")

    method = "POST"
    headers = {"Content-Type" : "application/json", "x-api-key" : key}
    request = urllib.request.Request(url, data=json_data, method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
        logger.info('StatusStore response: {}'.format(response_body))


if __name__ == '__main__':

    # setup MQTT client
    client = mqtt.Client(
        client_id='subloc',
        clean_session=True,
        protocol=mqtt.MQTTv311
    )
    client.username_pw_set('token:{}'.format(args.mqtt_token))
    client.tls_set(args.mqtt_ca_certs)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.mqtt_host, port=args.mqtt_port, keepalive=60)
    client.loop_forever()
