"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
from boto3.dynamodb.conditions import Key, Attr
import boto3
from botocore.exceptions import ClientError

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Interacting with DynamoDB ------------------------------------
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('WhoIsInTheHouses')

def get_names(userID):
    names = ""

    response = table.query(
        KeyConditionExpression=Key('UserID').eq(userID)
    )

    nameCount = len(response['Items'])
    for idx, item in enumerate(response['Items']):
        names += item['Name']
        if idx == nameCount - 2:
            names += " and "
        elif idx != nameCount - 1:
            names += ", "

    return names, nameCount

def get_name_list(userID):
    names, number = get_names(userID)
    if number == 0:
        return "There is no-one here in the house."
    elif number == 1:
        return names + " is the only person here in the house."
    else:
        return names + " are here in the house."

def add_name(userID, name):
    try:
        response = table.put_item(
           Item={
                'UserID': userID,
                'Name': name
            }
        ) 
    except ClientError as e:
        print(e.response)
        return e.response['Error']['Code']        
        
    return None

def delete_name(userID, name):
    try:
        response = table.delete_item(
           Key={
                'UserID': userID,
                'Name': name
            }
        )    
    except ClientError as e:
        print(e.response)
        return e.response['Error']['Code']        

    return None

# --------------- Functions that control the skill's behavior ------------------

def get_help_response(userID): 
    session_attributes = {}
    card_title = "Help"
    speech_output = get_name_list(userID) + \
        "You can tell me if someone has arrived or left and I'll keep the " + \
        "list up-to-date."
    should_end_session = False
    reprompt_text = "Has anyone arrived or left?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
    
def get_welcome_response(userID):
    session_attributes = {}
    card_title = "Welcome"
    speech_output = get_name_list(userID)
    should_end_session = False
    reprompt_text = "Has anyone arrived or left?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request(userID):
    card_title = "Session Ended"
    speech_output = get_name_list(userID)
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}

def add_name_in_session(intent, session, userID):
    card_title = "Someone arrived in the house"
    session_attributes = {}
    speech_output = ""
    reprompt_text = ""
    if 'Name' in intent['slots']:
        name = intent['slots']['Name']['value']
        error = add_name(userID, name)
        if error is not None:
            speech_output = "Sorry, that didn't work. " + error
            reprompt_text = "Tell me the name of a person who arrived?"
            should_end_session = False
        else:
            speech_output = "Now that " + name + " is here, " + get_name_list(userID)
            should_end_session = True
    else:
        speech_output = "Sorry, I didn't understand. Please try again."
        should_end_session = False
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def remove_name_in_session(intent, session, userID):
    card_title = "Someone left the house"
    session_attributes = {}
    speech_output = ""
    reprompt_text = ""

    if 'Name' in intent['slots']:
        name = intent['slots']['Name']['value']
        error = delete_name(userID, name)
        if error is not None:
            speech_output = "Sorry, that didn't work. " + error
            reprompt_text = "Tell me the name of a person who left the house?" 
            should_end_session = False
        else:
            speech_output = "Now that " + name + " has gone, " + get_name_list(userID)
            should_end_session = True
    else:
        speech_output = "Sorry, I didn't understand. Please try again."
        should_end_session = False
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    userID = session['user']['userId']

    # Dispatch to your skill's launch
    return get_welcome_response(userID)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    userID = session['user']['userId']

    if intent_name == "WhoIsInTheHouse":
        return get_welcome_response(userID)
    elif intent_name == "ArrivedInTheHouse":
        return add_name_in_session(intent, session, userID)
    elif intent_name == "LeftTheHouse":
        return remove_name_in_session(intent, session, userID)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(userID)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response(userID)
    else:
         raise ValueError("Invalid intent")    


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.26c78df3-5551-4001-b71b-eb6fdd799ebc"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

