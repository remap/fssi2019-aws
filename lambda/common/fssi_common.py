import time
import boto3
import copy
import json
from decimal import Decimal
import sys, traceback, os
import uuid
from datetime import datetime
import urllib.request, mimetypes
import statistics

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

s3Client = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)

esClient = boto3.client('es',
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
        Location = "fssi2019-dynamodb-popuplocation"

        MediaUserMetaPreload = "fssi2019-dynamodb-media-user-meta-preload"
        MediaUserMeta = "fssi2019-dynamodb-media-user-meta"
        MediaFileMetaPreload = "fssi2019-dynamodb-media-file-meta-preload"
        MediaFileMeta = "fssi2019-dynamodb-media-file-meta"
        MediaTranscribeMeta = "fssi2019-dynamodb-media-transcribe-meta"
        MediaComprehendMeta = "fssi2019-dynamodb-media-comprehend-meta"
        MediaRekognitionMeta = "fssi2019-dynamodb-media-rekognition-meta"

    class S3Bucket():
        Ingest = "fssi2019-s3-ingest"

    class Sns():
        DynamodbUpdates = "fssi2019-sns-dynamodb-updates"
        ElasticSearchUpdates = "fssi2019-sns-elasticsearch-updates"
        ExposureUpdates = "fssi2019-sns-exposure-update"

    class Lambda():
        FileProc = "fssi2019-lambda-media-file-proc"
        TranscribeProc = "fssi2019-lambda-media-transcribe-proc"
        ComprehendProc = "fssi2019-lambda-media-comprehend-proc"
        RekognitionProc = "fssi2019-lambda-media-rekognition-proc"

    class ElasticSearch():
        ProductionDomain = "fssi2019-elasticsearch-production"
        StageDomain = "fssi2019-elasticsearch-stage"
        DevDomain = "fssi2019-elasticsearch-dev"

################################################################################
# GENERAL HELPERS
################################################################################
def reportError():
    type, err, tb = sys.exc_info()
    print('caught exception:', err)
    traceback.print_exc(file=sys.stdout)
    return err

def downloadFile(objectKey, s3BucketName):
    fName = os.path.join('/tmp',objectKey.replace('/', '-'))
    s3Client.download_file(s3BucketName, objectKey, fName)
    return fName

def guessMimeTypeFromExt(fileName):
    # try to guwss from file extension first
    type, _ = mimetypes.guess_type(urllib.request.pathname2url(fileName))
    if type:
        return type
    return None

def guessMimeTypeFromFile(fileName):
    ## try reading the header
    res = os.popen('file --mime-type '+fileName).read()
    type = res.split(':')[-1].strip()
    return type

def unmarshallAwsDataItem(awsDict):
    boto3.resource('dynamodb')
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    pyDict = {k: deserializer.deserialize(v) for k,v in awsDict.items()}
    return pyDict

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
        'meta': {}
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
    def __init__(self, keyword, dictOrIntensity = None, sentiment = None, age = None):
        if (isinstance(sentiment,float) or isinstance(sentiment,int)) and (isinstance(dictOrIntensity, float) or isinstance(dictOrIntensity, int)):
            self.keyword_ = keyword
            self.intensity_ = float(dictOrIntensity)
            self.sentiment_ = float(sentiment)
            if age:
                self.age_ = age
            else:
                self.age_ = 0.
        elif isinstance(dictOrIntensity, dict):
            self.keyword_ = keyword
            self.intensity_ = 0.
            self.sentiment_ = 1.
            self.age_ = 0.
            if 'intensity' in dictOrIntensity:
                self.intensity_ = dictOrIntensity['intensity']
            if 'sentiment' in dictOrIntensity:
                self.sentiment_ = dictOrIntensity['sentiment']
            if 'age' in dictOrIntensity:
                self.age_ = dictOrIntensity['age']
        elif isinstance(keyword, KeywordState):
            self.keyword_ = keyword.keyword_
            self.intensity_ = keyword.intensity_
            self.sentiment_ = keyword.sentiment_
            self.age_ = keyword.age_
        else:
            raise ValueError('bad arguments in KeywordState constructor: {} {}'.format(type(dictOrIntensity), type(sentiment)))

    def encode(self):
        return {'intensity' : self.intensity_, 'sentiment' : self.sentiment_, 'age': self.age_}
        # return [ self.intensity_, self.sentiment_, self.age_ ]

    def __add__(self, other):
        if self.keyword_ == other.keyword_:
            i = KeywordState.cummulateIntensity(self.intensity_, other.intensity_)
            s = KeywordState.cummulateSentiment(self.sentiment_, other.sentiment_)
            a = max(self.age_, other.age_)
            return KeywordState(self.keyword_, i, s, a)
        raise ValueError("can't add up incompatible keyword states: {} and {}".format(self.keyword_, other.keyword_))

    def __mul__(self, scalar):
        return KeywordState(self.keyword_, self.intensity_*scalar, self.sentiment_*scalar, self.age_)

    def __repr__(self):
        return repr(self.encode())

    @classmethod
    def sum(cls, states):
        keyword = states[0].keyword_
        intensitySum = 0
        sentimentSum = 0
        a = 0
        for kws in states:
            if kws.keyword_ == keyword:
                intensitySum += kws.intensity_
                sentimentSum += kws.sentiment_
                if kws.age_ > a:
                    a = kws.age_
        return KeywordState(keyword, intensitySum, sentimentSum, a)

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
    def simpleMedian(cls, kwStates):
        '''Finds median for list of keyword states for a given dimension.

        :param kwStates: List of KeywordState objects. Note: all keyword states
                     should have the same keyword. States that have keyword
                     different from the first state will be ignored.
        :return: A KeywordState object that is a median for a given list
        '''

        keyword = kwStates[0].keyword_
        intensities = []
        sentiments = []
        ages = []
        for kws in kwStates:
            if kws.keyword_ == keyword:
                intensities.append(kws.intensity_)
                sentiments.append(kws.sentiment_)
                ages.append(kws.age_)
        return KeywordState(keyword, statistics.median(intensities), statistics.median(sentiments), statistics.median(ages))

    @classmethod
    def averageIntensity(cls, intensities):
        return sum(intensities) / len(intensities)

    @classmethod
    def averageSentiment(cls, sentiments):
        return sum(sentiments) / len(sentiments)

class EmissionVector():
    class Filter():
        class Value():
            Intensity = 1<<0
            Sentiment = 1<<1

        class Level():
            Low = 1<<0
            Medium = 1<<1
            High = 1<<2

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

    def __mul__(self, scalar):
        res = []
        for kw, kws in self.kwStates_.items():
            res.append(kws*scalar)
        return EmissionVector(res)

    def __repr__(self):
        return repr(self.encode())

    def cull(self, ageThreshold, iThreshold = 0.001, sThreshold = None):
        result = []
        for kw, kws in self.kwStates_.items():
            if kws.age_ >= ageThreshold:
                if sThreshold:
                    if kws.intensity_ > iThreshold or abs(kws.sentiment_) > sThreshold:
                        result.append(kws)
                else:
                    if kws.intensity_ > iThreshold:
                        result.append(kws)
            else:
                result.append(kws)
        return EmissionVector(result)

    def ageBy(self, delta):
        for kw, kws in self.kwStates_.items():
            kws.age_ += delta

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

    @classmethod
    def sum(cls, vectors):
        states = {}
        for v in vectors:
            for kws in v.kwStates():
                if not kws.keyword_ in states:
                    states[kws.keyword_] = []
                states[kws.keyword_].append(kws)
        sumV = []
        for _,s in states.items():
            sumV.append(KeywordState.sum(s))
        return EmissionVector(sumV)

    @classmethod
    def median(cls, vectors):
        states = {}
        for v in vectors:
            for kws in v.kwStates():
                if not kws.keyword_ in states:
                    states[kws.keyword_] = []
                states[kws.keyword_].append(kws)
        medianV = []
        for _,s in states.items():
            medianV.append(KeywordState.simpleMedian(s))
        return EmissionVector(medianV)

    @classmethod
    def weightedSum(cls, vectors, weights):
        if len(vectors) <= len(weights):
            weightedVectors = []
            idx = 0
            for v in vectors:
                weightedVectors.append(v * weights[idx])
                idx += 1
            return EmissionVector.sum(weightedVectors)
        else:
            return None

    @classmethod
    def normalize(cls, vector):
        '''Normalizes intensity and sentiment values accross all keywords in
            the vector
        '''
        ilist = [k.intensity_ for k in vector.kwStates()]
        slist = [s.sentiment_ for s in vector.kwStates()]
        edges = {'imax':max(ilist), 'imin': min(ilist), 'smax':max(slist), 'smin':min(slist)}
        normalized = []
        for k in vector.kwStates():
            iN = (k.intensity_ - edges['imin']) / (edges['imax'] - edges['imin'])
            sN = (k.sentiment_ - edges['smin']) / (edges['smax'] - edges['smin'])
            normalized.append(KeywordState(k.keyword_, iN, sN, k.age_))
        return EmissionVector(normalized)

    @classmethod
    def filter(cls, vector, filter, filterBy = Filter.Value.Intensity|Filter.Value.Sentiment):
        normalized = EmissionVector.normalize(vector)
        nBins = 3
        w = 1/float(nBins)
        bins = [[ [] for col in range(nBins)] for row in range(nBins)]
        # iFiltered = {bin: [] for bin in range(0,nBins)}
        # sFiltered = {[] for bin in range(0,nBins)}
        for k in normalized.kwStates():
            for sBin in range(0,nBins):
                leftEdge = w*sBin
                rightEdge = w*(sBin+1) if sBin < nBins-1 else w*(sBin+1)+.1
                if k.sentiment_ >= leftEdge and k.sentiment_ < rightEdge:
                    # sFiltered[bin].append(k)
                    for iBin in range(0,nBins):
                        leftEdge = w*iBin
                        rightEdge = w*(iBin+1) if iBin < nBins-1 else w*(iBin+1)+.1
                        if k.intensity_ >= leftEdge and k.intensity_ < rightEdge:
                            bins[sBin][iBin].append(k)
                # if k.intensity_ >= leftEdge and k.intensity_ < rightEdge:
                #     iFiltered[bin].append(k)

        selectedBins = []
        # for three filter levels, divide by three
        binNumW = float(nBins) / 3.
        if cls.Filter.Level.Low & filter:
            selectedBins.extend(range(0, round(binNumW)))
        if cls.Filter.Level.Medium & filter:
            selectedBins.extend(range(round(binNumW), round(2*binNumW)))
        if cls.Filter.Level.High & filter:
            selectedBins.extend(range(round(2*binNumW), nBins))
        # print(selectedBins)

        filtered = []
        if filterBy&cls.Filter.Value.Sentiment:
            # filtered = [bins[b] for b in selectedBins]
            def filterBin(binIdx): return bins[binIdx] if binIdx in selectedBins else []
            filtered = [filterBin(b) for b in range(nBins)]
        else:
            filtered = bins
        # print(filtered)
        if filter&cls.Filter.Value.Intensity:
            filtered = [filtered[b] for b in selectedBins]
        filteredStates = []
        for rowS in range(0,len(filtered)):
            for colI in range(0,len(filtered[rowS])):
                for k in filtered[rowS][colI]:
                    filteredStates.append(vector.kwStates_[k.keyword_])
        return EmissionVector(filteredStates)


ExposureVector = EmissionVector

class ExperienceState():
    ExperienceIdKey='experience_id'
    ExperienceIdKeyLegacy='exhibit_id'
    ExperienceStateKey='state'

    def __init__(self, dict):
        if not (ExperienceState.ExperienceIdKey in dict and ExperienceState.ExperienceStateKey in dict):
            if ExperienceState.ExperienceIdKeyLegacy in dict:
                self.experienceId_ = dict[ExperienceState.ExperienceIdKeyLegacy]
            else:
                raise ValueError('malformed experience state message: {}'.format(dict))
        if ExperienceState.ExperienceIdKey in dict:
            self.experienceId_ = dict[ExperienceState.ExperienceIdKey]
        self.emissionVector_ = EmissionVector(dict[ExperienceState.ExperienceStateKey])

    def encode(self):
        return { ExperienceState.ExperienceIdKey : self.experienceId_,
                 ExperienceState.ExperienceStateKey : self.emissionVector_.encode()}

    def __repr__(self):
        return repr(self.encode())
