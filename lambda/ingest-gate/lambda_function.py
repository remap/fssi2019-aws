import json
import boto3
import sys
import uuid
import os
from fssi_common import *

def lambda_handler(event, context):
    try:
        print('EVENT ', str(event))
        print('CONTEXT ', str(context))

        requestFileName = event["queryStringParameters"]['name']
        fileName, fileExtension = os.path.splitext(requestFileName)
        uploadKey = 'upload/' + str(uuid.uuid4()) + fileExtension
        s3 = boto3.client('s3')
        presignedUrl = s3.generate_presigned_url('put_object', {'Bucket':FssiResources.S3Bucket.Ingest ,'Key':uploadKey,  'ContentType':'binary/octet-stream'})

        print('GENERATED PRESIGNED URL for ', requestFileName, presignedUrl)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps({
                'uploadUrl': presignedUrl,
                'uploadKey': uploadKey
            })
        }

    except:
        print('caught exception:', sys.exc_info()[0])

    return {
        'statusCode': 404,
        'body': json.dumps('x⸑x')
    }
