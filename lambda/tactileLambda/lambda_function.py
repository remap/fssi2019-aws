import json
import boto3
import sys, traceback
import uuid
import os
from fssi_common import *
import simplejson
import time
import random
from query import *

profileName = 'fssi2019-xacc-intraorg-resource-access'
session = boto3.session.Session(profile_name=profileName)
snsClient = session.client('sns')
snsTopicName = 'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission' 

def get_location():
    db = boto3.resource(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )
    locationTable = db.Table('fssi2019-dynamodb-popuplocation')
    resp = locationTable.scan()
    return resp['Items'][0]['id']


def getOccupancy(experienceId):
    # get latest occupancy for the experience
    # the occupancy is an array of visitor IDs (QR codes)
    occupancyTable = dynamoDbResource.Table(FssiResources.DynamoDB.Occupancy)
    result = occupancyTable.get_item(Key={'id' : experienceId})
    if 'Item' in result:
        return result['Item']['occupancy']
    return None

def getVisitorExposure(visitorId):
    response = timeseriesGetLatestForKey(FssiResources.DynamoDB.VisitorExposureTs,
      keyName='visitor_id', keyValue=visitorId)
    if response['Count'] > 0:
        return ExposureVector(json.loads(response['Items'][0]['exposure']['S']))
    return ExposureVector({})

def publishSns(experienceId, exposureV):
    snsMessageBody = { 'experience_id' : experienceId,
                        'exposure' : exposureV.encode(),
                        't': time.time()}
    mySnsClient = boto3.client('sns')
    response = mySnsClient.publish(TopicArn=getSnsTopicByName(FssiResources.Sns.ExposureUpdates),
        Message=simplejson.dumps(snsMessageBody))
    if response and type(response) == dict and 'MessageId' in response:
        return
    else:
        print("unable to send SNS message: ", response)

def recommendImage(occupants):


    xpId = 'tactile'
    xpOccupancy = getOccupancy(xpId)
    

    visitorExposures = []
    veeps = []

    for userId in xpOccupancy:
        vExp = getVisitorExposure(userId)
        visitorExposures.append(vExp)
        veeps.append(vExp)
        print(getVisitorIdentity(userId))
        #print('occupant {} exposure {}'.format(userId, vExp))
    avg = EmissionVector.simpleAverage(veeps)
    tags= sorted(avg.items(), key=lambda x: x[1].intensity_,reverse=True)

    #results = tagQuery('bird')
    #return random.choice(results)[0]

    tags = [['bird'], ['asdf']]

    for tag in tags:
        print(tag[0])
        results = tagQuery(tag[0])
        if results:
            primeResult = random.choice(results)
            emissions = []
            for emit in primeResult[1]:
                emissions.append(emit[0])
            
            emission = { "experience_id" : xpId,   "state": {}, "t" : time.time() }
            for emit in emissions: 
                emission['state'][emit] = {}
                emission['state'][emit]['sentiment'] = .5
                emission['state'][emit]['intensity'] = .5
            print(json.dumps(emission, sort_keys=True, indent=4))
            try: 
                print("Published to %s:" % snsTopicName, publishSns(json.dumps(emission))['MessageId'])
            except:
                print('exception while publishing SNS', sys.exc_info()[0])
                traceback.print_exc(file=sys.stdout)


            return (primeResult[0], emissions)



def recommendText(temperature):
    s3 = boto3.resource('s3')

    if temperature == -1:
        temperature = random.randint(4,9)

    itemname = '{}_{}_{}.txt'.format(get_location().lower(),temperature,random.randint(1,1001))
    obj = s3.Object('la-lyric-poems', itemname)
    body = obj.get()['Body'].read().decode("utf-8").replace('\n',',\n').replace('\t','')
    return body

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
                #print('topic found by name. ARN: ', arn)
                response = snsClient.publish(TopicArn=arn, Message=msgBody)
                if response and type(response) == dict and 'MessageId' in response:
                    return response
            else:
                raise ValueError('topic {} was not found'.format(snsTopicName))
    except:
        print('exception while publishing SNS', sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)


def recommendHashtag(event):
    return '#institute4life'

def getVisitorIdentity(visitorId):
    identityTable = dynamoDbResource.Table(FssiResources.DynamoDB.Visitor)
    result = identityTable.get_item(Key={'id' : visitorId})
    if 'Item' in result:
        return result['Item']['ident_begin']
    return None


def lambda_handler(event, context):



    '''
    xpId = 'tactile'
    xpOccupancy = getOccupancy(xpId)
    for userId in xpOccupancy:
        print('userId: {}'.format(userId))
        print(getVisitorIdentity(userId))
        print()
    '''


    lane = event['lane']
    
    if lane == 'image':
        return recommendImage(event['occupants'])
    elif lane == 'text':
        return recommendText(event['temperature'])
    elif lane == 'tag':
        return recommendHashtag(event['occupants'])

    return None

    try:
        # change it or get it from event dictionary
        xpId = 'tactile'
        xpOccupancy = getOccupancy(xpId)
        #print('experience {}. occupancy {}'.format(xpId, xpOccupancy))

        # get experience exposure
        reply = timeseriesGetLatestForKey(FssiResources.DynamoDB.ExperienceExposureTs, 'experience_id', xpId)
        pyDict = unmarshallAwsDataItem(reply['Items'][0])
        xpExposure = ExposureVector(json.loads(pyDict['exposure']))
        #print('experience aggregate exposure {}'.format(xpExposure))

        # get each visitor's exposure
        visitorExposures = []
        veeps = []
        for userId in xpOccupancy:
            vExp = getVisitorExposure(userId)
            visitorExposures.append(vExp)
            veeps.append(vExp)
            #print('occupant {} exposure {}'.format(userId, vExp))
        avg = EmissionVector.simpleAverage(veeps)
        print(sorted(avg.items(), key=lambda x: x[1].intensity_)[-1])


        # get experience emission
        reply = timeseriesGetLatestForKey(FssiResources.DynamoDB.ExperienceEmissionTs, 'experience_id', xpId)
        pyDict = unmarshallAwsDataItem(reply['Items'][0])
        pyDict['state'] = json.loads(pyDict['state'])
        xpEmission = ExperienceState(pyDict)
        #print('experience {} last emission: {}'.format(xpEmission.experienceId_, xpEmission.emissionVector_))



    except:
        _, err, tb = sys.exc_info()
        print('caught exception:', err)
        traceback.print_exc(file=sys.stdout)
        return lambdaReply(420, str(err))


    return processedReply()

# for local testing
if __name__ == '__main__':
    payload = {
    'lane': 'image', # can be one of: image, tag, audio, text
    'occupants': ['alice', 'bob'],
    'temperature': 6
    }

    print(lambda_handler(payload, None))






























