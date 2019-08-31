# Ingest Gate Lambda

This lambda is used for content ingestion through the [web interface](s3/ingest-web).

## AWS Resource

* Name: `fssi2019-lambda-ingest-gate`
* ARN: `arn:aws:lambda:us-west-1:756428767688:function:fssi2019-lambda-ingest-gate`

### Trigger

* API Gateway: `https://j7f6n2sy1e.execute-api.us-west-1.amazonaws.com/stage`
* Type: `GET`
* Parameters:
    * `name` -- filename to upload

## Processing
On trigger:

1. Generate unique file identifier for the upload.
2. Ask S3 ingest bucket to generate presigned upload URL.
3. Return S3 pre-signed URL and file identifier back to the client.
