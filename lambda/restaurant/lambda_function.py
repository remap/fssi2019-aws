import json
import boto3
import sys, traceback
import uuid
import os
from fssi_common import *
#import simplejson
import time
import random

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

def getVisitorTimestamp(visitorId):
    response = timeseriesGetLatestForKey(FssiResources.DynamoDB.VisitorEventTs,
      keyName='visitor_id', keyValue=visitorId)
    print( response)
    return response['timestamp']


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

CROSS_ACCT_ACCESS_ROLE = "arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access"

stsConnection = boto3.client('sts')
acctB = stsConnection.assume_role(
    RoleArn=CROSS_ACCT_ACCESS_ROLE,
    RoleSessionName="cross_acct_access"
)

ACCESS_KEY = acctB['Credentials']['AccessKeyId']
SECRET_KEY = acctB['Credentials']['SecretAccessKey']
SESSION_TOKEN = acctB['Credentials']['SessionToken']

snsClient = boto3.client(
    'sns',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)

def publishSns(msgBody):
    response = snsClient.publish(TopicArn="arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission", Message=msgBody)
    """try:
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
    """




def listTags(obj):
    if obj is not None:
        return list(obj.keys())
    return None

def most_dict(dict, n):
    most = []
    vs = list(dict.values())
    ks = list(dict.keys())
    for i in range(n):
        most.append(ks[vs.index(max(vs))])
        vs[vs.index(max(vs))] = 0
    return most

def extractdata(profiles):
    colors = []
    result = []
    total = {}
    for p in profiles:
        if p is not None:
            # print(listTags(p))
            for key in listTags(p):
                if key == 'color_val':
                    colors.append(p['color_val'])
                else:
                    if str(key) in total:
                        total[str(key)] = total[str(key)] + p[str(key)]['intensity']
                    else:
                        total[str(key)] = p[str(key)]['intensity']
    most = most_dict(total,4)
    result.append(most)
    result.append(colors)
    return result

def cuisines():
    dict = {
           'Chinese' : [ 'peanut-oil', 'corn-starch','sesame oil','oyster sauce', 'hoisin sauce'],
           'French' : ['butter', 'all-purpose-flour', 'eggs', 'butter', 'shallots'],
           'Mediterranean' : ['feta-cheese-crumbles','dried-oregano', 'cucumber', 'fresh lemon juice', 'feta cheese'],
           'Indian' : ['green-chilies','turmeric', 'cumin', 'ground turmeric', 'garam masala'],
           'Italian' : ['ground-black-pepper', 'olive-oil', 'extra virgin olive oil', 'fresh basil', 'parmesan'],
           'Japanese' : ['scallions','soy-sauce', 'rice vinegar', 'mirin', 'sake'],
           'Korean' : ['sesame-oil', 'sesame-seeds', 'toasted sesame seeds', 'kimchi', 'gochujang'],
           'Mexican' : ['avocado', 'flour-tortillas', 'black beans', 'salsa', 'corn tortillas'],
           'Southern_us' : ['milk', 'baking-powder', 'baking soda','vanilla extract',  'buttermilk'],
           'Thai' : ['lime-juice', 'peanuts', 'coconut milk', 'fish sauce', 'lemongrass'],
    }
    return dict

def food_data(profiles):
    total = []
    cuisinelist = cuisines().keys()
    for p in profiles:
        if p is not None:
            dict = {}
            for key in listTags(p):
                if key in cuisinelist:
                    dict[str(key)] = p[str(key)]['intensity']
            total.append(dict) 
    print(total)
    make_emission(total)
    return total  

def get_ingreds(li):
    result = []
    for dict in li:
        most = most_dict(dict, min(len(dict),3))
        for key in most:
            result.append(map(key,dict[str(key)]))
    return result

def map(cuisine, intens):
    ingred = 'NULL'
    dict = cuisines()

    i = int(((intens*10)-Decimal(0.01))//2)
    ingred = dict[cuisine][i]
    return ingred
                                                                                                                                                             
def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last =0.0
    while last <len(seq):
       out.append(seq[int(last):int(last+avg)])
       last += avg
    return out

def menu(li):
    with open('data') as json_file:
        data = json.load(json_file, strict=False)
    result = []
    print (len(list(data.keys())))
    for item in li:
        if len(item) == 1:
            insert = 'butter'
            item.append(insert)
        item.sort()
        dish = data[' '.join(item)][random.randint(0,9)]
        # print(dish)
        result.append(dish)
    return result

def make_emission(li):
    emission = {"experience_id" : 'corporeal', "state": {}, "t": time.time()}
    for dict in li:
        bag = list(dict.keys())
        print(bag)
        for tag in bag: 
            emission['state'][tag] = {}
            emission['state'][tag]['sentiment'] = 0.5
            emission['state'][tag]['intensity'] = str(dict[tag])
    print(emission)
    emissionVector = json.dumps(emission, sort_keys=True, indent=4)
    publishSns(emissionVector)
    '''
    mySnsClient = boto3.client('sns')
    response = mySnsClient.publish(TopicArn=getSnsTopicByName(FssiResources.Sns.Emission),
        Message=simplejson.dumps(snsMessageBody))
    if response and type(response) == dict and 'MessageId' in response:
        return
    else:
        print("unable to send SNS message: ", response)
   '''
def lambda_handler(event, context):
    loc = get_location()
    default = {
        'color' : [{'r': Decimal('0'), 'g': Decimal('0'), 'b': Decimal('0')}],
	'friend': ['sobremesa2028','sobremesa2028','sobremesa2028','sobremesa2028'],
	'menu' : ['Ask about daily specials', 'Ask about daily specials', 'Ask about daily specials'],
	'occ': 0,
        'location': loc

    }
    xpOccupancy = getOccupancy('corporeal')
    if xpOccupancy is None:
        print("no occupants")
        # print(getVisitorTimestamp('Bob'))
        return default
    visitorProfiles = []
    tagli = []
    num = 0
    timestamps = {}
    """for userId in xpOccupancy:
        timestamps[userId] = getVisitorTimestamp(userId)
    finalfour = (most_dict(timestamps)).keys()
    print(finalfour) """
    for userId in xpOccupancy:        
        vId = getVisitorIdentity(userId)
        visitorProfiles.append(vId)
        num += 1
        print('occupant {} profile {}\n'.format(userId, vId))
    # blair = getVisitorIdentity('Blair ')
    # tagli = (listTags(blair))
    profData = extractdata(visitorProfiles)
    ingredlist = chunkIt(get_ingreds(food_data(visitorProfiles)),3)
    screenmenu = menu(ingredlist)
    if not screenmenu:
        screenmenu =  ['Ask about daily specials', 'Ask about daily specials', 'Ask about daily specials']
    print(screenmenu)

    returnPackage = {
	'color' : profData[1],
	'friend': profData[0],
	'menu' : screenmenu,
	'occ': num,
        'location': loc,
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
