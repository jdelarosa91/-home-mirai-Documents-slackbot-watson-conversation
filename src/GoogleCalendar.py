from __future__ import print_function
from apiclient import discovery
from oauth2client import client
from oauth2client import tools

import logging
import datetime
import os
import time
import httplib2
import json
import oauth2client
    

class GoogleCalendar(object):

    logging.basicConfig()
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    FLOW_MAP = {}
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Google Calendar API Python Quickstart'
     # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json    
    
    def get_credentials(self,user):
        """
            Gets valid user credentials from storage.
            If nothing has been stored, or if the stored credentials are invalid,
            the OAuth2 flow is completed to obtain the new credentials.
            Returns:
                Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'calendar-python-quickstart-' + user + '.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        return credentials

    def get_auth_url(self,user):
        """ 
            Creates a Flow Object from a clients_secrets.json which stores client parameters
            like client ID, client secret and other JSON parameters.
            Returns:
                Authorization server URI.
        """
        existing_flow = self.FLOW_MAP.get(user)
        if existing_flow is None:
            #urn:ietf:wg:oauth:2.0:oob to not redirect anywhere, but instead show the token on the auth_uri page
            try: 
                flow = client.flow_from_clientsecrets(filename = self.CLIENT_SECRET_FILE, scope = self.SCOPES, redirect_uri = "urn:ietf:wg:oauth:2.0:oob")
                flow.user_agent = self.APPLICATION_NAME
                auth_url = flow.step1_get_authorize_url()
                print(auth_url)
                self.FLOW_MAP[user] = flow
                return auth_url
            except:
                return False
        else:
            return existing_flow.step1_get_authorize_url()

    def set_auth_token(self, user, token):
        """ 
            Exchanges an authorization flow for a Credentials object.
            Passes the token provided by authorization server redirection to this function.
            Stores user credentials.
        """
        flow = self.FLOW_MAP.get(user)
        if flow is not None:
            try:
                credentials = flow.step2_exchange(token)
            except oauth2client.client.FlowExchangeError:
                return -1

            home_dir = os.path.expanduser('~')
            credential_dir = os.path.join(home_dir, '.credentials')
            if not os.path.exists(credential_dir):
                os.makedirs(credential_dir)
            credential_path = os.path.join(credential_dir,
                                           'calendar-python-quickstart-' + user + '.json')

            store = oauth2client.file.Storage(credential_path)
            print("Storing credentials at " + credential_path)
            store.put(credentials)
            return 0
        else:
            return None

    def get_events(self, user):
        """
            This function gets a list of events for an user
            Returns: List of events
        """
        try:
            credentials = self.get_credentials(user.id)

            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)

            now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
            print('Getting the upcoming events')
            eventsResult = service.events().list(
                calendarId='primary', timeMin=now, maxResults=999, singleEvents=True,
                orderBy='startTime').execute()
            return eventsResult.get('items', [])
        except:
            return False

    def get_freetime(self, user, maxDays):
        """
            This function gets the free time for an user in the next days from now().
            Returns: List of (datetime, datetime) with free time.
        """
        _events = self.get_events(user)
        if _events == False :
            return False
        else :
            events = []
            dateToday = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            """
                First of all, function removes every event after now + maxDays.
                They are also removed events in days when there is already a All day event.
            """
            lastEvent = None
            isAllDayEvent = False
            for event in _events:
                if 'dateTime' in event['start'] :
                    start = datetime.datetime.strptime(event['start']['dateTime'][:-6],"%Y-%m-%dT%H:%M:%S")
                else:
                    start = datetime.datetime.strptime(event['start']['date'],"%Y-%m-%d").replace(hour=0)
                if lastEvent and lastEvent[1] < start : 
                    isAllDayEvent = False
                if 'dateTime' in event['end'] :
                    end = datetime.datetime.strptime(event['end']['dateTime'][:-6],"%Y-%m-%dT%H:%M:%S")
                else:
                    end = datetime.datetime.strptime(event['end']['date'],"%Y-%m-%d").replace(hour=23,minute=59) - datetime.timedelta(days=1)
                if start <= (dateToday + datetime.timedelta(days=maxDays)) and not isAllDayEvent:
                    events.append((start, end))
                if start.hour == 0 or end.hour == 0:
                    isAllDayEvent = True
                lastEvent = (start, end)
            events.sort(key=lambda tup: tup[0])
            
            """
                If there is no event, empty days from 9 am to 19 pm are created. 
            """
            print ("Calculating free time")
            if not events:
                freeTimeSchedule = []
                response = "You are free"
                i=0
                
                startDate = dateToday.replace(hour=9)
                endDate = dateToday.replace(hour=19)
                while i <= maxDays :
                    if i == 0:
                        #first free time starts from now() and not from 9 am
                        today = datetime.datetime.now()
                        if today.weekday() < 5 :
                            freeTimeSchedule.append((today.replace(second=0, microsecond=0), endDate))
                    else :
                        if startDate.weekday() < 5 :
                            freeTimeSchedule.append((startDate, endDate))
                    startDate += datetime.timedelta(days=1)
                    endDate += datetime.timedelta(days=1)
                    i += 1
            else:
                """
                    If there are some events, function creates a list of free time tuples with start and     
                    end time between events.
                """
                freeTime = []

                for index, event in enumerate(events):
                    startDate = event[0]
                    endTime = event[1]

                    if index == 0 :
                        nowTime = datetime.datetime.now()
                        if nowTime < startDate : 
                            freeTime.append((datetime.datetime.now().replace(second=0, microsecond=0), startDate))
                        if index < len(events)-1 :
                            nextStartDate = events[index+1][0]
                            nextEndDate = events[index+1][1]
                            if endTime < nextStartDate :
                                freeTime.append((endTime, nextStartDate))
                        else :
                        	freeTime.append((endTime, endTime.replace(hour=19, minute=0, second=0)))
                    elif index < len(events)-1:
                        nextStartDate = events[index+1][0]
                        endLastDate = events[index - 1][1]
                        if endTime < nextStartDate and startDate > endLastDate:
                            freeTime.append((endTime, nextStartDate))
                    else:
                        endSchedule = endTime.replace(hour=19, minute=0, second=0)
                        endLastDate = events[index - 1][1]
                        if endTime < endSchedule and startDate > endLastDate:
                            freeTime.append((endTime, endSchedule))
                lastDay = events[len(events) - 1][1].replace(hour=0, minute=0, second=0)

                #if there are more days from the last event end time to the max days, empty days are inserted

                if (dateToday + datetime.timedelta(days=maxDays))> lastDay:
                    diff_empty_days = (dateToday + datetime.timedelta(days=maxDays) - lastDay).days
                    i=0
                    while i<diff_empty_days :
                        lastDay += datetime.timedelta(days=1)
                        freeTime.append((lastDay.replace(hour=9), lastDay.replace(hour=19)))
                        i += 1

                """
                    Once function calculated an array with free time, it is going to be split to get 
                    days fitting the schedule (from 9 am to 7 pm) and avoiding weekends.
                """
                freeTimeSchedule = []
                for index, free in enumerate(freeTime):
                    aux_init = free[0].replace(hour=19)
                    aux_fin = free[1].replace(hour=9)
                    diff_days = (aux_fin.replace(hour=0) - aux_init.replace(hour=0)).days
                    initialScheduleStart = free[0].replace(hour=9, minute=0, second=0)
                    initialScheduleEnd = free[0].replace(hour=19, minute=0, second=0)
                    endScheduleStart = free[1].replace(hour=9, minute=0, second=0)
                    endScheduleEnd = free[1].replace(hour=19, minute=0, second=0)                 
                    if free[0] < initialScheduleStart:
                        startFree = initialScheduleStart 
                    else :
                        startFree = free[0]
                    if free[1] > endScheduleEnd:
                        endFree = endScheduleEnd
                    elif free[1] < endScheduleStart:
                        endFree = endScheduleStart
                    else :
                        endFree = free[1]
                    if diff_days == 0 and free[1].day == free[0].day and startFree.weekday() < 5:
                        freeTimeSchedule.append((startFree, endFree))
                    else:
                            newEnd = free[0].replace(hour=19, minute=0, second=0)
                            if (startFree < newEnd and startFree.weekday() < 5):
                                freeTimeSchedule.append((startFree, free[0].replace(hour=19, minute=0, second=0)))
                            if diff_days > 0:
                                initialDate = free[0].replace(hour=9, minute=0, second=0)
                                finishDate = free[0].replace(hour=19, minute=0, second=0)
                                i = 0
                                while i < diff_days:
                                    initialDate += datetime.timedelta(days=1)
                                    finishDate += datetime.timedelta(days=1)
                                    if initialDate.weekday() < 5 :
                                        freeTimeSchedule.append((initialDate,finishDate))
                                    i += 1
                                if free[1].weekday() < 5 :
                                    freeTimeSchedule.append((free[1].replace(hour=9, minute=0, second=0),endFree))
                            else :
                                newStart = free[1].replace(hour=9, minute=0, second=0)
                                if (diff_days >= 0 and newStart != endFree and newStart.weekday() < 5 ):
                                    freeTimeSchedule.append((newStart, endFree))       
            return freeTimeSchedule


    def get_schedule(self, user, maxDays):
        """
            Return the calendar for a specific user and for a specific
            period of days.
            Returns: List of Calendar items, with Title, text and summary.
        """
        events = self.get_events(user)
        if events == False :
            return False
        else :
            calendarList = []
            if not events:
                calendarList = []
            for event in events:
            	calendarItems = {}
                if 'dateTime' in event['start'] :
                    startDate = datetime.datetime.strptime(event['start']['dateTime'][:-6],"%Y-%m-%dT%H:%M:%S")
                    calendarItems['isAllDay'] = False
                else:
                    startDate = datetime.datetime.strptime(event['start']['date'],"%Y-%m-%d")
                    calendarItems['isAllDay'] = True
                if(datetime.datetime.utcnow() + datetime.timedelta(days=maxDays)<startDate) :
                    break
                calendarItems['summary'] = event['summary'] if 'summary' in event else "No title"
                calendarItems['start'] = startDate
                calendarList.append(calendarItems)
            return calendarList


    def get_freeTimeBtwPeople(self, userList):
        """
            Divide and conquer: having a list of users to calculate free time beetwen them,
            the list is split and this function is called recursivily. The two results are calculating
            using freeTimeBtw2Users function.
            Returns: List of free time (dateTime, dateTime)
        """
        if len(userList) == 1 : 
            return userList[0]
        elif len(userList) == 2 : 
            return self.freeTimeBtw2Users(userList[0], userList[1])
        else :
            middle = len(userList) / 2
            firstList = self.get_freeTimeBtwPeople(userList[0:middle])
            secondList = self.get_freeTimeBtwPeople(userList[middle:len(userList)])
            if firstList == False or secondList == False :
                return False
            else :
                return self.freeTimeBtw2Users(firstList, secondList)

        
    def freeTimeBtw2Users(self, userList1, userList2):
        """
            This function calculate the free time between 2 users.
            Both list must be sorted.
            Returns: List of free time (dateTime, dateTime)
        """
        if userList1 == False or userList2 == False : 
            return False
        else :
            if userList1 and userList2:
                freeTime = []
                j = 0
                i = 0
                while i < len(userList1) and j<len(userList2) :
                    if userList1[i][1] < userList2[j][0]: 
                        i += 1
                    elif userList1[i][0] > userList2[j][1]:
                        j += 1
                    else :
                        start = max(userList1[i][0], userList2[j][0])
                        end = min(userList1[i][1], userList2[j][1])
                        if end == userList1[i][1] :
                            i += 1
                        else:
                            j += 1
                        if end > start :
                            freeTime.append((start, end))
                return freeTime

            else : 
                return userList1 if userList1 else userList2


    def post_event(self, user, userMailList, summary, location, timeZone, start, end):
        """
            Post and event in user's calendar and send invitations to the user mail list.
        """
        event = {
            'summary': summary,
            'location': location,
            'start': {
            'dateTime': start,
            'timeZone': timeZone,
            },
            'end': {
            'dateTime': end,
            'timeZone': timeZone,
            },
            'attendees': userMailList,
        }
        try :
            credentials = self.get_credentials(user.id)

            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)
            event = service.events().insert(calendarId='primary', sendNotifications='true', body=event).execute()
            return True
        except : 
            return False


    def get_response(self, user, intent):
        """
            Handle every possible iteraction with the calendar
        """
        if intent == "workers_schedule" :
            return self.get_schedule(user, 7)
        if intent == "schedule_within_30d":
            return self.get_schedule(user, 30)
        if intent == "schedule_within_30d" or intent == "schedule_longterm":
            return self.get_schedule(user, 365)
        if intent == "free_time":
            return self.get_freetime(user, 7)
        if intent == "workers_free_time":
            return self.get_freetime(user, 3)