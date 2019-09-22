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


def get_location():
    return 'mid-city'
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

if __name__ == '__main__':
    profileName = 'fssi2019-xacc-resource-access'
    session = boto3.session.Session(profile_name=profileName)
    snsClient = session.client('sns')
    snsTopicName = 'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission' 
else:

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
    response = snsClient.publish(TopicArn='arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission', Message=msgBody)
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
                response = snsClient.publish(TopicArn='arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission', Message=msgBody)
                if response and type(response) == dict and 'MessageId' in response:
                    return response
            else:
                raise ValueError('topic {} was not found'.format(snsTopicName))
    except:
        print('exception while publishing SNS', sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)

'''
def publishSns(experienceId, exposureV):
    snsMessageBody = exposureV
    mySnsClient = boto3.client('sns')
    response = mySnsClient.publish(TopicArn=getSnsTopicByName(FssiResources.Sns.Emission),
        Message=simplejson.dumps(snsMessageBody))
    if response and type(response) == dict and 'MessageId' in response:
        return
    else:
        print("unable to send SNS message: ", response)
'''

def paintingTag(tags):
    toReturn = []
    if 'religious' in tags:
        toReturn.append('church')
    if 'indoor' in tags:
        toReturn.append('indoors')
    if 'graffiti' in tags:
        toReturn.append('graffiti')
    if 'contemporary' in tags:
        toReturn.append('modern art')
    if 'landscape' in tags:
        toReturn.append('landscape')
    if 'environmental' in tags:
        toReturn.append('nature')
    return toReturn

def getTopFoods(tags):
    if not tags:
        return None
    toReturn = []
    cuisine_types = ['French', 'Thai', 'Indian', 'Chinese', 'Italian', 'Korean', 'Mexican','American', 'Mediterranean']
    for cuisine in cuisine_types:
        if cuisine in tags and tags[cuisine]['intensity'] == 1:
            toReturn.append(cuisine)
    return toReturn


def getTopFoodUrls(tags):
    if not tags:
        return None
    toReturn = ""
    cuisine_types = [['French',1422], ['Thai',1456], ['Indian',1368], ['Chinese',1422],  ['Italian',769], ['Mexican', 846]]#'Korean''','American', 'Mediterranean',  ]
    for cuisine in cuisine_types:
        if cuisine[0] in tags and tags[cuisine[0]]['intensity'] == 1:
            toReturn = toReturn + '~?' + getCuisineUrl(cuisine[0],cuisine[1])
    return toReturn

def getCuisineUrl(cuisine,size):
    index = random.randint(1,size)
    return 'https://fssi2019-jamie-photos.s3-us-west-1.amazonaws.com/cuisine/{}/{}.jpg'.format(cuisine.lower(),index)



def recommendImage(occupants):

    xpId = 'tactile'
    xpOccupancy = getOccupancy(xpId)

    visitorExposures = []
 
    veeps = []
    
    userTags = ''

    #print(xpOccupancy)

    for userId in xpOccupancy:
        vId = getVisitorIdentity(userId)
        vExp = getVisitorExposure(userId)
        if vId:
            for tg in vId:
                userTags = '{}~?{}'.format(userTags,tg)
            veeps.append(vId)
        #veeps.append(vExp)
        visitorExposures.append(vExp) 
            
    avg = {}
    for v in veeps[0:8]:
        avg = {**avg,**v}  

    #print(avg)      
    
    #avg = EmissionVector.simpleAverage(veeps)
    #tags = sorted(avg.items(), key=lambda x: x[1].intensity_,reverse=True)
    #print(tags)


    #return allTags
    allTags = paintingTag(avg)
    allTags.extend(getTopFoods(avg))

    if avg['traffic']['intensity'] > .7:
        allTags.append(random.choice(['Transportation', 'Road', 'Building', 'Bus', 'Traffic Light', 'Machine', 'Truck', 'Vehicle', 'Car', 'Freeway', 'Street']))
    elif avg['traffic']['intensity'] < .3:
        allTags.append(random.choice(['Sidewalk, Human, Person, Bike, Bicycle, Subway']))
       
    if avg['adventure']['intensity'] > .5:
        allTags.append(random.choice(['Sea', 'Outdoors', 'Human', 'Adventure', 'Person']))


    print(allTags)

    imageUrls = ''
    emissions = []

    for tag in allTags:
        results = tagQuery(tag)
        if results:
            choice = random.sample(results,3)
            for img in choice:
                imageUrls = '{}~?{}'.format(imageUrls,img[0])
                for emit in img[1][1:10]:
                    emissions.append(emit)

    imageUrls = imageUrls + getTopFoodUrls(avg) + getTopFoodUrls(avg) 
  
    imageUrls = imageUrls + '&'
    for emit in emissions:
        allTags.append(emit[0])
        imageUrls = imageUrls + '~?' + emit[0]


    emission = { "experience_id" : xpId,   "state": {}, "t" : time.time() }
    for tag in allTags: 
        emission['state'][tag] = {}
        emission['state'][tag]['sentiment'] = .5
        emission['state'][tag]['intensity'] = .5
    emissionVector = json.dumps(emission, sort_keys=True, indent=4)

    publishSns(emissionVector)

    imageUrls = imageUrls + '&'

    for tag in allTags:
        imageUrls = '{}~?{}'.format(imageUrls,tag)

    return imageUrls + userTags



def emitText(textString):

    xpId = 'tactile'
    comprehend = boto3.client('comprehend', region_name='us-west-2')

    phrases = comprehend.detect_key_phrases(Text=textString,LanguageCode='en')
    sentiment = comprehend.detect_sentiment(Text=textString,LanguageCode='en')
    #phrases = [{'Score': 0.7399657964706421, 'Text': 'downtown', 'BeginOffset': 0, 'EndOffset': 8}, {'Score': 0.6189231872558594, 'Text': 'home', 'BeginOffset': 37, 'EndOffset': 41}, {'Score': 0.9952608346939087, 'Text': 'the hoods', 'BeginOffset': 43, 'EndOffset': 52}, {'Score': 0.9308696389198303, 'Text': 'man poser', 'BeginOffset': 60, 'EndOffset': 69}, {'Score': 0.6694998145103455, 'Text': 'stop', 'BeginOffset': 91, 'EndOffset': 95}, {'Score': 0.9676438570022583, 'Text': 'the hollywood hills', 'BeginOffset': 97, 'EndOffset': 116}, {'Score': 0.9404119849205017, 'Text': 'hollywood hollywood', 'BeginOffset': 118, 'EndOffset': 137}, {'Score': 0.6332051753997803, 'Text': 'oh yes', 'BeginOffset': 140, 'EndOffset': 146}, {'Score': 0.9974281191825867, 'Text': 'the one', 'BeginOffset': 150, 'EndOffset': 157}, {'Score': 0.9991982579231262, 'Text': 'the moment', 'BeginOffset': 161, 'EndOffset': 171}, {'Score': 0.9990349411964417, 'Text': 'the way', 'BeginOffset': 176, 'EndOffset': 183}, {'Score': 0.9104302525520325, 'Text': 'bed and lights', 'BeginOffset': 201, 'EndOffset': 215}, {'Score': 0.8596657514572144, 'Text': 'a can drink', 'BeginOffset': 224, 'EndOffset': 235}, {'Score': 0.8826907277107239, 'Text': 'a back', 'BeginOffset': 242, 'EndOffset': 248}, {'Score': 0.9581464529037476, 'Text': 'his new i', 'BeginOffset': 257, 'EndOffset': 266}, {'Score': 0.9875640869140625, 'Text': 'the grap', 'BeginOffset': 269, 'EndOffset': 277}, {'Score': 0.8581511974334717, 'Text': 'a long', 'BeginOffset': 286, 'EndOffset': 292}, {'Score': 0.9913714528083801, 'Text': 'a walki', 'BeginOffset': 299, 'EndOffset': 306}]
    #sentiment = {'Sentiment': 'POSITIVE', 'SentimentScore': {'Positive': 0.43100911378860474, 'Negative': 0.04515540227293968, 'Neutral': 0.10286763310432434, 'Mixed': 0.42096781730651855}, 'ResponseMetadata': {'RequestId': 'ad785fd9-7199-4c9f-a30d-359655afea45', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'ad785fd9-7199-4c9f-a30d-359655afea45', 'content-type': 'application/x-amz-json-1.1', 'content-length': '163', 'date': 'Thu, 19 Sep 2019 20:09:35 GMT'}, 'RetryAttempts': 0}}


    pos = sentiment['SentimentScore']['Positive']
    neg = sentiment['SentimentScore']['Negative']
    sent = pos if pos > neg else -1*neg
    
    emission = { "experience_id" : xpId,   "state": {}, "t" : time.time() }
    for emit in phrases['KeyPhrases']: 
        emission['state'][emit['Text']] = {}
        emission['state'][emit['Text']]['sentiment'] = sent
        emission['state'][emit['Text']]['intensity'] = emit['Score']
    
    emissionVector = json.dumps(emission, sort_keys=True, indent=4)
    print(emissionVector)
    publishSns('xpId',emissionVector)

    return None


def recommendText(temperature):
    s3 = boto3.resource('s3')

    if temperature == -1:
        temperature = random.randint(4,9)

    itemname = '{}_{}_{}.txt'.format(get_location().lower(),temperature,random.randint(1,1001))
    print(itemname)
    obj = s3.Object('la-lyric-poems', itemname)
    body = obj.get()['Body'].read().decode("utf-8").replace('\n',',\n').replace('\t','') 
    #emitText(body)


    return body



'''
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
'''

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
    'lane': 'text', # can be one of: image, tag, audio, text
    'occupants': ['alice', 'bob'],
    'temperature': 6
    }

    '''
    occupants = getOccupancy('tactile')
    print(occupants)
    for id in occupants:
        
        print(getVisitorIdentity(id))
        print(getTopFoods(getVisitorIdentity(id)))
    print('=====')
    print('=====')
    for id in occupants:
        print(getVisitorExposure(id))
    '''
    print('\n')
    print(lambda_handler(payload, None).replace('&','\n\n'))






























