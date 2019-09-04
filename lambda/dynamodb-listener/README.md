# Exposure Lambda

This lambda processes DynamoDB Stream events and publishes SNS notifications.

## AWS Resource

* Name: `fssi2019-lambda-dynamodb-stream-listener`
* ARN: `arn:aws:lambda:us-west-1:756428767688:function:fssi2019-lambda-dynamodb-stream-listener`

### Trigger

* Any DynamoDB Stream

#### To add your table

1. Enable "Stream" for your table named `<table-name>`:

```
aws dynamodb update-table \
	--table-name <table-name>
	--stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

2. Get table stream ARN (requires `jq`):

> To install `jq` (aka "JSON query"), run `brew install jq`


```
streamArn=`aws dynamodb describe-table --table-name <table-name> | jq ".Table | .LatestStreamArn"`
```

3. Add trigger to this lambda:

```
aws lambda create-event-source-mapping \
    --region us-west-1 \
    --function-name fssi2019-lambda-dynamodb-stream-listener \
    --event-source $streamArn  \
    --batch-size 100 \
    --starting-position LATEST
```


### Input Format

The lambda receives DynamoDB Stream notifications (can be batched), that might look like this:

```
{
   "Records":[
      {
         "eventID":"511159a4d0156bf36339813ba3846e58",
         "eventName":"INSERT",
         "eventVersion":"1.1",
         "eventSource":"aws:dynamodb",
         "awsRegion":"us-west-1",
         "dynamodb":{
            "ApproximateCreationDateTime":1567576279.0,
            "Keys":{
               "id":{
                  "S":"test_id2"
               }
            },
            "NewImage":{
               "key1":{
                  "S":"value1"
               },
               "key2":{
                  "S":"value2"
               },
               "id":{
                  "S":"test_id2"
               }
            },
            "SequenceNumber":"4500000000000852941236",
            "SizeBytes":40,
            "StreamViewType":"NEW_AND_OLD_IMAGES"
         },
         "eventSourceARN":"arn:aws:dynamodb:us-west-1:<account-id>:table/<table-name>/stream/<timestamp>"
      },
      {
         "eventID":"bfc033a327e89a795c9acd676e6d1ffc",
         "eventName":"REMOVE",
         "eventVersion":"1.1",
         "eventSource":"aws:dynamodb",
         "awsRegion":"us-west-1",
         "dynamodb":{
            "ApproximateCreationDateTime":1567576280.0,
            "Keys":{
               "id":{
                  "S":"test_id3"
               }
            },
            "OldImage":{
               "key1":{
                  "S":"value1"
               },
               "key2":{
                  "S":"value2"
               },
               "id":{
                  "S":"test_id3"
               }
            },
            "SequenceNumber":"4600000000000852941441",
            "SizeBytes":40,
            "StreamViewType":"NEW_AND_OLD_IMAGES"
         },
         "eventSourceARN":"arn:aws:dynamodb:us-west-1:<account-id>:table/<table-name>/stream/<timestamp>"
      }
   ]
}
```

## Processing
On trigger:

1. Parse incoming notification
2. Form SNS message JSON:

```
{
    "table": <table-name>,
    "event": <INSERT | REMOVE>,
    "itemId": <item-id>,
    "itemData": <item-data>
}
```

3. Publish SNS message to `fssi2019-sns-dynamodb-updates`
