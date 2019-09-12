import boto3
import time
import sys,traceback
import json

profileName = 'fssi2019-participant'
session = boto3.session.Session(profile_name=profileName)
snsClient = session.client('sns')
snsTopicName = 'fssi2019-sns-emission'

def publishSns(msgBody):
    try:
        topicList = snsClient.list_topics()
        if topicList:
            topicFound = False
            for topicDict in topicList['Topics']:
                arn = topicDict['TopicArn']
                if snsTopicName in arn:
                    topicFound = True
                    break
            if topicFound:
                print('topic found by name. ARN: ', arn)
                response = snsClient.publish(TopicArn=arn, Message=msgBody)
                if response and type(response) == dict and 'MessageId' in response:
                    return response
            else:
                raise ValueError('topic {} was not found'.format(snsTopicName))
    except:
        print('exception while publishing SNS', sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)
        raise

emissionV = {
              "state":
                {
                    "venicebeach": { "sentiment": -0.9529862775779678, "intensity": 0.8087875166357418} ,
                    "marinadelrey": {"sentiment": 0.74881033573114, "intensity": 0.11315793978945798},
                    "lebaneesetaco": {"sentiment": -0.3213123222477674, "intensity": 0.7539981625252824},
                    "soup": {"sentiment": -0.08542835269519045, "intensity": 0.2429661845336737},
                    "malibu": {"sentiment": 0.37080509395715633, "intensity": 0.4101501834528354}
                },
              "exhibit_id": "main_exhibit\\n"
             }

res = publishSns(json.dumps(emissionV))
print(res)
