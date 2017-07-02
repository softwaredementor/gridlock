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
    # titletext = "Click here to see traffic pattern for " + command_text
    
    geocode_command = "https://maps.googleapis.com/maps/api/geocode/json?address="+command_text+"&key="+GOOGLE_MAPS_KEY
    output = urllib2.urlopen(geocode_command).read()
    pl = json.loads(output)
    lat = pl["results"][0]["geometry"]["location"]["lat"]
    lng = pl["results"][0]["geometry"]["location"]["lng"]
    trafficpattern_url = "https://www.google.co.in/maps/@"+"%.7f"%lat+","+"%.7f"%lng+",852m/data=!3m1!1e3!5m1!1e1"
    trafficpattern_url_alternate = "https://www.google.co.in/maps/@"+"%.7f"%lat+","+"%.7f"%lng+",16z/data=!5m1!1e1"
    
    titletext = "Click this link for more details"
    # finaltext = commands_text + " Traffic pattern alert!"
    imagelink = "https://maps.googleapis.com/maps/api/staticmap?center="+"%.7f"%lat+","+"%.7f"%lng+"&zoom=12&size=400x400&key=AIzaSCphPm-ocWxABmR3OMqImDOphbazGGwhN_A"
    test = {"text": "Traffic pattern alert!",
    "attachments": [
        {
            "title": titletext,
            "title_link": trafficpattern_url,
            "image_url": imagelink
        },
        
        {
            "fallback": "Do you have a suggestion to the traffic control room?",
            "title": "Do you have a suggestion to the traffic control room?",
            "callback_id": "traffic_1234_xyz",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [
                {
                    "name": "yes",
                    "text": "Travel exp was bad",
                    "type": "button",
                    "value": "recommend"
                },
                {
                    "name": "no",
                    "text": "Travel exp was good",
                    "type": "button",
                    "value": "bad"
                }
            ]
        }
    ]}
    return respond(None, str(test))

