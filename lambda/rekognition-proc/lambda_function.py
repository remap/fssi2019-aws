import json
import boto3, botocore
import sys, os
from decimal import Decimal
from fssi_common import *

metadataTable = dynamoDbResource.Table(FssiResources.DynamoDB.MediaRekognitionMeta)
rekognitionClient = boto3.client('rekognition')

################################################################################
## S3 Object Processing Here
def wasItemProcessed(objectKey):
    response = metadataTable.get_item(Key = {'id' : objectKey})
    return 'Item' in response

def processObject(objectKey, s3BucketName, s3BucketArn):
    mimeType = guessMimeTypeFromExt(objectKey)

    if not mimeType:
        print('couldn\'t derive MIME type from extension')
        fName = downloadFile(objectKey, s3BucketName)
        mimeType = guessMimeTypeFromFile(fName)

    if 'image' in mimeType:
       # do stuff
       if not wasItemProcessed(objectKey):
           labels = rekognitionClient.detect_labels(Image={'S3Object' : {'Bucket': s3BucketName, 'Name':objectKey}})
           mediaMetadata = makeMediaMetaItem(objectKey, s3BucketName)
           mediaMetadata['meta'] = { 'rekognition': labels }
           ddbData = json.loads(json.dumps(mediaMetadata), parse_float=Decimal)
           metadataTable.put_item(Item = ddbData, ConditionExpression='attribute_not_exists(id)')
       else:
           print('item {} was already processed'.format(objectKey))
       return

    print('no processing for item {}'.format(objectKey))
    return

################################################################################
## Lambda Handler
def lambda_handler(event, context):
    try:
        if not 'Records' in event:
            # assume direct invocation
            if 'items' in event:
                print('batch processing for {} items'.format(len(event['items'])))
                # batch processing
                for item in event['items']:
                    bucketArn = item['bucketArn'] if 'bucketArn' in item else None
                    processObject(item['objectKey'], item['bucket'], bucketArn)
            else:
                # one record invocation
                objectKey = event['objectKey']
                bucket = event['bucket']
                bucketArn = event['bucketArn'] if 'bucketArn' in event else None
                print('direct invocation for object {} from bucket {}'.format(objectKey, bucket))
                processObject(objectKey, bucket, bucketArn)
        else:
            for record in event['Records']:
                if record['EventSource'] != 'aws:sns':
                    return lambdaReply(420, 'received non-SNS event record: {}'.format(record))

                snsRecord = record['Sns']
                messageDict = json.loads(snsRecord['Message'])
                for snsRecord in messageDict['Records']:
                    if snsRecord['eventName'] == 'ObjectCreated:Put':
                        s3BucketName = snsRecord['s3']['bucket']['name']
                        s3BucketArn =  snsRecord['s3']['bucket']['arn']
                        objectKey = snsRecord['s3']['object']['key']

                        print('new item {} added to bucket {} ({})'.format(objectKey, s3BucketName, s3BucketArn))
                        processObject(objectKey, s3BucketName, s3BucketArn)
                    else:
                        lambdaReply(420, 'SNS event type not supported: {}'.format(snsRecord['eventName']))
    except:
        err = reportError()
        print('caught exception:', sys.exc_info()[0])
        return lambdaReply(420, str(err))

    return processedReply()

# for testing, run locally "python lambda_function.py"
if __name__ == '__main__':
    sampleSnsEvent = {
                        'Records':[
                        {
                            'EventSource':'aws:sns',
                            'EventVersion':'1.0',
                            'EventSubscriptionArn':'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload:7e9d0542-bdae-4ec9-a114-d73be62f9a28',
                            'Sns':{
                                'Type':'Notification',
                                'MessageId':'105a42d1-a4a5-5adf-a620-173bb838d5a7',
                                'TopicArn':'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload',
                                'Subject':'Amazon S3 Notification',
                                'Message':'{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-west-1","eventTime":"2019-09-04T20:11:09.660Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AROA3AHVLAHEOUASVZXIH:fssi2019-lambda-ingest-gate"},"requestParameters":{"sourceIPAddress":"131.179.142.121"},"responseElements":{"x-amz-request-id":"497AD45555DD0057","x-amz-id-2":"eyiMv7GzyjS7azmBORnShRuyUIxUVBLzQitguWVagDn8obtQqgtJ1PsMPxlCYvU2MmiXPYccxcE="},"s3":{"s3SchemaVersion":"1.0","configurationId":"Ingest Upload","bucket":{"name":"fssi2019-s3-ingest","ownerIdentity":{"principalId":"A2IYG3741R477C"},"arn":"arn:aws:s3:::fssi2019-s3-ingest"},"object":{"key":"upload/bfe82b36-f70d-4702-bc0f-65c8079d389a.jpg","size":466,"eTag":"bdf430c4b4bbdd37886b0de2a4b87107","sequencer":"005D701A5D9658C51B"}}}]}',
                                'Timestamp':'2019-09-04T20:11:09.920Z',
                                'SignatureVersion':'1',
                                'Signature':'evgodY/lwnQ7Luw4XrUWdBsOim6Ufe6DAIAN7fdwOU5Ao8BT8XQ2D4y+6Kq9Ja1GQTJnZE1vwlw1MLqCLXFDzWnbJvko98rZBdgzrm+N8MW/Jp+0gQfjZOWnMvHu98sJyZPGuz7foE3hFT3FCUlsieVbRSK6PD9MMqya5PGYnjXUfQKb80TnBu/58hRmY0R+aVbskqraPdnIB0Z9ZcCm1neRkJ1u/CcDY6w1ENxWZokh8/jt3b9dJ9UjP92U/tlmrAV4nlw+h9GbXpfTS+k7aa+pZoQ1NFgcJ3ETkBpEMY5Vsc4DFaHFuJGhFvsjfSUHmMHUgroEC5d8z8yV/2wbNg==',
                                'SigningCertUrl':'https://sns.us-west-1.amazonaws.com/SimpleNotificationService-6aad65c2f9911b05cd53efda11f913f9.pem',
                                'UnsubscribeUrl':'https://sns.us-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload:7e9d0542-bdae-4ec9-a114-d73be62f9a28',
                                'MessageAttributes':{}
                                }
                        }]
                    }
    lambda_handler(sampleSnsEvent, None)
