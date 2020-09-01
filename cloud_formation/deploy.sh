#!/bin/bash

aws cloudformation deploy --template-file $1 --stack-name $2 --capabilities CAPABILITY_NAMED_IAM
