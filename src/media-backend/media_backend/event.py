import globals_variables
import global_functions

import boto3
import uuid

_object_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "pattern": globals_variables.NAME_REGEX},
        "time": {"type": "integer", "minimum": 0}
    },
    "required": [
        "name", "time"
    ],
    "additionalProperties": False
}


def _key(object_id):
    return {
        'PK': {'S': "event#{}".format(object_id)},
        'SK': {'S': "event#{}".format(object_id)},
    }


def _dd2obj(item):
    return {
        'id': item['PK']['S'].replace("event#", ""),
        'name': item['Name']['S'],
        'time': item['Time']['N']
    }


def handle(event, context):
    route_key = event['routeKey']

    if route_key.startswith("DELETE /event/"):
        return delete(event, context)
    elif route_key.startswith("PUT /event/"):
        return update(event, context)
    elif route_key == "POST /event":
        return create(event, context)
    elif route_key == 'GET /events':
        return index(event, context)
    elif route_key.startswith("GET /event/"):
        return get(event, context)

    return global_functions.return_error("Route {} not found.".format(route_key), code=404)


def index(event, context):
    dynamodb = boto3.client('dynamodb')

    scan_paginator = dynamodb.get_paginator('query')
    page_iterator = scan_paginator.paginate(
        TableName=globals_variables.DDB_TABLE,
        IndexName='EntityTypeIndex',
        KeyConditions={
            'EntityType': {
                'AttributeValueList': [{'S': 'event'}],
                'ComparisonOperator': 'EQ'
            },
        },
        Select='ALL_ATTRIBUTES'
    )

    events = []

    for page in page_iterator:
        for event_item in page['Items']:
            events.append(_dd2obj(event_item))

    return global_functions.return_data(events, ttl=604800)


def get(event, context):
    event_id = event['pathParameters']['id']

    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=globals_variables.DDB_TABLE,
        Key=_key(event_id)
    )

    if "Item" not in response:
        return global_functions.return_not_found(event_id)

    return global_functions.return_data(_dd2obj(response["Item"]), ttl=604800)


def _put(event, event_id):
    data, error_message = global_functions.decode_body(event, schema=_object_schema)
    if error_message is not None:
        return global_functions.return_error("Invalid input: {}".format(error_message), code=400)

    if event_id is None:
        data['id'] = str(uuid.uuid4())
    else:
        data['id'] = event_id

    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.update_item(
            TableName=globals_variables.DDB_TABLE,
            Key=_key(data['id']),
            UpdateExpression="SET EntityType = :entityType, #name = :name, #time = :time",
            ExpressionAttributeValues={
                ':entityType': {'S': 'event'},
                ':name': {'S': data['name']},
                ':time': {'N': '{}'.format(data['time'])},
            },
            ExpressionAttributeNames={
                '#name': "Name",
                '#time': "Time"
            },
            ConditionExpression="attribute_not_exists(PK)" if event_id is None else "attribute_exists(PK)"
        )
    except Exception as error:
        if 'ConditionalCheckFailedException' in str(error) and event_id is not None:
            return global_functions.return_not_found(event_id)
        else:
            return global_functions.return_error(str(error))

    global_functions.invalidate_path(["/events", "/event/{}".format(data["id"])])

    return global_functions.return_data({
        'event_id': data['id']
    })


def create(event, context):
    return _put(event, event_id=None)


def update(event, context):
    return _put(event, event_id=event['pathParameters']['id'])


def delete(event, context):
    event_id = event['pathParameters']['id']

    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.delete_item(
            TableName=globals_variables.DDB_TABLE,
            Key=_key(event_id),
            ConditionExpression="attribute_exists(PK)"
        )
    except Exception as e:
        if 'ConditionalCheckFailedException' in str(e):
            return global_functions.return_not_found(event_id)
        else:
            raise e

    global_functions.invalidate_path(["/events", "/event/{}".format(event_id)])

    return global_functions.return_message("Success.")
