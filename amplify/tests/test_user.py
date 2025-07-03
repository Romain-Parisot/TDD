import json
import boto3
import pytest
import os
from typing import Any
from moto import mock_dynamodb
import sys
import importlib.util


TABLE_NAME = "UserTable"
REGION = "eu-west-1"


def import_handler(path: str):
    spec = importlib.util.spec_from_file_location("module.name", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.handler

@pytest.fixture(scope="function")
def dynamodb_mock():
    
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        table = dynamodb.create_table( # type: ignore
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"},
                {"AttributeName": "user_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "email-index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
                }
            ],
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)

        os.environ['STORAGE_USERTABLE_NAME'] = TABLE_NAME

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'function'))

        add_user_path = os.path.join(base_dir, 'addUser', 'src', 'index.py')
        get_user_path = os.path.join(base_dir, 'getUser', 'src', 'index.py')

        global add_user_handler
        global get_user_handler

        add_user_handler = import_handler(add_user_path)
        get_user_handler = import_handler(get_user_path)

        yield

def test_add_user(dynamodb_mock):
    email = "test@example.com"
    event = {
        "body": json.dumps({"email": email})
    }

    response = add_user_handler(event, None)
    body = json.loads(response["body"])

    print("Response:", response)
    print("Body:", response.get("body"))

    assert response["statusCode"] == 200
    assert "id" in body

def test_get_user(dynamodb_mock):
    email = "test@example.com"
    user_id = "1234-5678"

    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table(TABLE_NAME) # type: ignore

    table.put_item(Item={"email": email, "user_id": user_id})

    event = {
        "queryStringParameters": {"email": email}
    }

    response = get_user_handler(event, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["email"] == email
    assert body["user_id"] == user_id
