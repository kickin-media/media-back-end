import json
import jsonschema
import boto3

import globals_variables


def decode_body(event, schema=None):
    try:
        data = json.loads(event['body'])
    except Exception:
        return None, "Data was not valid JSON."

    if schema is not None:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except Exception as e:
            return None, e.message

    return data, None


def return_error(message, code=500, ttl=0):
    return return_message(message, code=code, ttl=ttl)


def return_not_found(object_id, ttl=0):
    return return_message("Object with ID {} not found.".format(object_id), code=404, ttl=ttl)


def return_message(message, code=200, ttl=0):
    return return_data({
        "message": message
    }, code=code, ttl=ttl)


def return_data(data, code=200, ttl=0):
    return {
        "statusCode": code,
        "body": json.dumps(data),
        "headers": {
            "Cache-Control": "s-maxage={}".format(ttl)
        }
    }


def invalidate_path(paths):
    return  # does nothing for now

    # cloudfront = boto3.client('cloudfront')
    # cloudfront.create_invalidation(
    #     DistributionId="E3DPRWRHX4Z2QV",
    #     InvalidationBatch={
    #         "Paths": {
    #             "Quantity": len(paths),
    #             "Items": paths
    #         },
    #         "CallerReference": "%.4f" % time.time()
    #     }
    # )


def get_item_by_entity_type(entity_type, entity_id):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=globals_variables.DDB_TABLE,
        Key={
            'PK': {'S': "album#{}".format(object_id)},
            'SK': {'S': "album#{}".format(object_id)},
        }
    )

    if "Item" not in response:
        return global_functions.return_not_found(album_id)

    return global_functions.return_data(_dd2obj(response["Item"]))


def check_if_key_exists(key):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=globals_variables.DDB_TABLE,
        Key=key
    )

    if "Item" not in response:
        return False

    return True
