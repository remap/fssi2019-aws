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

def testExposureVectorMultiply():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.4,'sentiment':0.4},
                'h5':{'intensity':0.5,'sentiment':0.5},
              }
    ev1 = ExposureVector(vecDict1)
    mul = ev1 * 0.5

    for kws in mul.kwStates():
        iTarget = vecDict1[kws.keyword_]['intensity']
        sTarget = vecDict1[kws.keyword_]['sentiment']
        assert kws.intensity_ * 2 == iTarget, "Unexpected intensity value for {}: {} vs {}".format(kws.keyword_, kws.intensity_, iTarget)
        assert kws.sentiment_ * 2 == iTarget, "Unexpected sentiment value for {}: {} vs {}".format(kws.keyword_, kws.sentiment_, sTarget)

def testExposureVectorSum():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
              }
    vecDict2 = {
                'h1':{'intensity':0.3,'sentiment':-0.5},
                'h4':{'intensity':0.8,'sentiment':0.7},
                'h5':{'intensity':0.1,'sentiment':-0.1},
              }
    vecDict3 = {
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.6,'sentiment':0.55},
                'h5':{'intensity':0.3,'sentiment':0.2},
              }
    target = {
              'h1':{'intensity':0.4,'sentiment':-0.4},
              'h2':{'intensity':0.2,'sentiment':0.2},
              'h3':{'intensity':0.6,'sentiment':0.6},
              'h4':{'intensity':1.4,'sentiment':1.25},
              'h5':{'intensity':0.4,'sentiment':0.1},
              }
    ev1 = ExposureVector(vecDict1)
    ev2 = ExposureVector(vecDict2)
    ev3 = ExposureVector(vecDict3)
    sum = ExposureVector.sum([ev1, ev2, ev3])
    for kws in sum.kwStates():
        iTarget = target[kws.keyword_]['intensity']
        sTarget = target[kws.keyword_]['sentiment']
        assert kws.intensity_ == iTarget, "Unexpected intensity value for {}: {} vs {}".format(kws.keyword_, kws.intensity_, iTarget)
        assert kws.sentiment_ == sTarget, "Unexpected sentiment value for {}: {} vs {}".format(kws.keyword_, kws.sentiment_, sTarget)

def testExposureVectorWeightedMean():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
              }
    vecDict2 = {
                'h1':{'intensity':0.3,'sentiment':-0.5},
                'h4':{'intensity':0.8,'sentiment':0.7},
                'h5':{'intensity':0.1,'sentiment':-0.1},
              }
    vecDict3 = {
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.6,'sentiment':0.55},
                'h5':{'intensity':0.3,'sentiment':0.2},
              }
    target = {
              'h1':{'intensity':0.15,'sentiment':-0.17},
              'h2':{'intensity':0.06,'sentiment':0.06},
              'h3':{'intensity':.09+.09,'sentiment':.09+.09},
              'h4':{'intensity':.32+.18,'sentiment':.28+.165},
              'h5':{'intensity':0.04+.09,'sentiment':-0.04+.06},
              }
    ev1 = ExposureVector(vecDict1)
    ev2 = ExposureVector(vecDict2)
    ev3 = ExposureVector(vecDict3)
    sum = ExposureVector.weightedSum([ev1, ev2, ev3], [0.3, 0.4, 0.3])
    for kws in sum.kwStates():
        iTarget = target[kws.keyword_]['intensity']
        sTarget = target[kws.keyword_]['sentiment']
        assert abs(kws.intensity_ - iTarget) < .0000001, "Unexpected intensity value for {}: {} vs {}".format(kws.keyword_, kws.intensity_, iTarget)
        assert abs(kws.sentiment_ - sTarget) < .0000001, "Unexpected sentiment value for {}: {} vs {}".format(kws.keyword_, kws.sentiment_, sTarget)

def testExposureVectorCulling1():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.03,'sentiment':0.3},
                'h4':{'intensity':0.04,'sentiment':0.4},
                'h5':{'intensity':0.5,'sentiment':0.5},
              }
    ev1 = ExposureVector(vecDict1)
    culled = ev1.cull(0, 0.05)
    assert len(culled.kwStates()) == 3, "Unexpected number of keyword states in Exposure vector: {} vs {}".format(len(culled.kwStates()), 3)

def testExposureVectorCulling2():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.001},
                'h2':{'intensity':0.002,'sentiment':0.2},
                'h3':{'intensity':0.003,'sentiment':0.003},
                'h4':{'intensity':0.04,'sentiment':0.4},
                'h5':{'intensity':0.0005,'sentiment':-0.005},
              }
    ev1 = ExposureVector(vecDict1)
    culled = ev1.cull(0, 0.01, 0.01)
    # print(culled)
    assert len(culled.kwStates()) == 3, "Unexpected number of keyword states in Exposure vector: {} vs {}".format(len(culled.kwStates()), 3)


def testExposureVectorCulling3():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.0002,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
                'h4':{'intensity':0.0004,'sentiment':0.4},
                'h5':{'intensity':0.5,'sentiment':0.5},
              }
    ev1 = ExposureVector(vecDict1)
    culled = ev1.cull(0)
    assert len(culled.kwStates()) == 3, "Unexpected number of keyword states in Exposure vector: {} vs {}".format(len(culled.kwStates()), 3)

def testNormalize():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
              }
    ev = ExposureVector(vecDict1)
    n = ExposureVector.normalize(ev)
    assert n.kwStates_['h1'].intensity_ == 0
    assert n.kwStates_['h1'].sentiment_ == 0
    assert n.kwStates_['h2'].intensity_ - 0.5 < .0000001
    assert n.kwStates_['h2'].sentiment_ - 0.5 < .0000001
    assert n.kwStates_['h3'].intensity_ == 1.
    assert n.kwStates_['h3'].sentiment_ == 1.

def testFiltering():
    vecDict1 = {
                'h1':{'intensity':0.1,'sentiment':0.1},
                'h2':{'intensity':0.2,'sentiment':0.2},
                'h3':{'intensity':0.3,'sentiment':0.3},
              }
    ev = ExposureVector(vecDict1)
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.Low)
    assert len(f.kwStates()) == 1
    assert 'h1' in f.kwStates_
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.Medium)
    assert len(f.kwStates()) == 1
    assert 'h2' in f.kwStates_
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.High)
    assert len(f.kwStates()) == 1
    assert 'h3' in f.kwStates_
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.Medium|ExposureVector.Filter.Level.Low)
    assert len(f.kwStates()) == 2
    assert 'h1' in f.kwStates_ and 'h2' in f.kwStates_
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.Medium|ExposureVector.Filter.Level.High)
    assert len(f.kwStates()) == 2
    assert 'h3' in f.kwStates_ and 'h2' in f.kwStates_
    f = ExposureVector.filter(ev, ExposureVector.Filter.Level.High|ExposureVector.Filter.Level.Low)
    assert len(f.kwStates()) == 2
    assert 'h1' in f.kwStates_ and 'h3' in f.kwStates_

if __name__ == '__main__':
    testKeywordStateCreate()
    testExposureVectorCreate()
    testKeywordStateSimpleAverage()
    testExposureVectorSimpleAverage()
    testExposureVectorMultiply()
    testExposureVectorSum()
    testExposureVectorWeightedMean()
    testExposureVectorCulling1()
    testExposureVectorCulling2()
    testExposureVectorCulling3()
    testNormalize()
    testFiltering()
    print('all passed')
