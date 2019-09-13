# Emission Vector Simulator
# 9/10/2019 jburke@ucla.edu
#

# Dependencies
# pip3 install nltk
#
#
from fssi_common import *
import random, time, json
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet

import boto3
import sys,traceback

profileName = 'fssi2019-participant'
session = boto3.session.Session(profile_name=profileName)
snsClient = session.client('sns')
snsTopicName = 'fssi2019-sns-emission'

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


class EvolvingRandomTag:

	MAX_LIFETIME = 10
	MAX_STEP_INTENSITY = 0.04
	MAX_STEP_SENTIMENT = 0.04

	def __init__(self):
		self.tag = random.sample(list(wordnet.words()),1)[0]
		self.intensity = random.random()
		self.sentiment = random.random()*2 - 1
		self.lifetimesecs = random.random() * (EvolvingRandomTag.MAX_LIFETIME-1) + 1
		self.ttl = self.lifetimesecs
		self.t_start = time.time()
		self.t_last = self.t_start
		self.intensitystep = EvolvingRandomTag.MAX_STEP_INTENSITY  # max step per second
		self.sentimentstep = EvolvingRandomTag.MAX_STEP_SENTIMENT

	def _randsign(self):
		return 1 if random.random() < 0.5 else -1

	def evolve(self):
		now = time.time()
		newsecs = now - self.t_last
		self.t_last= now
		self.ttl = max(self.lifetimesecs - (now - self.t_start), 0)
		self.intensity = min(max(self.intensity + self._randsign() * random.random() * self.intensitystep * newsecs, 0), 1)
		self.sentiment = min(max(self.sentiment + self._randsign() * random.random() * self.sentimentstep * newsecs, -1), 1)

	def __str__(self):
		return "#%s : %0.2f | %0.2f ttl %0.3f" % (self.tag, self.intensity, self.sentiment, self.ttl)

	def toJSONcompact(self):
		return json.dumps({"keyword": self.tag, "intensity": self.intensity, "sentiment": self.sentiment})

if __name__ == "__main__":

	bag = []

	while(True):

		if len(bag) < 10:
			for k in range(0, random.randint(0,3)):
				bag.append(EvolvingRandomTag())

		D = []
		for tag in bag:
			tag.evolve()
			if tag.ttl==0: D.append(tag)

		for tag in D:
			bag.remove(tag)

#		bag.sort(key = lambda t: t.tag)
#		for tag in bag:
#			print(tag)
#		print()
#
		emission = { "experience_id" : "tactile" ,	 "state": {}, "t" : time.time() }
		for tag in bag:
			kws = KeywordState(tag.tag, tag.intensity, tag.sentiment)
			emission['state'][tag.tag] = kws.encode()
			# emission['state'][tag.tag].append(tag.intensity)
			# emission['state'][tag.tag].append(tag.sentiment)
		print(json.dumps(emission, sort_keys=True, indent=4))

		try:
			print("Published to %s:" % snsTopicName, publishSns(json.dumps(emission))['MessageId'])
		except:
			print('exception while publishing SNS', sys.exc_info()[0])
			traceback.print_exc(file=sys.stdout)
		print()
		time.sleep(1)
