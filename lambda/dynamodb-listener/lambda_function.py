import boto3
import sys, traceback
import uuid
import os
import simplejson
from decimal import *
from fssi_common import *

## more info -- https://stackoverflow.com/a/46738251/846340
def unmarshallAwsDataItem(awsDict):
    boto3.resource('dynamodb')
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    pyDict = {k: deserializer.deserialize(v) for k,v in awsDict.items()}
    return pyDict

def lambda_handler(event, context):
    print('EVENT', event)
    try:
        for record in event['Records']:
            eventName = record['eventName']
            sourceArn = record['eventSourceARN']
            tableName = sourceArn.split('/')[1]
            itemData = None
            if eventName == 'INSERT' or eventName == 'MODIFY':
                itemData = unmarshallAwsDataItem(record['dynamodb']['NewImage'])
            if eventName == 'REMOVE':
                itemData = unmarshallAwsDataItem(record['dynamodb']['OldImage'])

            # sanity checks
            if not itemData:
                raise ValueError('unsupported stream event type {} table {}'.format(eventName, tableName))
            if not 'id' in itemData:
                raise ValueError('couldn\'t find "id" field in table {}: '
                        'table must provide "id" for items'.format(tableName))

            objectUrl = 'https://'+itemData['bucket']+'.s3.amazonaws.com/'+itemData['id']
            snsMessageBody = { 'table': tableName, 'event':eventName,
                'itemId': itemData['id'], 'objectUrl': objectUrl, 'itemData': itemData }
            print('will publish SNS message {}'.format(simplejson.dumps(snsMessageBody)))

            mySnsClient = boto3.client('sns')
            response = mySnsClient.publish(TopicArn=getSnsTopicByName(FssiResources.Sns.DynamodbUpdates),
                Message=simplejson.dumps(snsMessageBody))
            if response and type(response) == dict and 'MessageId' in response:
                return processedReply()
            else:
                return lambdaReply(420, "unable to send SNS message")
    except:
        err = reportError()
        return lambdaReply(420, err)

    return lambdaReply(420, "undefined")

# for testing locally
if __name__ == '__main__':
    sampleEvent = {'Records': [{'eventID': '511159a4d0156bf36339813ba3846e58', 'eventName': 'INSERT', 'eventVersion': '1.1', 'eventSource': 'aws:dynamodb', 'awsRegion': 'us-west-1', 'dynamodb': {'ApproximateCreationDateTime': 1567576279.0, 'Keys': {'id': {'S': 'test_id2'}}, 'NewImage': {'key1': {'S': 'value1'}, 'key2': {'S': 'value2'}, 'id': {'S': 'test_id2'}}, 'SequenceNumber': '4500000000000852941236', 'SizeBytes': 40, 'StreamViewType': 'NEW_AND_OLD_IMAGES'}, 'eventSourceARN': 'arn:aws:dynamodb:us-west-1:756428767688:table/fssi2019-dynamodb-media-user-meta/stream/2019-09-04T04:37:25.589'}, {'eventID': 'bfc033a327e89a795c9acd676e6d1ffc', 'eventName': 'INSERT', 'eventVersion': '1.1', 'eventSource': 'aws:dynamodb', 'awsRegion': 'us-west-1', 'dynamodb': {'ApproximateCreationDateTime': 1567576280.0, 'Keys': {'id': {'S': 'test_id3'}}, 'NewImage': {'key1': {'S': 'value1'}, 'key2': {'S': 'value2'}, 'id': {'S': 'test_id3'}}, 'SequenceNumber': '4600000000000852941441', 'SizeBytes': 40, 'StreamViewType': 'NEW_AND_OLD_IMAGES'}, 'eventSourceARN': 'arn:aws:dynamodb:us-west-1:756428767688:table/fssi2019-dynamodb-media-user-meta/stream/2019-09-04T04:37:25.589'}]}
    lambda_handler(sampleEvent, None)
