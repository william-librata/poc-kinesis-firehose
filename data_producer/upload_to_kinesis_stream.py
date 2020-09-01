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


def upload_data(channel_name, subscriber_key, stream_name, partition_key, data_limit=10):
    # setup data source
    pubnub = setup_pubnub(subscriber_key)
    listener = setup_listener(pubnub, channel_name)

    # setup counter
    counter = 1

    # setup boto
    client = boto3.client('kinesis')

    # loop
    while(counter < data_limit):
        # send to kinesis stream
        data = listener.wait_for_message_on(channel_name).message
        print(data)
        response = client.put_record(
            StreamName=stream_name,
            Data=json.dumps(data),
            PartitionKey=partition_key,
        )
        print(response)
        counter += 1

    unsubscribe(pubnub, listener, channel_name)


def upload_data_batch(channel_name, subscriber_key, stream_name, partition_key, batch_size=10, data_limit=10):
    # setup data source
    pubnub = setup_pubnub(subscriber_key)
    listener = setup_listener(pubnub, channel_name)

    # setup counter
    counter = 1

    # setup boto
    client = boto3.client('kinesis')

    # set records to be list
    records = []

    # loop
    while(counter <= data_limit+1):

        # send to kinesis stream
        # check if the records is at batch size
        if len(records) == batch_size:
            response = client.put_records(
                Records=records,
                StreamName=stream_name
            )
            print(response)
            # once uploaded, clear records list
            records = []

        record = {
                    'Data': json.dumps(listener.wait_for_message_on(channel_name).message),
                    'PartitionKey': partition_key
                 }
        # add record to the list
        records.append(record)
        counter += 1

    unsubscribe(pubnub, listener, channel_name)


if __name__ == '__main__':

    # setup parameter
    channel_name = 'pubnub-sensor-network'
    subscriber_key = 'sub-c-5f1b7c8e-fbee-11e3-aa40-02ee2ddab7fe'
    stream_name = 'DataStream'
    partition_key = 'HADES-SensorNetworkData'
    data_limit = 20
    batch_size = 10

    # upload data one at a time
    #upload_data(channel_name, subscriber_key, stream_name, partition_key, data_limit)

    # upload data in batch
    upload_data_batch(channel_name, subscriber_key, stream_name, partition_key, batch_size, data_limit)
