#!/bin/bash

pip3 install -r /lambda/requirements.txt --target /tmp/lambda-package
cd /tmp/lambda-package
zip -r9 /lambda/function.zip .
