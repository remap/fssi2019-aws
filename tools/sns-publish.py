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
                    "venicebeach":  [0.8087875166357418, -0.9529862775779678] ,
                    "marinadelrey": [0.11315793978945798,  0.74881033573114],
                    "lebaneesetaco": [0.7539981625252824, -0.3213123222477674],
                    "soup": [0.2429661845336737, -0.08542835269519045],
                    "malibu": [0.4101501834528354, 0.37080509395715633]
                },
              "experience_id": "main_exhibit\\n"
             }

res = publishSns(json.dumps(emissionV))
print(res)
