LAMBDA_NAME=$1
LAMBDA_FOLDER=$2
DIR=`pwd`

if [ $# -ne 2 ]
  then
    echo "Must provide LAMBDA_NAME and LAMBDA_FOLDER arguments"
    exit 1
fi

cd $LAMBDA_FOLDER

if [ -f "requirements.txt" ]
then
    # package lambda with dependencies
    docker run --rm -v `pwd`:/lambda peetonn/fssi2019-lambda-packager:latest
    zip -g function.zip * -x "*.pyc" -x "*.txt"
else
    zip -X -r function.zip * -x "*.pyc"
fi
echo $PWD
aws s3 cp --profile fssi2019-xacc-resource-access function.zip s3://fssi2019-s3-code-support
cd $DIR

echo "Uploading code from ${LAMBDA_FOLDER} to lambda named ${LAMBDA_NAME}..."
aws lambda update-function-code --profile fssi2019-xacc-resource-access --function-name $LAMBDA_NAME --s3-bucket fssi2019-s3-code-support --s3-key function.zip
rm -r $LAMBDA_FOLDER/function.zip