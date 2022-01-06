# This tool uploads the current working directory using the upload API.
import argparse
import os
import requests
import boto3
import json

# create parser
parser = argparse.ArgumentParser(
    "Upload a directory using the upload API. Make sure there is a file called `token.secret` in your current working directory that contains a valid authentication token for the API.")

# add arguments to the parser
parser.add_argument("--api", dest='api', help='The hostname for the API.')
parser.add_argument("--directory", dest='directory', help='The directory to upload.')

# parse the arguments
args = parser.parse_args()

abs_path = os.path.abspath(args.directory)
files = [os.sep.join([abs_path, f]) for f in os.listdir(abs_path)]

token_file = open("token.secret", "r")
token = token_file.read().strip("\n")
headers = {
    "Authorization": "Bearer {}".format(token)
}

# upload all photos
for file in files:
    print("Uploading {}...".format(file))
    upload_data = requests.post('/'.join([args.api, 'photo']), headers=headers)
    upload_data = json.loads(upload_data.content)
    print("  Created photo: {}".format(upload_data['id']))
    with open(file, 'rb') as fp:
        file_dict = {'file': (file, fp)}
        response = requests.post(upload_data['pre_signed_url']['url'], data=upload_data['pre_signed_url']['fields'],
                                 files=file_dict)
        print("  Uploaded photo: {}".format(response.status_code))
    print("Done!")