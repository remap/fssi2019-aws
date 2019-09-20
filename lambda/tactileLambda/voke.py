import boto3, json

session = boto3.session.Session(profile_name='fssi2019-xacc-resource-access')

client = session.client('lambda')

payload = {
    'lane': 'text', # can be one of: image, text
    'occupants': ['alice', 'bob'],
    'temperature': -1  # 3 to 9, 3 is coherent but boring, 9 is crazy but interesting
}

response = client.invoke(FunctionName = 'tactile', Payload=json.dumps(payload).encode('utf-8'))
print(response['Payload'].read().decode("utf-8").replace('\\n','\n'))