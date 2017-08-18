# slackbot-watson-conversation
Slackbot using watson to handle team's calendar.

## Requirements:

### Slack:
* Create a bot: https://api.slack.com/bot-users
* Create a slack APP: https://api.slack.com
* Google Calendar:
* Create a google calendar project: https://console.developers.google.com/flows/enableapi?apiid=calendar&authuser=1

### IBM Watson:
* Create a service Watson conversation
* Import intents and entities from the excel file
* Activate: sys-time, sys-date
* Create a service Watson Translator

### Python:
* Python 2/3
* PIP installed
* virtualenv installed
* Necessay to install using "pip install <package_name> the following packages: watson_developer_cloud, apiclient, langdetect