LAMBDA_NAME=$1
LAMBDA_FOLDER=$2
DIR=`pwd`

if [ $# -ne 2 ]
  then
    echo "Must provide LAMBDA_NAME and LAMBDA_FOLDER arguments"
    exit 1
fi

cd $LAMBDA_FOLDER
zip -X -r $DIR/index.zip *
cd $DIR
echo "Uploading code from ${LAMBDA_FOLDER} to lambda named ${LAMBDA_NAME}..."
aws lambda update-function-code --profile fssi2019-xacc-resource-access --function-name $LAMBDA_NAME --zip-file fileb://index.zip
rm $DIR/index.zip
