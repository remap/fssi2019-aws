import json
import boto3
import sys
import uuid
import os
from fssi_common import ACCESS_KEY, SECRET_KEY, SESSION_TOKEN

def lambda_handler(event, context):
    dynamoDbClient = boto3.client(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )

    print(dynamoDbClient.list_tables())

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
