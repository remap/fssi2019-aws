LAMBDA_NAME=tactile
LAMBDA_FOLDER=..
DIR=`pwd`


cd $LAMBDA_FOLDER

if [ -f "requirements.txt" ]
then
    # package lambda with dependencies
    docker run --rm -v `pwd`:/lambda peetonn/fssi2019-lambda-packager:latest
    zip -g function.zip * -x "*.pyc" -x "*.txt"
else
    zip -X -r function.zip * -x "*.pyc"
fi

cd $DIR
echo "Uploading code from ${LAMBDA_FOLDER} to lambda named ${LAMBDA_NAME}..."
aws lambda update-function-code --profile fssi2019-xacc-resource-access --function-name $LAMBDA_NAME --zip-file fileb://$LAMBDA_FOLDER/function.zip
rm $LAMBDA_FOLDER/function.zip
