import json
import boto3
import sys
import uuid
import os

def lambda_handler(event, context):
    print("lambda exposure is at work!!!")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
