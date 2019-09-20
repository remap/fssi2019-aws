import requests
import json

queryUrl = 'https://search-fssi2019-elasticsearch-stage-dk3gt2igpfx3nl7kkl6l6sppay.us-west-1.es.amazonaws.com/image/_search'
queryPageSize = 20
queryPageFrom = 0
limitHits = me.parent().par.Limitresults.eval()
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

def runQuery(pageSize = queryPageSize, pageFrom = queryPageFrom):
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
    if invokeResult['result'] == 'ok':
        idx = 0
        results = invokeResult['return_value']
        for hit in results['hits']['hits']:
            objectUrl = hit['_source']['objectUrl']
            labels = hit['_source']['meta']['rekognition']['Labels']
            label_list = []
            for l in labels:
                label_list.append([l['Name'],l['Confidence']])
            op('hits').appendRow([objectUrl, label_list])
            idx += 1
    op('constant1').par.value0 = 0

################################################################################
##
session=requests.Session()
session.headers={"content-type": "application/json"}

queryDat = op('query')
queryList = []
for r in queryDat.rows():
    kw = r[0].val
    confMin = r[1].val
    confMax = r[2].val
    queryList.append({'keyword': kw, 'confidence_min': confMin, 'confidence_max': confMax})

queryType = 'should' if me.parent().par.Findany == 1 else 'must'
query=rekognitionQuery(queryList, queryType)

op('debug_query').text = json.dumps(query, indent=4)

print('invoke search...')
op('constant1').par.value0 = 1
mod.td_utils.runAsync(me, runQuery, parseResult)
