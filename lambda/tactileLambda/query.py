import requests
import json
import math
import random

queryUrl = 'https://search-fssi2019-elasticsearch-stage-dk3gt2igpfx3nl7kkl6l6sppay.us-west-1.es.amazonaws.com/image/_search'
queryPageSize = 50
queryPageFrom = 0
limitHits = 50
url = queryUrl

class ElasticSearchFields:
    class UserTags:
        UserTagsMeta = "meta.userTags"
        Keyword = UserTagsMeta+".keyword"
        Intensity = UserTagsMeta+".intensity"
        Sentiment = UserTagsMeta+".sentiment"

    class Rekognition:
        RekognitionMeta = "meta.rekognition"
        Labels = RekognitionMeta+".Labels"
        LabelName = Labels+".Name"
        LabelConfidence = Labels+".Confidence"

def boolMatchClause(field, match):
    return { "match": { field : match } }

def boolRangeClause(field, rangeMin, rangeMax):
    return { "range": { field : { "gte": rangeMin, "lte": rangeMax }}}

def keywordRangeClause(kwField, confField, keyword, confMin, confMax):
    return { "must" : [
        boolMatchClause(kwField, keyword),
        boolRangeClause(confField, confMin, confMax)
    ]}

def rekognitionNestedQuery(keyword, confMin, confMax):
    return {
        "nested" : {
            "path": "meta.rekognition.Labels",
            "query" : {
                "bool" : keywordRangeClause(ElasticSearchFields.Rekognition.LabelName,
                                            ElasticSearchFields.Rekognition.LabelConfidence,
                                            keyword, confMin, confMax)
            }
        }
    }

def rekognitionQuery(queryList, queryType = 'must'):
    q = {
        "_source": ["objectUrl", ElasticSearchFields.Rekognition.LabelName, ElasticSearchFields.Rekognition.LabelConfidence],
        "query": {
            "bool" : {
                queryType : []
            }
        }
    }

    for item in queryList:
        kw = item['keyword']
        confMin = item['confidence_min']
        confMax = item['confidence_max']
        q["query"]["bool"][queryType].append(rekognitionNestedQuery(kw, confMin, confMax))
    return q

def runQuery(session,query,pageSize = queryPageSize, pageFrom = queryPageFrom):
    response=session.post(url, data=json.dumps(query), params={'size':pageSize, 'from':pageFrom})
    if response.ok:
        results=json.loads(response.text)
        totalHits = results['hits']['total']['value']
        if pageFrom == 0:
            if totalHits > pageSize:
                # need to paginate
                print('retrieving all results...')
                queryHits = totalHits if totalHits < limitHits else limitHits
                morePages = math.floor(queryHits/pageSize)
                pageHits = []
                for startFrom in list(range(pageSize, queryHits, pageSize)):
                    print('querying results [{}-{})'.format(startFrom, startFrom+pageSize))
                    pageRes = runQuery(pageSize, startFrom)
                    if len(pageRes):
                        pageHits.extend(pageRes['hits']['hits'])
                results['hits']['hits'].extend(pageHits)

            print('total results {}. retrieved {}'.format(totalHits, len(results['hits']['hits'])))
            print('total search results:', totalHits)
    else:
        print('request failed. code {}: {}'.format(response.status_code, response.text))
        results = {}
    return results

def parseResult(invokeResult):
    idx = 0
    results = invokeResult
    toReturn = []
    for hit in results['hits']['hits']:
        objectUrl = hit['_source']['objectUrl']
        labels = hit['_source']['meta']['rekognition']['Labels']
        label_list = []
        for l in labels:
            label_list.append([l['Name'],l['Confidence']])
        idx += 1
        toReturn.append([objectUrl, label_list])
    return toReturn

################################################################################
##

def tagQuery(argument):

    session=requests.Session()
    session.headers={"content-type": "application/json"}

    #queryDat = op('query')
    queryList = [{'keyword': argument, 'confidence_min': 50, 'confidence_max': 100}]

    #queryType = 'should' if me.parent().par.Findany == 1 else 'must'
    queryType = 'should'
    query=rekognitionQuery(queryList, queryType)
    debug_query = json.dumps(query, indent=4)

    results = runQuery(session,query)
    return parseResult(results)

'''
session=requests.Session()
session.headers={"content-type": "application/json"}

#queryDat = op('query')
queryList = [{'keyword': 'light', 'confidence_min': 90, 'confidence_max': 100}]

#queryType = 'should' if me.parent().par.Findany == 1 else 'must'
queryType = 'must'
query=rekognitionQuery(queryList, queryType)
debug_query = json.dumps(query, indent=4)

results = runQuery(session,query)
tags = []
parsed = parseResult(results)

print(parsed)
#tags = set([j[0][0] for j in [i[1] for i in parsed]])
#print(tags)
'''


