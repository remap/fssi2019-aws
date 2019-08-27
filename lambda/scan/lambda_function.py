import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import time
from fssi_common import ACCESS_KEY, SECRET_KEY, SESSION_TOKEN

def lambda_handler(event, context):
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )

    if not ('visitor_id' in event):
        return { 'statusCode': 400,
                 'body': "The input event must have a visitor_id" }
    if not ('experience_id' in event):
        return { 'statusCode': 400,
                 'body': "The input event must have a experience_id" }

    # Get all events with the visitor_id and experience_id.
    table = dynamodb.Table('fssi2019-dynamodb-visitor_event_ts')
    response = table.scan(
        FilterExpression=Attr('visitor_id').eq(event['visitor_id']) &
                         Attr('experience_id').eq(event['experience_id'])
    )

    # Get the visitor event with the latest timestamp.
    latestEvent = None
    for e in response['Items']:
        if latestEvent == None or e['timestamp'] > latestEvent['timestamp']:
            latestEvent = e

    # TODO: Check if latestEvent == None

    print("latestEvent: " + str(latestEvent))

    return { 'statusCode': 200,
             'body': json.dumps({ 'event': event }) }
