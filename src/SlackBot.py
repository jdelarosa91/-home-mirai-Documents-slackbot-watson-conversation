from __future__ import print_function
from apiclient import discovery
from slackclient import SlackClient
from oauth2client import client
from oauth2client import tools
from langdetect import detect

from GoogleCalendar import GoogleCalendar
from User import User
from WatsonServices import WatsonConversation
from WatsonServices import WatsonTranslator

import datetime
import httplib2
import json
import logging
import os
import re
import sys 
import time


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

 
logging.basicConfig()
reload(sys)  
sys.setdefaultencoding('utf8')

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# get enviroments variables
slack_token = os.environ.get('SLACK_TOKEN')
watson_translator_user = os.environ.get('WATSON_TRANS_USER')
watson_translator_pass = os.environ.get('WATSON_TRANS_PASS')
watson_conversation_user = os.environ.get('WATSON_CONVER_USER')
watson_conversation_pass = os.environ.get('WATSON_CONVER_PASS')
watson_conversation_workspace = os.environ.get('WATSON_CONVER_WORKSPACE')
context = {}

#Initialize constant variables.
COLOR_LIST = ["#3AA3E3","#FF0000", "#FFFF00", "#FF0080", "#00FF80", "#38610B", "#A9D0F5"]
ERROR_MSG = "We are sorry, our system is temporarily unavailable."
FLOW_MAP = {}

#Initialize every service to be used
googleCalendar = GoogleCalendar()
watsonTranslator = WatsonTranslator(watson_translator_user,watson_translator_pass)
watsonConversation = WatsonConversation(watson_conversation_user,watson_conversation_pass,watson_conversation_workspace)


def handle_command(command, channel,userList):
    """
        Receives commands directed at the bot and determines if they
        are valid commands.
        If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    attachments = []
    response = "I am not sure what you mean."

    #Getting the language of the text. If there is any problem (such as short sentence), english is used.
    try :
        lang = detect(command.decode('utf-8'))
        lang = lang if lang and lang in ["en", "es"] else 'en'
    except :
        lang = "en"

    if command.startswith("token"):
        store_status = googleCalendar.set_auth_token(userList[0].id, command[6:].strip())
        if store_status is None:
            response = "You must first start the authorization process with @watson hello."
        elif store_status == -1:
            response = "The token you sent is wrong."
        elif store_status == 0:
            response = "Authentication successful!You can now communicate with Watson."
    elif googleCalendar.get_credentials(userList[0].id) is None or command.startswith("reauth"):
        url = googleCalendar.get_auth_url(userList[0].id)
        if url == False :
            response = ERROR_MSG
        else :
            response = "Visit the following URL in the browser: " +  url \
                       + " \n Then send watson the authorization code like @arwen token abc123."
    else :
        #get language of the text and translate it using watson when it is not english
        _summary = re.findall('[\"][\w _.,!''/$]+[\"]',command, re.UNICODE)
        summary = _summary[0].replace('"', '') if _summary else "Event created by SlackBot"
        command = re.sub('[\"][\w _.,!''/$]+[\"]', 'something', command, flags=re.IGNORECASE)
        
        if lang != 'en':
            command = watsonTranslator.translateText(command, lang, 'en')

        #Get response from Watson Conversation
        responseFromWatson = watsonConversation.responseFromWatson(command, context)

        if responseFromWatson == False :
            response = ERROR_MSG
        elif len(responseFromWatson['intents'])<1 :
            response = "I am not sure what you mean."
        else :
            #Get intent of the query
            intent = responseFromWatson['intents'][0]['intent']

            #Get entities fo the query
            entitiesResponse = responseFromWatson['entities']
            entities = []
            if entitiesResponse:
                for entity in entitiesResponse:
                    entities.append((entity["entity"], entity["value"]))

            
            #Evaluate the different posible intents to execute a task and get a response
            if (intent == "schedule_within_30d" or intent == "schedule_longterm"):

                """
                    In this intent the user is requesting for having a look to his calendar.
                """
                calendarItems = googleCalendar.get_response(userList[0], intent)
                if len(calendarItems) == 0 :
                    response = "You don't have any event for the next days"
                else :
                    response = "Here are your upcoming events: "
                for item in calendarItems :
                    attachmentObject = {}
                    attachmentObject['color'] = COLOR_LIST[0]
                    attachmentObject['title']= item['summary']
                    text = \
                    "All day, " + item['start'].strftime("%D") if item['isAllDay'] == True else "From " + item['start'].strftime("%I:%M %p %D")
                    if lang != 'en' : 
                        text = watsonTranslator.translateText(text, 'en', lang)
                    attachmentObject['text']= text
                    attachments.append(attachmentObject)


            elif intent == "workers_schedule" :
                """
                    In this intent the user is requesting for having a look to 
                    someone else calendar.
                """
                i=0
                usersNonAuth= []
                for index, user in enumerate(userList):
                    i = 0 if i == 7 else i
                    if googleCalendar.get_credentials(user.id) is None :
                        usersNonAuth.append(user)
                    elif (index != 0) :
                        attachmentObject = {}
                        attachmentObject['color'] = "#FFFFFF"
                        attachmentObject['title']= user.realName

                        attachments.append(attachmentObject)
                        calendarItems = googleCalendar.get_response(user, intent)

                        for item in calendarItems:
                            attachmentObject = {}
                            attachmentObject['color'] = COLOR_LIST[i]
                            attachmentObject['title']= item['summary']
                            text = \
                            "All day, " + item['start'].strftime("%D") if item['isAllDay'] == True else "From " + item['start'].strftime("%I:%M %p %D")
                            if lang != 'en' : 
                                text = watsonTranslator.translateText(text, 'en', lang)
                            attachmentObject['text']= text
                            attachments.append(attachmentObject)
                        i = i + 1
                if len(usersNonAuth) == 0 :
                    response = "Here are your upcoming events and your co-workers's upcoming events: "
                else :
                    response = "The following users must start authorization process first: \n"
                    for user in usersNonAuth :
                        response += user.realName +"\n"

            elif intent == "free_time":
                """
                    In this intent the user wants to know his own free time
                """
                freeTime = googleCalendar.get_response(userList[0], intent)
                if freeTime is None : 
                    response = "No upcoming events found."
                else:
                    response = "Here is your free time"
                    for period in freeTime:
                        attachmentObject = {}
                        attachmentObject['color'] = COLOR_LIST[0]
                        startFreeTime = period[0].strftime("%I:%M %p %D")
                        endFreeTime = period[1].strftime("%I:%M %p %D")
                        if lang != 'en':
                                attachmentObject['title'] = watsonTranslator.translateText("From " + startFreeTime + " to " + endFreeTime, 'en', lang)
                        else: 
                            attachmentObject['title']= "From " + startFreeTime + " to " + endFreeTime
                        attachments.append(attachmentObject)
            elif intent == "workers_free_time":
                """
                    In this intent the user wants to know a coworker free time
                """
                i = 0
                usersNonAuth= []
                if len(userList) > 1 :
                    for index, user in enumerate(userList):
                        if googleCalendar.get_credentials(user.id) is None :
                            usersNonAuth.append(user)
                        elif (index != 0) :
                            i = 0 if i == 7 else i
                            attachmentObject = {}
                            attachmentObject['color'] = "#FFFFFF"
                            attachmentObject['title']= user.realName

                            attachments.append(attachmentObject)
                            freeTime = googleCalendar.get_response(user, intent)
                            if freeTime is None:
                                attachmentObject = {}
                                if lang != 'en':
                                    attachmentObject['title'] = watsonTranslator.translateText("No upcoming events found.", 'en', lang)
                                else: 
                                    attachmentObject['title'] = "No upcoming events found."
                                attachments.append(attachmentObject)
                            else:
                                for period in freeTime:
                                    attachmentObject = {}
                                    startFreeTime = period[0].strftime("%I:%M %p %D")
                                    endFreeTime = period[1].strftime("%I:%M %p %D")
                                    if lang != 'en':
                                        attachmentObject['title'] = watsonTranslator.translateText("From " + startFreeTime + " to " + endFreeTime, 'en', lang)
                                    else: 
                                        attachmentObject['title']= "From " + startFreeTime + " to " + endFreeTime
                                    attachmentObject["color"] = COLOR_LIST[i]
                                    attachments.append(attachmentObject)
                            i += 1
                    
                    if len(usersNonAuth) == 0 :
                        response = "Here is your free time and your co-workers's free time"
                    else :
                        response = "The following users must start authorization process first: \n"
                        for user in usersNonAuth :
                            response += user.realName +"\n"
                else : 
                    reposne = "Sorry, If you want me to find information about someone, type his/her slack name such as @name"
            elif intent == "create_event":
                """
                    In this intent the user wants to schedule a event in his calendar.
                    He also may want to invite others to the meeting.
                """
                userMailList = []
                for index, user in enumerate(userList) : 
                    if index != 0:
                        userMailList.append({"email": user.email})        

                #Getting start and end datetime and location from watson entities.
                datesEntities = [ entity for entity in entities if entity[0]=="sys-date"]
                timesEntities = [ entity for entity in entities if entity[0]=="sys-time"]
                locationEntities = [ entity for entity in entities if entity[0]=="location"]
                location = locationEntities[0][1] if locationEntities else ""
                #building datetime using dates and times
                if len(datesEntities) > 0 and len(timesEntities) > 1 :
                    start = datesEntities[0][1] + "T" + timesEntities[0][1]
                    #getting last time as an end time, sometimes watson duplicate times.
                    if len(timesEntities) > 2 :
                        endTime = timesEntities[len(timesEntities) - 1][1]
                    else :
                        endTime = timesEntities[1][1]
                    if len(datesEntities)<2:
                        end = datesEntities[0][1] + "T" + endTime
                    else:
                        end = datesEntities[1][1] + "T" + endTime
                else  :
                    start = None
                    end = None

                timeZone = userList[0].timeZone

                if start is None or end is None or start > end :
                    response = "There was a problem with your event. \n Be sure you wrote at least one Date and two hours."
                else :
                    googleCalendar.post_event(userList[0], userMailList, summary, location, timeZone, start, end)

                    text = "From " + datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p %D") + \
                    " to " + datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p %D")
                    if userMailList:
                        text += "\n People with the following emails has been invited: \n"
                        for userMail in userMailList:
                            text += userMail["email"] + "\n"
                    
                    response = "New event created"

                    if lang != 'en':
                        text = watsonTranslator.translateText(text, 'en', lang)
                        
                    attachments = [{
                        "title": "'"+summary+ "'",
                        "text": text,
                        "callback_id": "new_schedule",
                        "color": "#3AA3E3",
                    }]
                
            elif intent == "find_free_time" : 
                userFreeTimeList = []
                usersNonAuth= []
                for user in userList:
                    if googleCalendar.get_credentials(user.id) is None :
                        usersNonAuth.append(user)
                    else :
                        free = googleCalendar.get_freetime(user,5)
                        if free is not None :
                            userFreeTimeList.append(free)
                freeTime = googleCalendar.get_freeTimeBtwPeople(userFreeTimeList)
                if len(usersNonAuth) > 0 :
                        response = "The following users must start authorization process first: \n"
                        for user in usersNonAuth :
                            response += user.realName +"\n"
                elif freeTime is None or len(freeTime) == 0 :
                    reponse = "Everyone is busy"
                else :
                    response = "Here is the time when everyone is available:"

                    for period in freeTime:
                            attachmentObject = {}
                            attachmentObject['color'] = COLOR_LIST[0]
                            startFreeTime = period[0].strftime("%I:%M %p %D")
                            endFreeTime = period[1].strftime("%I:%M %p %D")
                            if lang != 'en':
                                    attachmentObject['title'] = watsonTranslator.translateText("From " + startFreeTime + " to " + endFreeTime, 'en', lang)
                            else: 
                                attachmentObject['title']= "From " + startFreeTime + " to " + endFreeTime
                            attachments.append(attachmentObject)

            else:
                response = responseFromWatson['output']['text'][0]

    #if language is not english the response is translated.
    if lang != 'en':
        response = watsonTranslator.translateText(response, 'en', lang)
    try :     
        slack_client.api_call("chat.postMessage", as_user=True, channel=channel, text=response,
                      attachments=attachments)
    except :
        print("ERROR trying to reponse to slack client.")


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        This parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip(), \
                       output['channel'], output['user']
    return None, None, None

def get_user(userid, isCurrentUser) :
    """
        This function calls slack api to get the information of a give user id.
        Returns: User object
    """
    try :
        userJsonResponse = slack_client.api_call(
            "users.info",
            user=userid,
            token=watson_conversation_workspace
        )

        userJson = json.loads(json.dumps(userJsonResponse))["user"]
        userProfileJson=userJson["profile"]
        realName = userProfileJson["real_name"]
        email = userProfileJson["email"]
        timeZone = userJson["tz"]
        isCurrentUser = isCurrentUser
        return User(userid, realName, email, timeZone, isCurrentUser)
    except :
        return False

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            _command, channel, user = parse_slack_output(slack_client.rtm_read())
            if _command and channel and user:
                command = _command.encode('utf-8')
                userList = []
                userList.append(get_user(user, True))
                if command :
                    users_noprefix= [u.replace('<@','') for u in re.findall("<@[\w]*>",command)]
                    users = [u.replace('>','') for u in users_noprefix]
                    for user in users:
                        userList.append(get_user(user, False))
                if command:
                    command= re.sub('<@[\w]*>', 'someone', command, flags=re.IGNORECASE)

                handle_command(command, channel, userList)
                
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")