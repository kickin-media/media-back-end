import globals_variables
import global_functions

import boto3
import uuid

from event import _key as _event_key

_object_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "pattern": globals_variables.NAME_REGEX},
        "time": {"type": "integer", "minimum": 0},
        "event_id": {"type": "string", "pattern": globals_variables.UUID_REGEX}
    },
    "required": [
        "name", "time", "event_id"
    ],
    "additionalProperties": False
}


def _dd2obj(item):
    return {
        'id': item['SK']['S'].replace("album#", ""),
        'event_id': item['PK']['S'].replace("event#", ""),
        'name': item['Name']['S'],
        'time': item['Time']['N']
    }


def handle(event, context):
    route_key = event['routeKey']

    if route_key.startswith("DELETE /album/"):
        return delete(event, context)
    elif route_key.startswith("PUT /album/"):
        return update(event, context)
    elif route_key == "POST /album":
        return create(event, context)
    elif route_key == 'GET /albums':
        return index(event, context)
    elif route_key.startswith("GET /album/"):
        return get(event, context)

    return global_functions.return_error("Route {} not found.".format(route_key), code=404)


def index(event, context):
    dynamodb = boto3.client('dynamodb')

    scan_paginator = dynamodb.get_paginator('query')
    page_iterator = scan_paginator.paginate(
        TableName=globals_variables.DDB_TABLE,
        IndexName=globals_variables.INDEX_ENTITY_TYPE_PK,
        KeyConditions={
            'EntityType': {
                'AttributeValueList': [{'S': 'album'}],
                'ComparisonOperator': 'EQ'
            },
        },
        Select='ALL_ATTRIBUTES'
    )

    albums = []

    for page in page_iterator:
        for album_item in page['Items']:
            albums.append(_dd2obj(album_item))

    return global_functions.return_data(albums)


def get(event, context):
    album_id = event['pathParameters']['id']

    dynamodb = boto3.client('dynamodb')
    response = dynamodb.query(
        TableName=globals_variables.DDB_TABLE,
        IndexName=globals_variables.INDEX_ENTITY_TYPE_SK,
        KeyConditions={
            'EntityType': {
                'AttributeValueList': [{'S': 'album'}],
                'ComparisonOperator': 'EQ'
            },
            'SK': {
                'AttributeValueList': [{'S': 'album#{}'.format(album_id)}],
                'ComparisonOperator': 'EQ'
            }
        },
        Select='ALL_ATTRIBUTES'
    )

    if "Items" not in response:
        return global_functions.return_not_found(album_id)

    return global_functions.return_data(_dd2obj(response["Items"][0]))


def _put(event, album_id):
    data, error_message = global_functions.decode_body(event, schema=_object_schema)

    if error_message is not None:
        return global_functions.return_error("Invalid input: {}".format(error_message), code=400)

    if album_id is None:
        data['id'] = str(uuid.uuid4())
    else:
        data['id'] = album_id

    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.update_item(
            TableName=globals_variables.DDB_TABLE,
            Key=_key(object_id=data['id'], event_id=data['event_id']),
            UpdateExpression="SET EntityType = :entityType, #name = :name, #time = :time",
            ExpressionAttributeValues={
                ':entityType': {'S': 'album'},
                ':name': {'S': data['name']},
                ':time': {'N': '{}'.format(data['time'])},
            },
            ExpressionAttributeNames={
                '#name': "Name",
                '#time': "Time"
            },
            ConditionExpression="attribute_not_exists(PK)" if album_id is None else "attribute_exists(PK)"
        )
    except Exception as error:
        if 'ConditionalCheckFailedException' in str(error) and album_id is not None:
            return global_functions.return_not_found(album_id)
        else:
            return global_functions.return_error(str(error))

    global_functions.invalidate_path(["/albums", "/album/{}".format(data["id"])])

    return global_functions.return_data({
        'album_id': data['id']
    })


def create(event, context):
    return _put(event, album_id=None)


def update(event, context):
    return _put(event, album_id=event['pathParameters']['id'])


def delete(event, context):
    album_id = event['pathParameters']['id']

    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.delete_item(
            TableName=globals_variables.DDB_TABLE,
            Key=_key(album_id),
            ConditionExpression="attribute_exists(PK)"
        )
    except Exception as e:
        if 'ConditionalCheckFailedException' in str(e):
            return global_functions.return_not_found(album_id)
        else:
            raise e

    global_functions.invalidate_path(["/albums", "/album/{}".format(album_id)])

    return global_functions.return_message("Success.")
