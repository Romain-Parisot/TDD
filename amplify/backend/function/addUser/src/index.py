import json
import boto3
import uuid
import os
from typing import Any
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get('STORAGE_USERTABLE_NAME', 'UserTable-dev')
REGION = 'eu-west-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)  # type: Any
table = dynamodb.Table(TABLE_NAME)  # type: Any

def handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')

        if not email:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email is required'})
            }

        user_id = str(uuid.uuid4())

        table.put_item(Item={
            'email': email,
            'id': user_id
        })

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User added', 'id': user_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
