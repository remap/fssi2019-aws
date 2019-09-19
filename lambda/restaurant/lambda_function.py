import json
import boto3
import sys, traceback
import uuid
import os
from fssi_common import *
#import simplejson
import time

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

def getVisitorIdentity(visitorId):
    identityTable = dynamoDbResource.Table(FssiResources.DynamoDB.Visitor)
    result = identityTable.get_item(Key={'id' : visitorId})
    if 'Item' in result:
        return result['Item']['ident_begin']
    return None

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
def listTags(obj):
    if obj is not None:
        return list(obj.keys())
    return None
def extractdata(profiles):
    most = []
    colors = []
    result = []
    total = {}
    for key in listTags(profiles[0]):
        if key == 'color_val':
            for p in profiles:
                if p is not None:
                    colors.append(p['color_val'])
        else:
            total[key] = 0
            for p in profiles:
                if p is not None and key in p:
                    # print(p[str(key)])
                    total[str(key)] = total[str(key)] + p[str(key)]['intensity']
                # print (key +' '+ str(total[str(key)]))
    vs = list(total.values())
    ks = list(total.keys())
    most.append(ks[vs.index(max(vs))])
    vs[vs.index(max(vs))] = 0
    most.append(ks[vs.index(max(vs))])
    vs[vs.index(max(vs))] = 0
    most.append(ks[vs.index(max(vs))])
    vs[vs.index(max(vs))] = 0
    most.append(ks[vs.index(max(vs))])
    result.append(most)
    result.append(colors)
    return result

def lambda_handler(event, context):
    xpOccupancy = getOccupancy('offboard')
    visitorProfiles = []
    tagli = []
    num = 0
    for userId in xpOccupancy:        
        vId = getVisitorIdentity(userId)
        visitorProfiles.append(vId)
        num += 1
        print('occupant {} profile {}\n'.format(userId, vId))
    # blair = getVisitorIdentity('Blair ')
    # tagli = (listTags(blair))
    profData = extractdata(visitorProfiles)
    print(profData[1])
    returnPackage = {
	'color' : profData[1],
	'friend': profData[0],
	'menu' : ['rice beans tacos', 'sugar butter flour', 'cheese butter pasta'],
	'occ': num
    }
    # returnPackage = json.dumps(message)
    """
    try:
        # change it or get it from event dictionary
        xpId = 'tactile'
        xpOccupancy = getOccupancy(xpId)
        print('experience {}. occupancy {}'.format(xpId, xpOccupancy))

        # get experience exposure
        reply = timeseriesGetLatestForKey(FssiResources.DynamoDB.ExperienceExposureTs, 'experience_id', xpId)
        pyDict = unmarshallAwsDataItem(reply['Items'][0])
        xpExposure = ExposureVector(json.loads(pyDict['exposure']))
        print('experience aggregate exposure {}'.format(xpExposure))

        # get each visitor's exposure
        visitorExposures = []
        for userId in xpOccupancy:
            vExp = getVisitorExposure(userId)
            visitorExposures.append(vExp)
            print('occupant {} exposure {}'.format(userId, vExp))

        # get experience emission
        reply = timeseriesGetLatestForKey(FssiResources.DynamoDB.ExperienceEmissionTs, 'experience_id', xpId)
        pyDict = unmarshallAwsDataItem(reply['Items'][0])
        pyDict['state'] = json.loads(pyDict['state'])
        xpEmission = ExperienceState(pyDict)
        print('experience {} last emission: {}'.format(xpEmission.experienceId_, xpEmission.emissionVector_))

        # get identity info here

    except:
        type, err, tb = sys.exc_info()
        print('caught exception:', err)
        traceback.print_exc(file=sys.stdout)
        return lambdaReply(420, str(err))
    """ 
    return returnPackage
    # return processedReply()

# for local testing
if __name__ == '__main__':
    lambda_handler(None, None)
