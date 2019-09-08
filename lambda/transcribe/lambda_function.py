import json
import boto3
import sys, os
from fssi_common import *
import subprocess

FFMPEG_STATIC = "/var/task/ffmpeg"

################################################################################
def get_duration(file):
    """Get the duration of a video using ffprobe."""
    cmd = '/var/task/ffprobe -i {} -show_entries format=duration -v quiet -of csv="p=0"'.format(file)
    output = subprocess.check_output(
        cmd,
        shell=True, # Let this run in the shell
        stderr=subprocess.STDOUT
    )
    # return round(float(output))  # ugly, but rounds your seconds up or down
    return float(output)

## S3 Object Processing Here
def processObject(objectKey, s3BucketName, s3BucketArn):
    fName = None
    mimeType = guessMimeTypeFromExt(objectKey)
    print(mimeType)
    if not mimeType:
        print('couldn\'t derive MIME type from extension')
        fName = downloadFile(objectKey, s3BucketName)
        mimeType = guessMimeTypeFromFile(fName)

    if 'audio' in mimeType:
        if not fName:
            fName = downloadFile(objectKey, s3BucketName)
        ## need audio type to clip file. transcribe supports mp3, wav
        audio = ""
        audio_format = ""
        fOutName = fName[:-4] + "_trim" + fName[-4:]
        duration = get_duration(fName)
        trimmed = False
        if duration > 10: 
            #trim to 10 seconds from the middle
            start = str(round(duration/2 - 5))
            subprocess.call([FFMPEG_STATIC, '-ss', start, '-t', '10', '-i', fName, fOutName])
            trimmed = True
        if 'mpeg' in mimeType:
            # audio = AudioSegment.from_mp3(fName)
            audio_format = 'mp3'
        elif 'x-wav' in mimeType:
            audio = AudioSegment.from_wav(fName)
            audio_format = 'wav'

        if trimmed:
            fName = fOutName
        with open(fName, 'rb') as data:
                s3Client.put_object(Bucket="fssi2019-s3-code-support", Body=data, Key=objectKey)

        transcribe = boto3.client(
            'transcribe',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            aws_session_token=SESSION_TOKEN
        )
        job_name = "transcribe_"+str(hash(objectKey))
        job_uri = "s3://fssi2019-s3-code-support"+'/'+objectKey
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            LanguageCode='en-US',
            MediaFormat=audio_format,
            OutputBucketName="fssi2019-s3-transcription-out"
        )

    # raise ValueError('object processing is not implemented')

################################################################################
## Lambda Handler
def lambda_handler(event, context):
    try:
        if not 'Records' in event:
            # assume direct invocation
            objectKey = event['objectKey']
            bucket = event['bucket']
            bucketArn = event['bucketArn'] if 'bucketArn' in event else None

            print('direct invocation for object {} from bucket {}'.format(objectKey, bucket))
            processObject(objectKey, bucket, bucketArn)
        else:
            for record in event['Records']:
                if record['EventSource'] != 'aws:sns':
                    return lambdaReply(420, 'received non-SNS event record: {}'.format(record))

                snsRecord = record['Sns']
                messageDict = json.loads(snsRecord['Message'])
                for snsRecord in messageDict['Records']:
                    if snsRecord['eventName'] == 'ObjectCreated:Put':
                        s3BucketName = snsRecord['s3']['bucket']['name']
                        s3BucketArn =  snsRecord['s3']['bucket']['arn']
                        objectKey = snsRecord['s3']['object']['key']

                        print('new item {} added to bucket {} ({})'.format(objectKey, s3BucketName, s3BucketArn))
                        print("CallFunction")
                        processObject(objectKey, s3BucketName, s3BucketArn)
                    else:
                        lambdaReply(420, 'SNS event type not supported: {}'.format(snsRecord['eventName']))
    except:
        err = reportError()
        print('caught exception:', sys.exc_info()[0])
        return lambdaReply(420, str(err))

    return processedReply()

# for testing, run locally "python lambda_function.py"
if __name__ == '__main__':
    sampleSnsEvent = {
                        'Records':[
                        {
                            'EventSource':'aws:sns',
                            'EventVersion':'1.0',
                            'EventSubscriptionArn':'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload:7e9d0542-bdae-4ec9-a114-d73be62f9a28',
                            'Sns':{
                                'Type':'Notification',
                                'MessageId':'105a42d1-a4a5-5adf-a620-173bb838d5a7',
                                'TopicArn':'arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload',
                                'Subject':'Amazon S3 Notification',
                                'Message':'{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-west-1","eventTime":"2019-09-04T20:11:09.660Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AROA3AHVLAHEOUASVZXIH:fssi2019-lambda-ingest-gate"},"requestParameters":{"sourceIPAddress":"131.179.142.121"},"responseElements":{"x-amz-request-id":"497AD45555DD0057","x-amz-id-2":"eyiMv7GzyjS7azmBORnShRuyUIxUVBLzQitguWVagDn8obtQqgtJ1PsMPxlCYvU2MmiXPYccxcE="},"s3":{"s3SchemaVersion":"1.0","configurationId":"Ingest Upload","bucket":{"name":"fssi2019-s3-ingest","ownerIdentity":{"principalId":"A2IYG3741R477C"},"arn":"arn:aws:s3:::fssi2019-s3-ingest"},"object":{"key":"upload/28d61694-0348-4c6f-83a2-89a9d781d942.md","size":466,"eTag":"bdf430c4b4bbdd37886b0de2a4b87107","sequencer":"005D701A5D9658C51B"}}}]}',
                                'Timestamp':'2019-09-04T20:11:09.920Z',
                                'SignatureVersion':'1',
                                'Signature':'evgodY/lwnQ7Luw4XrUWdBsOim6Ufe6DAIAN7fdwOU5Ao8BT8XQ2D4y+6Kq9Ja1GQTJnZE1vwlw1MLqCLXFDzWnbJvko98rZBdgzrm+N8MW/Jp+0gQfjZOWnMvHu98sJyZPGuz7foE3hFT3FCUlsieVbRSK6PD9MMqya5PGYnjXUfQKb80TnBu/58hRmY0R+aVbskqraPdnIB0Z9ZcCm1neRkJ1u/CcDY6w1ENxWZokh8/jt3b9dJ9UjP92U/tlmrAV4nlw+h9GbXpfTS+k7aa+pZoQ1NFgcJ3ETkBpEMY5Vsc4DFaHFuJGhFvsjfSUHmMHUgroEC5d8z8yV/2wbNg==',
                                'SigningCertUrl':'https://sns.us-west-1.amazonaws.com/SimpleNotificationService-6aad65c2f9911b05cd53efda11f913f9.pem',
                                'UnsubscribeUrl':'https://sns.us-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-1:756428767688:fssi2019-sns-ingest-upload:7e9d0542-bdae-4ec9-a114-d73be62f9a28',
                                'MessageAttributes':{}
                                }
                        }]
                    }
    lambda_handler(sampleSnsEvent, None)
