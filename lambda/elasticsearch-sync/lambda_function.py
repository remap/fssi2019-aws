import json
import boto3
import sys
from fssi_common import *

def lambda_handler(event, context):
    try:
        print('SNS EVENT ', str(event))

        for record in event['Records']:
            snsRecord = record['Sns']
            messageDict = json.loads(snsRecord['Message'])

            table = messageDict['table']
            event = messageDict['event']
            itemId = messageDict['itemId']
            itemData = messageDict['itemData']

            print('DynamoDB event {} for table {}, item {}: {}'.format(event, table, itemId, itemData))
    except:
        err = reportError()
        print('caught exception:', sys.exc_info()[0])

    return processedReply()

if __name__ == '__main__':
    sampleEvent = {
                    'Records':[{
                                'Sns':{
                                    'Message' : '{\"table\": \"fssi2019-dynamodb-media-user-meta\", \"event\": \"REMOVE\", \"itemId\": \"testid2\", \"itemData\": {\"key1\": {\"S\": \"value1\"}, \"key2\": {\"S\": \"value2\\n\"}, \"key3\": {\"N\": \"0.1\"}, \"id\": {\"S\": \"testid2\"}}}'
                                    }
                                }]
                  }
    lambda_handler(sampleEvent, None)
