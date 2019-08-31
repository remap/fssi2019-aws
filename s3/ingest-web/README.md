# User Content Ingestion Interface

To upload your content, go to http://fssi2019-s3-ingest-web.s3-website-us-west-1.amazonaws.com/ .

You file will be uploaded to the S3 bucket `fssi2019-s3-ingest` and processed for embedded or supplied metadata.

## Update web interface (dev)

Web interface can be updated by uploading "index.html" S3 bucket `fssi2019-s3-ingest-web`. To do this using AWS CLI:

```
aws s3 cp index.html s3://fssi2019-s3-ingest-web/index.html
```
