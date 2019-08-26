# Exposure Lambda

This lambda is used to process incoming exposure vectors (from exhibits).

## AWS Resource

* Name: `fssi2019-lambda-exposure`
* ARN: `arn:aws:lambda:us-west-1:756428767688:function:fssi2019-lambda-exposure`

### Trigger

* SNS Topic: `fssi2019-sns-emission`
* SNS ARN: `arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission`
* SNS Subscription ARN: `arn:aws:sns:us-west-1:756428767688:fssi2019-sns-emission:92d85985-87c8-4f1a-92dd-82fc6b5b3f41`

## Processing
On trigger:

1. DB fetches
  1.1. Retrieve exhibit occupancy from `fssi2019-dynamodb-occupancy`
  1.2. Retrieve visitor exposures from `fssi2019-dynamodb-visitor_exposure_ts`
2. Calculate per-visitor exposures by some vector operation /TBD/
3. Store new exposure in `fssi2019-dynamodb-visitor_exposure_ts`
4. Publish exposures for the experience - both per-user breakdown and aggregate (average)
5. Write aggregates to `fssi2019-dynamodb-exhibit_exposure_ts` as telemetry
