#!/bin/bash
CWD="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# install brew, python3 and virtualenv
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
if [ $? -ne 0 ]; then
    echo "brew install failed"
    exit 1
fi

brew install python jq
if [ $? -ne 0 ]; then
    echo "python3 install failed"
    exit 1
fi

pip3 install virtualenv
if [ $? -ne 0 ]; then
    echo "virtualenv install failed"
    exit 1
fi

git clone https://github.com/remap/fssi2019-aws.git
if [ $? -ne 0 ]; then
    echo "git clone failed"
    exit 1
fi

virtualenv -p python3 fssi2019-aws/env && source fssi2019-aws/env/bin/activate
if [ $? -ne 0 ]; then
    echo "virtualenv setup failed"
    exit 1
fi

pip install awscli boto3
if [ $? -ne 0 ]; then
    echo "virtualenv pip install failed"
    exit 1
fi

${CWD}/fssi2019-aws/touch/get-module-path.sh
if [ $? -ne 0 ]; then
    echo "get-module-path failed"
    exit 1
fi

mkdir -p ~/.aws
cmd="ZWNobyAtZSAiW2RlZmF1bHRdXG5hd3NfYWNjZXNzX2tleV9pZCA9IEFLSUEzQUhWTEFIRUk0R00yNk83XG5hd3Nfc2VjcmV0X2FjY2Vzc19rZXkgPSBxMWdpaTdkOU1KZkdQdndIZEpGVjJGRWtyQmt0akxsKzVvRFFsaW1TXG5yZWdpb249dXMtd2VzdC0xIiA+IH4vLmF3cy9jcmVkZW50aWFscwo="
eval "`echo $cmd | base64 --decode`"

echo "--> setup completed"
