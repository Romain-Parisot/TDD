import json
import boto3
import os
from typing import Any
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get('STORAGE_USERTABLE_NAME', 'UserTable')
REGION = 'eu-west-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)  # type: Any
table = dynamodb.Table(TABLE_NAME)  # type: Any

def handler(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        email = params.get('email')

        if not email:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email query parameter is required'})
            }

        response = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        user = items[0]

        return {
            'statusCode': 200,
            'body': json.dumps(user)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }