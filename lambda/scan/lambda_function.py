import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
import time
from fssi_common import ACCESS_KEY, SECRET_KEY, SESSION_TOKEN

def lambda_handler(event, context):
    msgBody = json.loads(event['Records'][0]['Sns']['Message'])
    if not ('visitor_id' in msgBody):
        return { 'statusCode': 400,
                 'body': "The input event must have a visitor_id" }
    visitor_id = msgBody['visitor_id']

    if not ('experience_id' in msgBody):
        return { 'statusCode': 400,
                 'body': "The input event must have a experience_id" }
    experience_id = msgBody['experience_id']

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )

    visitorEventTable = dynamodb.Table('fssi2019-dynamodb-visitor_event_ts')
    occupancyTable = dynamodb.Table('fssi2019-dynamodb-occupancy')

    # Get all events with the visitor_id.
    # Note: Scan reads all records from DynamoDB. Maybe set up a secondary index.
    visitorEvents = visitorEventTable.scan(
      FilterExpression=Attr('visitor_id').eq(visitor_id))

    # Get the visitor event with the latest timestamp.
    latestEvent = None
    for e in visitorEvents['Items']:
        if latestEvent == None or e['timestamp'] > latestEvent['timestamp']:
            latestEvent = e

    print("Debug: latestEvent: " + str(latestEvent))
    messageExit = None
    # Figure out whether the event means that the visitor is entering the experience.
    if latestEvent == None:
        isEntering = True
    elif latestEvent['experience_id'] == experience_id:
        if latestEvent['event'] == 'exit':
            # Re-entering this experience.
            isEntering = True
        else:
            # Now exiting.
            isEntering = False
    else:
        # The latest event was for a different experience. We have to be
        # entering this experience.
        isEntering = True
        if latestEvent['event'] != 'exit':
            # The visitor must have exited the other experience without scanning.
            # Add an exit event for the other experience and remove from occupancy.
            visitorEventTable.put_item(Item=
              { 'timestamp': Decimal(time.time()),
                'visitor_id': visitor_id,
                'experience_id': latestEvent['experience_id'],
                'event': 'exit',
                'confidence': Decimal(1.0) })
            messageExit={"defualt": {"event": "exit", "experience_id": latestEvent['experience_id'], "visitor_id":visitor_id}} 
            occupancyResponse = occupancyTable.get_item(Key=
              { 'id': latestEvent['experience_id'] })
            if 'Item' in occupancyResponse:
                occupancy = occupancyResponse['Item']['occupancy']
                occupancy.discard(visitor_id)
                if len(occupancy) == 0:
                    # The empty set is not allowed, so remove the entry.
                    occupancyTable.delete_item(Key=
                      { 'id': latestEvent['experience_id'] })
                else:
                    occupancyTable.put_item(Item=
                      { 'id': latestEvent['experience_id'], 'occupancy': occupancy })

    # Add a new visitor event.
    visitorEventTable.put_item(Item=
      { 'timestamp': Decimal(time.time()),
        'visitor_id': visitor_id,
        'experience_id': experience_id,
        'event': 'entry' if isEntering else 'exit',
        'confidence': Decimal(1.0) })
        
    mySnsClient = boto3.client('sns')
    if isEntering:
        message={"defualt": {"event": "entry", "experience_id": experience_id, "visitor_id":visitor_id}}
    else:
        message = message={"defualt": {"event": "exit", "experience_id": experience_id, "visitor_id":visitor_id}}
    response = mySnsClient.publish(TopicArn='arn:aws:sns:us-west-1:756428767688:fssi2019-sns-visitor-event', Message=json.dumps(message))
    
    if messageExit is not None:
        response = mySnsClient.publish(TopicArn='arn:aws:sns:us-west-1:756428767688:fssi2019-sns-visitor-event', Message=json.dumps(messageExit))

    # Update the occupancy table for the experience based on isEntering.
    occupancyResponse = occupancyTable.get_item(Key={ 'id': experience_id })
    if 'Item' in occupancyResponse:
        occupancy = occupancyResponse['Item']['occupancy']
        if isEntering:
            occupancy.add(visitor_id)
        else:
            occupancy.discard(visitor_id)

        if len(occupancy) == 0:
            # The empty set is not allowed, so remove the entry.
            occupancyTable.delete_item(Key={ 'id': experience_id })
        else:
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
