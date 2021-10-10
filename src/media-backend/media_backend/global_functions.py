import json
import jsonschema
import boto3
import time


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


def return_error(message, code=500, ttl=86400):
    return return_message(message, code=code, ttl=ttl)


def return_not_found(object_id, ttl=86400):
    return return_message("Object with ID {} not found.".format(object_id), code=404, ttl=ttl)


def return_message(message, code=200, ttl=86400):
    return return_data({
        "message": message
    }, code=code, ttl=ttl)


def return_data(data, code=200, ttl=86400):
    return {
        "statusCode": code,
        "body": json.dumps(data),
        "headers": {
            "Cache-Control": "s-maxage={}".format(ttl)
        }
    }


def invalidate_path(paths):
    cloudfront = boto3.client('cloudfront')
    cloudfront.create_invalidation(
        DistributionId="E3DPRWRHX4Z2QV",
        InvalidationBatch={
            "Paths": {
                "Quantity": len(paths),
                "Items": paths
            },
            "CallerReference": "%.4f" % time.time()
        }
    )
