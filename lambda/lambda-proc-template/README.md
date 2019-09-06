# Media Processing Lambda Template

This is a boilerplate code for media processing lambdas.

Media processing lambdas used for processing media, ingested into S3 bucket. The code is set up to take S3 SNS topic notifications (or custom direct invocation data) as input. One may subscribe to multiple S3 SNS topics. Each media processing lambda writes processing metadata into a dedicated DynamoDB table, which must be set up with DynamoDB Stream and hooked up with `fssi2019-lambda-dynamodb-stream-listener` lambda (see [below how](#create-media-metadata-table)).

## AWS Resource

* Name: `<pick a name from the list below>`

### Triggers

#### User Media Ingest
* SNS Topic: `fssi2019-sns-ingest-upload`
* SNS ARN: `arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload`

#### Custom Ingest

If you have your own S3 bucket, you should set it up to pose a SNS notification which you can subscribe your lambda to (see [below how](#Setup-S3-Bucket-to-Post-SNS-notifications)).

#### Direct Invocation

You may want to invoke lambda function directly to process already existing object. To do that, you'll need to invoke lambda like this (see the format for `myPayload` [below](#custom)):

```
import boto3
lambdaClient = boto3.client('lambda')
lambdaClient.invoke(FunctionName='lambda-name', Payload=json.dumps(myPayload))
```

### Input Format

#### S3 SNS
The lambda expects *SNS S3 notification* dictionary placed as a string in the "Message" field of SNS notification. The format of the input can be found in the [source code](https://github.com/remap/fssi2019-aws/blob/master/lambda/lambda-proc-template/lambda_function.py#L54).

#### Custom
If lambda can not find SNS notifications in the event records, it will assume direct invocation and expect event payload with the following format (for one record):

```
{
  "bucket": <bucket-name>,
  "bucketArn": <bucket-arn>, // optional
  "objectKey": <object-key>
}
```

Or batch processing format:

```
{
    "items": [{
        "bucket": <bucket-name>,
        "bucketArn": <bucket-arn>, // optional
        "objectKey": <object-key>
    }, ...]
}
```

## Processing

To implement your lambda, add code to the [processObject](https://github.com/remap/fssi2019-aws/blob/master/lambda/lambda-proc-template/lambda_function.py#L8) function for processing S3 objects.
Processing results must be written into a *media metadata table* (one must ensure that the table is created, see [below how](#Create-Media-Metadata-Table)).

### Media Metadata Tables

Media metadata table is a DynamoDB table that has the following keys:

* `id` -- S3 object key;
* `bucket` -- S3 bucket name;
* `created` -- date when item was created;
* `meta` -- service-specific metadata.

`fssi_common.py` has [helper function](https://github.com/remap/fssi2019-aws/blob/master/lambda/common/fssi_common.py#L128) to quickly instantiate dictionary for a new item. One can use it as:

```
...
newItem = makeMediaMetaItem(objectKey, bucketName)
newItem['meta'] = {<processing results>}
...
```

The format of the `meta` is not enforced. At least for right now. But make sure to save all the information that might be helpful for retrieving media (this metadata is also ingested into ElasticSearch).

#### Table Names

Here is the proposed list of media metadata table names (and their Python constants from [fssi_common.py](https://github.com/remap/fssi2019-aws/blob/master/lambda/common/fssi_common.py#L66)):

* User-supplied metadata (through [Ingestion Web UI](https://github.com/remap/fssi2019-aws/tree/master/s3/ingest-web)):
    * `fssi2019-dynamodb-media-user-meta`
    * `FssiResources.DynamoDB.MediaUserMeta`
* File-based metadata (extracted from uploaded file, e.g. EXIF for images):
    * `fssi2019-dynamodb-media-file-meta`
    * `FssiResources.DynamoDB.MediaFileMeta`
* AWS Transcribe metadata:
    * `fssi2019-dynamodb-media-transcribe-meta`
    * `FssiResources.DynamoDB.MediaTranscribeMeta`
* AWS Comprehend metadata:
    * `fssi2019-dynamodb-media-comprehend-meta`
    * `FssiResources.DynamoDB.MediaComprehendMeta`
* AWS Rekognition metadata:
    * `fssi2019-dynamodb-media-rekognition-meta`
    * `FssiResources.DynamoDB.MediaRekognitionMeta`

### Lambda Names

Here is the proposed list of lambdas (and Python constants from [fssi_common.py](https://github.com/remap/fssi2019-aws/blob/master/lambda/common/fssi_common.py#L80)):

* File-based metata processing:
    * `fssi2019-lambda-media-file-proc`
    * `FssiResources.Lambda.FileProc`
* AWS Transcribe processing:
    * `fssi2019-lambda-media-transcribe-proc`
    * `FssiResources.Lambda.TranscribeProc`
* AWS Comprehend processing:
    * `fssi2019-lambda-media-comprehend-proc`
    * `FssiResources.Lambda.ComprehendProc`
* AWS Rekognition processing:
    * `fssi2019-lambda-media-rekognition-proc`
    * `FssiResources.Lambda.RekognitionProc`

## Setup S3 Bucket to Post SNS notifications

More information [here](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/enable-event-notifications.html).

Two-step process:

1. Update topic access policy (using Web Console).

    :point_right: add this dictionary into "Statement" list (replace `SNS-ARN` and `S3-ARN` with real values accordingly):
    ```
        {
            "Sid": "s3-bucket-pubblish",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "SNS:Publish",
            "Resource": "<SNS-ARN>",
            "Condition": {
                "ArnLike": {
                    "aws:SourceArn": "<S3-ARN>"
                }
            }
        }
    ```
2. Configure S3 Bucket to post notifications to SNS topic:

    :point_right: go to "Properties" tab of the Bucket, enable "Event Notifications"

    :point_right: select "All object create events"

    :point_right: choose SNS topic and save

:blush: Your bucket will now post notifications to the topic every time a new object is added.


## Create Media Metadata Table

1. Create table if it’s not created yet (must be created using `fssi2019-xacc-resource-access` through CLI or Web Console):

```
export tableName=<table-name>
aws dynamodb create-table --profile fssi2019-xacc-resource-access \
    --table-name $tableName \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=100
```

2. Make sure to add stream to your table:

```
aws dynamodb update-table --profile fssi2019-xacc-resource-access \
    --table-name $tableName \
    --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

3. Get table stream ARN:

```
streamArn=`aws dynamodb describe-table --profile fssi2019-xacc-resource-access --table-name $tableName --query "Table.LatestStreamArn" --output text`
```

3. Add trigger to lambda:

```
aws lambda create-event-source-mapping --profile fssi2019-xacc-resource-access \
    --region us-west-1 \
    --function-name fssi2019-lambda-dynamodb-stream-listener \
    --event-source $streamArn  \
    --batch-size 100 \
    --starting-position LATEST
```
## Setup Processing Lambda

To start implementing processing lambda, one shall use current template code. The steps below show how to do it and hook up your processing lambda to the user ingestion SNS topic. One shall also hook up lambda to one's own S3 buckets used for media ingestion.

* copy processing lambda template into a separate folder (set concrete folder name for `<my-proc-lambda>`):

```
export myProcLambda=<my-proc-lambda>
cd lambda
rsync -av lambda-proc-template/ $myProcLambda/ --exclude README.md
```

* create your lambda `<my-proc-lambda-name>` (consult list above for lambda names):

```
export lambdaName=<my-proc-lambda-name>
zip -X -r -j index.zip $myProcLambda/* -x "*.pyc"
aws lambda create-function --profile fssi2019-xacc-resource-access \
    --region us-west-1 \
    --function-name $lambdaName \
    --zip-file fileb://index.zip \
    --role arn:aws:iam::756428767688:role/fssi2019-iam-role-proc-lambda \
    --handler lambda_function.lambda_handler \
    --timeout 600 \
    --runtime python3.7
lambdaArn=`aws lambda get-function --profile fssi2019-xacc-resource-access --function-name $lambdaName --query "Configuration.FunctionArn" --output text`
```

* subscribe your lambda to `fssi2019-sns-ingest-upload` SNS topic:

```
myAccountId=`aws sts get-caller-identity --query "Account" --output text`
aws sns add-permission --profile fssi2019-xacc-resource-access \
    --label lambda-proc-access-$myAccountId \
    --aws-account-id $myAccountId \
    --topic-arn arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload \
    --action-name Subscribe ListSubscriptionsByTopic Receive
aws sns subscribe --profile fssi2019-xacc-resource-access \
    --topic-arn arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload \
    --protocol lambda \
    --notification-endpoint $lambdaArn
aws lambda add-permission --profile fssi2019-xacc-resource-access \
    --function-name $lambdaName \
    --statement-id `date +%s`\
    --action "lambda:InvokeFunction" \
    --principal sns.amazonaws.com \
    --source-arn arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload
```

* implement your lambda
* to upload your code, run:

```
./upload.sh $lambdaName $myProcLambda
```
