'''
This function handles a Slack slash command and echoes the details back to the user.

Follow these steps to configure the slash command in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Slash Commands".

  3. Enter a name for your command and click "Add Slash Command Integration".

  4. Copy the token string from the integration settings and use it in the next section.

  5. After you complete this blueprint, enter the provided API endpoint URL in the URL field.


To encrypt your secrets use the following steps:

  1. Create or use an existing KMS Key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html

  2. Click the "Enable Encryption Helpers" checkbox

  3. Paste <COMMAND_TOKEN> into the kmsEncryptedToken environment variable and click encrypt


Follow these steps to complete the configuration of your command API endpoint

  1. When completing the blueprint configuration select "Open" for security
     on the "Configure triggers" page.

  2. Enter a name for your execution role in the "Role name" field.
     Your function's execution role needs kms:Decrypt permissions. We have
     pre-selected the "KMS decryption permissions" policy template that will
     automatically add these permissions.

  3. Update the URL for your Slack slash command with the invocation URL for the
     created API resource in the prod stage.
'''

import boto3
import json
import logging
import os
import httplib, urllib2

from base64 import b64decode
from urlparse import parse_qs
from pprint import pprint

ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']
GOOGLE_MAPS_KEY = "AIzaSCphPm-ocWxABmR3OMqImDOphbazGGwhN_A"
kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else res,
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    params = parse_qs(event['body'])
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        return respond(Exception('Invalid request token'))

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0]

    MODES = ["DRIVING", "WALKING", "BICYCLING", "TRANSIT"]
    qparams = command_text.split()
    origin = qparams[0]
    destination = qparams[1]
    response_message = ""
    original_query = "https://maps.googleapis.com/maps/api/directions/json?origin="+origin+"&destination="+destination+"&key="+GOOGLE_MAPS_KEY

    if(len(qparams)>2 and (qparams[2].upper() in map(str.upper, MODES))):
       mode = qparams[2]
       output = urllib2.urlopen(original_query+"&mode="+mode).read()
    elif(len(qparams)>2 and qparams[2].upper() not in map(str.upper, MODES)):
       response_message = "`*Choose travel mode as : walking/bicycling/driving/transit*`\n"
       output = urllib2.urlopen(original_query).read()
    elif(len(qparams)==2):
       output = urllib2.urlopen(original_query).read()
    elif(len(qparams)<2):
       response_message = "Choose an origin and destination! \n"
       return respond(None, response_message)

    pl = json.loads(output)
    if(len(pl["routes"])==0):
        response_message = "`No route exists using " + mode.upper() + " as transportation between "+origin.upper()+" and "+destination.upper()+"`\n"
        return respond(None, response_message)
    return respond(None, response_message + "*Origin:* %s and *Destination:* %s\n *Distance:* %s *Duration:* %s \n*TravelMode:* %s" % (origin, destination, pl["routes"][0]["legs"][0]["distance"]["text"],pl["routes"][0]["legs"][0]["duration"]["text"], pl["routes"][0]["legs"][0]["steps"][0]["travel_mode"]))
    #return respond(None, "%s invoked %s in %s with the following text: %s" % (user, command, channel, pl))
