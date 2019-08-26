# fssi2019-aws
AWS code for FSSI 2019

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

### How to use it in `boto3`

```
sess = boto3.session.Session(profile_name='fssi2019-xacc-resource-access')
snsClient = sess.client('sns')
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
