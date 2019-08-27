import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
import time
from fssi_common import ACCESS_KEY, SECRET_KEY, SESSION_TOKEN

def lambda_handler(event, context):
    if not ('visitor_id' in event):
        return { 'statusCode': 400,
                 'body': "The input event must have a visitor_id" }
    visitor_id = event['visitor_id']

    if not ('experience_id' in event):
        return { 'statusCode': 400,
                 'body': "The input event must have a experience_id" }
    experience_id = event['experience_id']

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )

    # Get all events with the visitor_id and experience_id.
    visitorEventTable = dynamodb.Table('fssi2019-dynamodb-visitor_event_ts')
    # Note: Scan reads all records from DynamoDB. Maybe set up a secondary index.
    visitorEvents = visitorEventTable.scan(
        FilterExpression=Attr('visitor_id').eq(visitor_id) &
                         Attr('experience_id').eq(experience_id)
    )

    # Get the visitor event with the latest timestamp.
    latestEvent = None
    for e in visitorEvents['Items']:
        if latestEvent == None or e['timestamp'] > latestEvent['timestamp']:
            latestEvent = e

    print("Debug: latestEvent: " + str(latestEvent))
    
    # Figure out whether the event means that the visitor is entering the experience.
    if latestEvent == None or latestEvent['event'] == 'exit':
        isEntering = True
    else:
        isEntering = False

    # TODO: If latestEvent['event'] == 'off-board', do we need to on-board before entry?

    # Add a new visitor event.
    visitorEventTable.put_item(Item=
      { 'timestamp': time.time(),
        'visitor_id': visitor_id,
        'experience_id': experience_id,
        'event': 'entry' if isEntering else 'exit',
        'confidence': Decimal('1.0') })

    # Update the occupancy table for the experience based on isEntering.
    occupancyTable = dynamodb.Table('fssi2019-dynamodb-occupancy')
    occupancyResponse = occupancyTable.get_item(Key={ 'id': experience_id })
    if 'Item' in occupancyResponse:
        occupancy = occupancyResponse['Item']['occupancy']
        if isEntering:
            occupancy.add(visitor_id)
        else:
            occupancy.discard(visitor_id)

        occupancyTable.put_item(Item=
          { 'id': experience_id, 'occupancy': occupancy })
    else:
        # The is no entry for the experience_id. Create it if is entering.
        if isEntering:
            occupancyTable.put_item(Item=
              { 'id': experience_id,
                'occupancy': set([visitor_id]) })

    return { 'statusCode': 200,
             'body': json.dumps({ 'event': event }) }
