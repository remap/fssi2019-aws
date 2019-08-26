# fssi2019-aws
AWS code for FSSI 2019

## AWS CLI Set up

> Dont' forget to [create an administrator user](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html) and use its' creadentials in `aws configure`.

```
git clone https://github.com/remap/fssi2019-aws.git && cd fssi2019-aws
virtualenv -p python3 env && source env/bin/activate
pip install awscli boto3
complete -C aws_completer aws jq
aws configure
```

> This will be your AWS development environment. Every time you open new terminal window, you need to activate it by `cd`-ing into "fssi2019-aws" folder and running `source env/bin/activate`.

## Cross Account Inter-Organization Access

To set up cross account inter-organization access:

1. Make sure you use *non-root user*

    * [Create admin user](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html).
    * You'll need to run `aws configure` again to set up access keys for that user.

2. Assume role `arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access`

    * Add this to your `~/.aws/credentials` file:
    ```
    [fssi2019-xacc-resource-access]
    role_arn = arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access
    source_profile = default
    region = us-west-1
    ```

3. Test access by explicitly specifying profile in AWS CLI:

    * Lists all SNS topics `aws sns --profile=fssi2019-xacc-resource-access list-topics`
    * Lists all DynamoDB tables `aws dynamodb --profile=fssi2019-xacc-resource-access list-tables`

### How to use it in `boto3` locally

```
sess = boto3.session.Session(profile_name='fssi2019-xacc-resource-access')
snsClient = sess.client('sns')
```

### How to use it in AWS Console

1. Follow this [link](https://signin.aws.amazon.com/switchrole?account=756428767688&roleName=fssi2019-xacc-intraorg-resource-access&displayName=fssi2019-xaccount-access)
2. Press "Switch Role"
3. Now your user assumed role for cross-account access, try checking your DynanoDB tables list.

### How to use it in AWS Lambda

> (from [here](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-function-assume-iam-role/))

1. [Create this Policy](https://console.aws.amazon.com/iam/home#/policies) named `fssi2019-iam-policy-xacc-intraorg-resource-access`:

```
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access"
    }
}
```

2. Attach created policy to the lambda execution role that needs to assume the role (cross-account access)

	1. Go to Services -> IAM -> Roles -> _open your lambda function role_
	2. Attach policy created above

3. To access DynamoDB tables, you need to create a session that assumes the role:
```
    stsConnection = boto3.client('sts')
    acctB = stsConnection.assume_role(
        RoleArn="arn:aws:iam::756428767688:role/fssi2019-xacc-intraorg-resource-access",
        RoleSessionName="cross_acct_lambda"
    )
    ACCESS_KEY = acctB['Credentials']['AccessKeyId']
    SECRET_KEY = acctB['Credentials']['SecretAccessKey']
    SESSION_TOKEN = acctB['Credentials']['SessionToken']

    dynamoDbClient = boto3.client(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN
    )

    print(dynamoDbClient.list_tables())
```

## AWS Resources List
### SNS Topics

```
aws sns --profile=fssi2019-xacc-resource-access list-topics
```

### DynamoDB Tables

```
aws dynamodb --profile=fssi2019-xacc-resource-access list-tables
```

> See details in this [document](https://docs.google.com/document/d/1wBYp_Km6t0anTLR-IaE3tMVg98PQwaTPjN4ejN95htg/edit#).
