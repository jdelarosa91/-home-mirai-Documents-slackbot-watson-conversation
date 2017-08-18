# Slackbot + Watson Conversation + Watson translator

Slack chatbot that use natural language and multilanguage using Watson that allows to control Google calendar to do the following tasks:
* Get next events
* Get free time
* Get time available for a meeting
* Post a event in google calendar


## Getting Started

These instructions will allow you to run the program 

### Prerequisites

You need to instal the following things before running the program:
* Create a bot: https://api.slack.com/bot-users
* Create a slack APP: https://api.slack.com
* Google Calendar:
* Create a google calendar project: https://console.developers.google.com/flows/enableapi?apiid=calendar&authuser=1
* Create a service Watson conversation
* Import intents and entities from the excel file
* Activate: sys-time, sys-date
* Create a service Watson Translator
* Python 2/3
* PIP installed
* virtualenv installed

### Installing

First of all, the enviroment must be set up using the following code:

```
source bin/activate
```

After it, few libraries must be installed using the following command

```
pip install name_of_library
```
Libraries to install:
* watson_developer_cloud
* apiclient
* langdetect


## Deployment

To run the program just run the following code:
```
python src/SlackBot.py 
```
