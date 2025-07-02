#!/bin/bash
#
### This script will retrive aws usage ###

set -x

echo "s3"
aws s3 ls

echo "ec2"

aws ec2 describe-instances

echo "lambda"

aws lambda list-functions

echo "iam"

aws iam list-users
