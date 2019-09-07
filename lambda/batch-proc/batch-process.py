"""
batch-process.py

Iterates over items in S3 bucket and invokes a lambda function for it.

Usage:
    batch-process.py <bucket_name> <lambda_name> [--batch_size=<batch_size>] [--filter=<filter>] [--no-pause]

Arguments:
    <bucket_name>               S3 bucket name
    <lambda_name>               Lambda to be invoked for each item.

Options:
    --filter=<filter>           Prefix filter applied to items. Only items that pass this
                                filter will be processed [default: ].
    --batch_size=<batch_size>   Number of items to collect before invoking lambda [default: 1].
    --no-pause                  Disables interactive mode (when script pauses after every <batch_size> items).
Examples:
    python bucket-batch-process.py fssi2019-s3-ingest upload/* fssi2019-lambda-media-rekognition-proc
"""

import json
import boto3
import sys, os, traceback
from decimal import Decimal
from fssi_common import *
from docopt import docopt
import re
import time

def processItem(item):
    print('processing item {}'.format(item))

def iterateBucketItems(bucket, prefix):
    """
    Generator that iterates over all objects in a given s3 bucket

    See http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.list_objects_v2
    for return data format
    :param bucket: name of s3 bucket
    :return: dict of metadata for an object
    """

    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects_v2')
    if prefix != '':
        pageIterator = paginator.paginate(**{'Bucket':bucket, 'Prefix':prefix})
    else:
        pageIterator = paginator.paginate(Bucket=bucket)

    for page in pageIterator:
        if page['KeyCount'] > 0:
            for item in page['Contents']:
                yield item

def iterateBucket(bucketName, lambdaName, prefixFilter, batchSize, noPause):
    batch = []
    try:
        nIter = 0
        nItems = 0
        nItemsProcessed = 0
        runTime = []
        lambdaClient = boto3.client('lambda')
        for item in iterateBucketItems(bucketName, prefixFilter):
            nItems += 1
            mimeType = guessMimeTypeFromExt(item['Key'])
            if mimeType and 'image' in mimeType:
                batch.append({'bucket': bucketName, 'objectKey': item['Key']})
            if len(batch) >= batchSize:
                print('gathered {} items. will invoke lambda now'.format(len(batch)))
                # print(batch)
                start = time.time()
                # res = {'ResponseMetadata' : {'HTTPStatusCode': 200}}
                # print('invoke lambda')
                payload = json.dumps({'items': batch})
                print('payload size', len(payload))
                res = lambdaClient.invoke(FunctionName=lambdaName, Payload=payload)
                runTime.append(time.time() - start)
                statusCode = res['ResponseMetadata']['HTTPStatusCode']
                print('lambda returned code {}'.format(statusCode))
                nItemsProcessed += len(batch)
                nIter += 1
                batch = []
                if not noPause:
                    reply = input('continue? [Y/n]')
                    if reply in ['n', 'N']:
                        break

        print('items iterated {}, processed {}. avg processing time {:.2f}ms, '
              'total processing time {:.4f}sec'.format(nItems, nItemsProcessed,
              sum(runTime)/len(runTime)*1000., sum(runTime)))
    except:
        type, err, tb = sys.exc_info()
        print('caught exception:', err)
        traceback.print_exc(file=sys.stdout)

if __name__ == '__main__':
    options = docopt(__doc__, version='0.0.1')
    # print(options)
    bucketName = options['<bucket_name>']
    lambdaName = options['<lambda_name>']
    prefixFilter = options['--filter']
    batchSize = options['--batch_size']

    print('running batch process for bucket {} (filter {}). will invoke lambda '
          '{} for every {} record(s)'.format(bucketName, prefixFilter, lambdaName, batchSize))

    iterateBucket(bucketName, lambdaName, prefixFilter, int(batchSize), options['--no-pause'])


def iterate_bucket_items(bucket):
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)
    for page in page_iterator:
        if page['KeyCount'] > 0:
            for item in page['Contents']:
                yield item
