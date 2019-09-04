import time
import boto3
import copy
import json
from decimal import Decimal
import sys, traceback
import uuid
from datetime import datetime

CROSS_ACCT_ACCESS_ROLE = "arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access"

stsConnection = boto3.client('sts')
acctB = stsConnection.assume_role(
    RoleArn=CROSS_ACCT_ACCESS_ROLE,
    RoleSessionName="cross_acct_access"
)

ACCESS_KEY = acctB['Credentials']['AccessKeyId']
SECRET_KEY = acctB['Credentials']['SecretAccessKey']
SESSION_TOKEN = acctB['Credentials']['SessionToken']

dynamoDbClient = boto3.client(
    'dynamodb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)

dynamoDbResource = boto3.resource(
    'dynamodb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)

snsClient = boto3.client(
    'sns',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)

################################################################################
# FSSI2019 RESOURCES
################################################################################
class FssiResources():
    class DynamoDB():
        ExperienceEmissionTs = "fssi2019-dynamodb-experience_emission_ts"
        ExperienceExposureTs = "fssi2019-dynamodb-experience_exposure_ts"
        Experience = "fssi2019-dynamodb-experience"
        Folksonomy = "fssi2019-dynamodb-folksonomy"
        KeywordRelevanceTs = "fssi2019-dynamodb-keyword_relevance_ts"
        Occupancy = "fssi2019-dynamodb-occupancy"
        Pavilion = "fssi2019-dynamodb-pavilion"
        Visitor = "fssi2019-dynamodb-visitor"
        VisitorEventTs = "fssi2019-dynamodb-visitor_event_ts"
        VisitorExposureTs = "fssi2019-dynamodb-visitor_exposure_ts"

        MediaUserMeta = "fssi2019-dynamodb-media-user-meta"

    class S3Bucket():
        Ingest = "fssi2019-s3-ingest"
    class Sns():
        DynamodbUpdates = "fssi2019-sns-dynamodb-updates"

################################################################################
# GENERAL HELPERS
################################################################################
def reportError():
    type, err, tb = sys.exc_info()
    print('caught exception:', err)
    traceback.print_exc(file=sys.stdout)
    return err

################################################################################
# SNS HELPERS
################################################################################
def getSnsTopicByName(snsTopicName):
    topicList = snsClient.list_topics()
    if topicList:
        topicFound = False
        for topicDict in topicList['Topics']:
            arn = topicDict['TopicArn']
            if snsTopicName in arn:
                return arn
    return None

################################################################################
# DYNAMODB HELPERS
################################################################################
def timeseriesGetLatestForKey(tableName, keyName, keyValue):
    response = dynamoDbClient.query(TableName=tableName,
                         KeyConditionExpression="{} = :v_id".format(keyName),
                         ExpressionAttributeValues={":v_id": {'S': keyValue}},
                         Select='ALL_ATTRIBUTES',
                         Limit=1,
                         ScanIndexForward=False)
    return response

def timeseriesAdd(tableName, records):
    table = dynamoDbResource.Table(tableName)
    itemDict = records
    itemDict['timestamp'] = Decimal(time.time())
    table.put_item(Item = itemDict)

def getMediaItemUuid():
    return str(uuid.uuid4())

def makeMediaMetaItem(itemId, s3BucketName):
    return {
        'id' : itemId,
        'bucket': s3BucketName,
        'created': str(datetime.now()),
        'userMeta': {}
    }


################################################################################
# LAMBDA HELPERS
################################################################################
def lambdaReply(code, message):
    print('lambda reply {}: {}'.format(code, message))
    return {
        'statusCode': code,
        'body': json.dumps(message)
    }

def malformedMessageReply():
    return lambdaReply(420, 'Malformed message received')

def processedReply():
    return lambdaReply(200, 'Message processed')

################################################################################
# VISITOR MANAGEMENT CLASSES
################################################################################
class KeywordState():
    def __init__(self, keyword, dictOrIntensity = None, sentiment = None):
        if isinstance(sentiment,float) and isinstance(dictOrIntensity, float):
            self.keyword_ = keyword
            self.intensity_ = dictOrIntensity
            self.sentiment_ = sentiment
        elif isinstance(dictOrIntensity, dict):
            self.keyword_ = keyword
            self.intensity_ = 0.
            self.sentiment_ = 1.
            if 'intensity' in dictOrIntensity:
                self.intensity_ = dictOrIntensity['intensity']
            if 'sentiment' in dictOrIntensity:
                self.sentiment_ = dictOrIntensity['sentiment']
        elif isinstance(keyword, KeywordState):
            self.keyword_ = keyword.keyword_
            self.intensity_ = keyword.intensity_
            self.sentiment_ = keyword.sentiment_
        else:
            raise ValueError('bad arguments in KeywordState constructor')

    def encode(self):
        return {'intensity' : self.intensity_, 'sentiment' : self.sentiment_}
        # return [ self.intensity_, self.sentiment_ ]

    def __add__(self, other):
        if self.keyword_ == other.keyword_:
            i = KeywordState.cummulateIntensity(self.intensity_, other.intensity_)
            s = KeywordState.cummulateSentiment(self.sentiment_, other.sentiment_)
            return KeywordState(self.keyword_, i, s)
        raise ValueError("can't add up incompatible keyword states: {} and {}".format(self.keyword_, other.keyword_))

    def __repr__(self):
        return repr(self.encode())

    @classmethod
    def cummulateIntensity(cls, i1, i2):
        return (i1 + i2)/2

    @classmethod
    def cummulateSentiment(cls, s1, s2):
        return (s1 + s2)/2

    @classmethod
    def simpleAverage(cls, kwStates):
        averaged = []
        if len(kwStates) > 0:
            stats = {}
            for kws in kwStates:
                if kws.keyword_ in stats:
                    # stats[kws.keyword_]['num'] += 1.
                    stats[kws.keyword_]['intensities'].append(kws.intensity_)
                    stats[kws.keyword_]['sentiments'].append(kws.sentiment_)
                else:
                    stats[kws.keyword_] = {'intensities': [kws.intensity_], 'sentiments': [kws.sentiment_]}
            for k,stat in stats.items():
                iAvg = KeywordState.averageIntensity(stat['intensities'])
                sAvg = KeywordState.averageSentiment(stat['sentiments'])
                averaged.append(KeywordState(k, iAvg, sAvg))
        return averaged

    @classmethod
    def averageIntensity(cls, intensities):
        return sum(intensities) / len(intensities)

    @classmethod
    def averageSentiment(cls, sentiments):
        return sum(sentiments) / len(sentiments)

class EmissionVector():
    def __init__(self, arg):
        self.timestamp_ = None
        self.kwStates_ = {}
        if isinstance(arg, dict):
            for kw, kwDict in arg.items():
                self.kwStates_[kw] = KeywordState(kw,kwDict)
        elif isinstance(arg, list):
            for kws in arg:
                self.kwStates_[kws.keyword_] = kws
        elif isinstance(arg, EmissionVector):
            self.kwStates_ = copy.deepcopy(arg.kwStates_)
        else:
            raise ValueError('bad argument supplied to EmissionVector constructor: {}. must be dict or list'.format(arg))

    def append(self, keywordState):
        if keywordState.keyword_ in self.kwStates_:
            self.kwStates_[keywordState.keyword_] += keywordState
        else:
            self.kwStates_[keywordState.keyword_] = keywordState

    def encode(self):
        emissionV = {}
        for kw, kwState in self.kwStates_.items():
            emissionV[kwState.keyword_] = kwState.encode()
        return emissionV

    def kwStates(self):
        return list(self.kwStates_.values())

    def items(self):
        return self.kwStates_.items()

    def __setitem__(self, key, item):
        self.kwStates_[key] = item

    def __getitem__(self, key):
        return self.kwStates_[key]

    def __add__(self,other):
        return EmissionVector.cummulateVectors(self, other)

    def __repr__(self):
        return repr(self.encode())

    @classmethod
    def cummulateVectors(cls, v1, v2):
        resultV = EmissionVector([])
        for kw, kws in v1.items():
            resultV.append(kws)
        for kw, kws in v2.items():
            resultV.append(kws)
        return resultV

    @classmethod
    def simpleAverage(cls, vectors):
        allKwStates = []
        for v in vectors:
            allKwStates.extend(v.kwStates())
        averaged = KeywordState.simpleAverage(allKwStates)
        return EmissionVector(averaged)

ExposureVector = EmissionVector

class ExperienceState():
    ExperienceIdKey='experience_id'
    ExperienceStateKey='state'

    def __init__(self, dict):
        if not (ExperienceState.ExperienceIdKey in dict and ExperienceState.ExperienceStateKey in dict):
            raise ValueError('malformed experience state message: {}'.format(dict))
        self.experienceId_ = dict[ExperienceState.ExperienceIdKey]
        self.emissionVector_ = EmissionVector(dict[ExperienceState.ExperienceStateKey])

    def encode(self):
        return { ExperienceState.ExperienceIdKey : self.experienceId_,
                 ExperienceState.ExperienceStateKey : self.emissionVector_.encode()}

    def __repr__(self):
        return repr(self.encode())
