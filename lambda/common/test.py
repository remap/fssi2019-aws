from fssi_common import *

def testKeywordStateCreate():
    kws = KeywordState('test', 0.2, 0.5)
    assert kws.intensity_ == 0.2, "KWS intensity check failed"
    assert kws.sentiment_ == 0.5, "KWS sentiment check failed"
    assert kws.keyword_ == 'test', "KWS keyword check failed"

    kws = KeywordState('test', {'intensity':0.4, 'sentiment':-0.4})
    assert kws.intensity_ == 0.4, "KWS intensity check failed"
    assert kws.sentiment_ == -0.4, "KWS sentiment check failed"
    assert kws.keyword_ == 'test', "KWS keyword check failed"

    kws2 = KeywordState(kws)
    assert kws2.intensity_ == 0.4, "KWS intensity check failed"
    assert kws2.sentiment_ == -0.4, "KWS sentiment check failed"
    assert kws2.keyword_ == 'test', "KWS keyword check failed"

    try:
        kws = KeywordState()
        assert False, "Constructor with no arguments should fail"
    except TypeError:
        pass

    try:
        kws = KeywordState('blah', {})
        assert kws.intensity_ == 0., "KWS intensity check failed"
        assert kws.sentiment_ == 1., "KWS sentiment check failed"
    except:
        assert False, "Should intialize with default intensity and sentiment"

def testExposureVectorCreate():
    vecDict = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.4,'sentiment':0.4},
                'h5':{'intensity':0.5,'sentiment':0.5},
              }
    ev = ExposureVector(vecDict)
    assert len(ev.items()) == 5, "Error in parsing dictionary"
    idx = 1
    hashtags = list(vecDict.keys())
    for kw, kws in ev.items():
        assert kws.keyword_ in hashtags, "Error parsing dictionary"

    ev = ExposureVector([
        KeywordState(hashtags[0], vecDict[hashtags[0]]),
        KeywordState(hashtags[1], vecDict[hashtags[1]]),
        KeywordState(hashtags[2], vecDict[hashtags[2]]),
        ])
    for kw, kws in ev.items():
        assert kws.keyword_ in hashtags, "Error parsing dictionary"

    ev2 = ExposureVector(ev)
    for kw, kws in ev2.items():
        assert kws.keyword_ in hashtags, "Error parsing dictionary"

def testKeywordStateSimpleAverage():
    hashtags = { 'tag1' : {
                            'avg' : [0.3, 0.08],
                            'params': [
                                        [0.1, 0.1],
                                        [0.2, -0.1],
                                        [0.3, 0.3],
                                        [0.4, 0.3],
                                        [0.5, -0.2]
                                      ]
                            },
                  'tag2' : {
                                          'avg' : [.575, 0.],
                                          'params': [
                                                      [0.8, 0.1],
                                                      [0.6, -0.1],
                                                      [0.2, -0.3],
                                                      [0.7, 0.3],
                                                    ]
                                          },
                  'tag3' : {
                                          'avg' : [0.112, -0.08],
                                          'params': [
                                                      [0.01, -0.1],
                                                      [0.2, -0.1],
                                                      [0.1, -0.3],
                                                      [0.15, 0.3],
                                                      [0.1, -0.2]
                                                    ]
                                          },
                }
    kwsList = []
    for k,v in hashtags.items():
        keyword = k
        # targetAvg = v['avg']
        for params in v['params']:
            intensity = params[0]
            sentiment = params[1]
            kwsList.append(KeywordState(keyword, intensity, sentiment))
    avgList = KeywordState.simpleAverage(kwsList)
    assert len(avgList) == len(hashtags), "Should be only {} KWSs after averaging".format(len(hashtags))
    for kws in avgList:
        assert kws.keyword_ in list(hashtags.keys()), "Unexpected keyword after averaging: {}".format(kws.keyword_)
        iTarget = hashtags[kws.keyword_]['avg'][0]
        sTarget = hashtags[kws.keyword_]['avg'][1]
        assert abs(kws.intensity_ - iTarget) < 0.0001, "Unexpected average intensity value for {}: {} vs {}".format(kws.keyword_, kws.intensity_, iTarget)
        assert abs(kws.sentiment_ - sTarget) < 0.0001, "Unexpected average sentiment value for {}: {} vs {}".format(kws.keyword_, kws.sentiment_, sTarget)

def testExposureVectorSimpleAverage():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.4,'sentiment':0.4},
                'h5':{'intensity':0.5,'sentiment':0.5},
              }
    vecDict2 = {
                'h1':{'intensity':0.3,'sentiment':-0.5},
                'h4':{'intensity':0.8,'sentiment':0.7},
                'h5':{'intensity':0.1,'sentiment':-0.1},
              }
    vecDictAvg = {
                'h1':{'intensity':0.2,'sentiment':-0.2},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.6,'sentiment':0.55},
                'h5':{'intensity':0.3,'sentiment':0.2},
              }
    ev1 = ExposureVector(vecDict1)
    ev2 = ExposureVector(vecDict2)
    evAvg = ExposureVector.simpleAverage([ev1, ev2])

    for kws in evAvg.kwStates():
        assert kws.keyword_ in list(vecDictAvg.keys()), "Unexpected KWS keyword {}".format(kws.keyword_)
        iTarget = vecDictAvg[kws.keyword_]['intensity']
        sTarget = vecDictAvg[kws.keyword_]['sentiment']
        assert abs(kws.intensity_ - iTarget) < 0.0001, "Unexpected average intensity value for {}: {} vs {}".format(kws.keyword_, kws.intensity_, iTarget)
        assert abs(kws.sentiment_ - sTarget) < 0.0001, "Unexpected average sentiment value for {}: {} vs {}".format(kws.keyword_, kws.sentiment_, sTarget)

if __name__ == '__main__':
    testKeywordStateCreate()
    testExposureVectorCreate()
    testKeywordStateSimpleAverage()
    testExposureVectorSimpleAverage()
    print('all passed')
