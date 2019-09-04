# ElasticSearch Sync Lambda

This lambda is subscribed for [DynamoDB SNS updates](https://github.com/remap/fssi2019-aws/tree/master/lambda/dynamodb-listener) and performs necessary updates with ElasticSearch engine.

## AWS Resource

* Name: `fssi2019-lambda-elasticsearch-sync`
* ARN: `arn:aws:lambda:us-west-1:756428767688:function:fssi2019-lambda-elasticsearch-sync`

### Trigger


* SNS Topic: `fssi2019-sns-dynamodb-updates`
* SNS ARN: `arn:aws:sns:us-west-1:756428767688:fssi2019-sns-dynamodb-updates`
* SNS Subscription ARN: `arn:aws:sns:us-west-1:756428767688:fssi2019-sns-dynamodb-updates:fe494d9c-3880-4bd5-a6ca-db0f80692a6b`


### Input Format

See [DynamoDB Stream listener lambda](https://github.com/remap/fssi2019-aws/tree/master/lambda/dynamodb-listener#processing) for details on the SNS message format.



## Processing
On trigger:

_TBD_
