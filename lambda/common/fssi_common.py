import boto3

CROSS_ACCT_ACCESS_ROLE = "arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access"

stsConnection = boto3.client('sts')
acctB = stsConnection.assume_role(
    RoleArn=CROSS_ACCT_ACCESS_ROLE,
    RoleSessionName="cross_acct_lambda"
)

ACCESS_KEY = acctB['Credentials']['AccessKeyId']
SECRET_KEY = acctB['Credentials']['SecretAccessKey']
SESSION_TOKEN = acctB['Credentials']['SessionToken']
