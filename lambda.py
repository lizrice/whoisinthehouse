"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import boto3

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
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
table = dynamodb.Table('WhoIsInTheHouse')

def get_names():
    names = ""

    response = table.scan()

    nameCount = len(response['Items'])
    for idx, item in enumerate(response['Items']):
        names += item['NameId']
        if idx == nameCount - 2:
            names += " and "
        elif idx != nameCount - 1:
            names += ", "

    return names

def add_name(name):
    try:
        response = table.put_item(
           Item={
                'NameId': name
            }
        ) 
    except ClientError as e:
        print(e.response)
        return e.response['Error']['Code']        
        
    return None

def delete_name(name):
    try:
        response = table.delete_item(
           Key={
                'NameId': name
            }
        )    
    except ClientError as e:
        print(e.response)
        return e.response['Error']['Code']        

    return None

# --------------- Functions that control the skill's behavior ------------------

def get_help_response(): 
    session_attributes = {}
    card_title = "Help"
    speech_output = get_names() + " are here in the house. " + \ 
        "You can tell me if someone has arrived or left and I'll keep the " + \
        "list up-to-date."
    should_end_session = False
    reprompt_text = "Has anyone arrived or left?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
    
def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = get_names() + " are here in the house."
    should_end_session = False
    reprompt_text = "Has anyone arrived or left?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = get_names() +  " are here in the house."
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}

def add_name_in_session(intent, session):
    card_title = intent['name']
    session_attributes = {}
    speech_output = ""
    reprompt_text = ""
    if 'Name' in intent['slots']:
        name = intent['slots']['Name']['value']
        error = add_name(name)
        if error is not None:
            speech_output = "Sorry, that didn't work. " + error
            reprompt_text = "Tell me the name of a person who arrived?"
            should_end_session = False
        else:
            speech_output = "Now that " + name + " is here, " + get_names() + " are here in the house."
            should_end_session = True
    else:
        reprompt_text = "Sorry, I didn't understand. Please try again."
        should_end_session = False
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def remove_name_in_session(intent, session):
    card_title = intent['name']
    session_attributes = {}
    speech_output = ""
    reprompt_text = ""

    if 'Name' in intent['slots']:
        name = intent['slots']['Name']['value']
        error = delete_name(name)
        if error is not None:
            speech_output = "Sorry, that didn't work. " + error
            reprompt_text = "Tell me the name of a person who left the house?" 
            should_end_session = False
        else:
            speech_output = "Now that " + name + " has gone, " + get_names() + " are here in the house."
            should_end_session = True
    else:
        reprompt_text = "Sorry, I didn't understand. Please try again."
        should_end_session = False
    
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


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
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "WhoIsInTheHouse":
        return get_welcome_response()
    elif intent_name == "ArrivedInTheHouse":
        return add_name_in_session(intent, session)
    elif intent_name == "LeftTheHouse":
        return remove_name_in_session(intent, session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
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

