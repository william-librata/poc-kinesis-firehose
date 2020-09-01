#!../venv/bin/python

import boto3
import json

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener


def setup_pubnub(subscriber_key):
    # setup config
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = subscriber_key
    pnconfig.ssl = False
    return PubNub(pnconfig)


def setup_listener(pubnub, channel_name):
    listener = SubscribeListener()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels(channel_name).execute()
    listener.wait_for_connect()
    return listener


def unsubscribe(pubnub, listener, channel_name):
    # unsubscribe
    pubnub.unsubscribe().channels(channel_name).execute()
    listener.wait_for_disconnect()
    print('unsubscribed')


def upload_data(channel_name, subscriber_key, stream_name, data_limit=10):
    # setup data source
    pubnub = setup_pubnub(subscriber_key)
    listener = setup_listener(pubnub, channel_name)

    # setup counter
    counter = 1

    # setup boto
    client = boto3.client('firehose')

    # loop
    while(counter < data_limit):
        # send to kinesis stream
        data = listener.wait_for_message_on(channel_name).message
        print(data)

        record = {
            'Data': json.dumps(data)
        }
        response = client.put_record(
            DeliveryStreamName=stream_name,
            Record=record
        )
        print(response)
        counter += 1

    unsubscribe(pubnub, listener, channel_name)


def upload_data_batch(channel_name, subscriber_key, stream_name, batch_size=10, data_limit=10):
    # setup data source
    pubnub = setup_pubnub(subscriber_key)
    listener = setup_listener(pubnub, channel_name)

    # setup counter
    counter = 1

    # setup boto
    client = boto3.client('firehose')

    # set records to be list
    records = []

    # loop
    while(counter <= data_limit+1):

        # send to kinesis stream
        # check if the records is at batch size
        if len(records) == batch_size:
            response = client.put_record_batch(
                DeliveryStreamName=stream_name,
                Records=records,
            )
            print(response)
            # once uploaded, clear records list
            records = []

        record = {
                    'Data': json.dumps(listener.wait_for_message_on(channel_name).message)
                 }
        # add record to the list
        records.append(record)
        counter += 1

    unsubscribe(pubnub, listener, channel_name)


if __name__ == '__main__':

    # setup parameter
    channel_name = 'pubnub-sensor-network'
    subscriber_key = 'sub-c-5f1b7c8e-fbee-11e3-aa40-02ee2ddab7fe'
    stream_name = 'sensor-network-stream'
    partition_key = 'HADES-SensorNetworkData'
    data_limit = 2000
    batch_size = 10

    # upload data one at a time
    upload_data(channel_name, subscriber_key, stream_name, data_limit)

    # upload data in batch
    #upload_data_batch(channel_name, subscriber_key, stream_name, batch_size, data_limit)
