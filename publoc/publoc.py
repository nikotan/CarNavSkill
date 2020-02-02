#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import StreamHandler
import time, json
import paho.mqtt.client as mqtt
from gps3 import gps3


# setup logger
logger = logging.getLogger()
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s %(funcName)s(%(lineno)d) : %(message)s'
)
handler = TimedRotatingFileHandler(
    filename="log/publoc.log",
    when="D",
    interval=1,
    backupCount=7,
)
#handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    # argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--host', help='')
    parser.add_argument('--port', type=int, help='')
    parser.add_argument('--ca_certs', help='')
    parser.add_argument('--token', help='')
    parser.add_argument('--topic', help='')
    parser.add_argument('--interval', type=int, default=10, help='')
    args = parser.parse_args()

    logging.info('args.host     : {}'.format(args.host))
    logging.info('args.port     : {}'.format(args.port))
    logging.info('args.ca_certs : {}'.format(args.ca_certs))
    logging.info('args.token    : {}'.format(args.token))
    logging.info('args.topic    : {}'.format(args.topic))
    logging.info('args.interval : {}'.format(args.interval))


    # setup MQTT client
    client = mqtt.Client(
        client_id='publoc',
        clean_session=True,
        protocol=mqtt.MQTTv311
    )
    client.username_pw_set('token:{}'.format(args.token))
    client.tls_set(args.ca_certs)
    client.connect(args.host, port=args.port, keepalive=60)

    # setup GPS
    gps_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()

    # read GPS
    ut = 0
    cnt = 0
    sum_lat = 0.
    sum_lon = 0.
    for new_data in gps_socket:
        if new_data:
            data_stream.unpack(new_data)
            lat = data_stream.TPV['lat']
            lon = data_stream.TPV['lon']
            if lat != 'n/a' and lon != 'n/a':
                sum_lat += lat
                sum_lon += lon
                cnt += 1
                now = int(time.time())
                if now - ut > args.interval and cnt > 0:
                    # publish
                    lat = sum_lat / cnt
                    lon = sum_lon / cnt
                    message = "{{\"latitude\":{:.6f},\"longitude\":{:.6f}}}".format(lat, lon)
                    logging.info('send message = {}'.format(message))
                    ret = client.publish(args.topic, message)
                    logging.info('return value = {}'.format(ret))

                    ut = now
                    cnt = 0
                    sum_lat = 0.
                    sum_lon = 0.
