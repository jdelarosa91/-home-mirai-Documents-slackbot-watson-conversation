from watson_developer_cloud import LanguageTranslatorV2 as LanguageTranslator
from watson_developer_cloud import ConversationV1

import json

class WatsonTranslator(object):
    """
    This Class allows to connect with Watson translation service using a particular account.
    """
    def __init__(self, username, password):
        
        self.language_translator = LanguageTranslator(
            username = username,
            password = password
        )

    def translateText(self, text,source,target):
        """
        This function translates a text from a source language to a target language.
        Returns: Text translated.
        """
        
        try: 
            translation = self.language_translator.translate(
                text = text,
                source = source,
                target = target
            )
            return json.dumps(translation, indent = 2, ensure_ascii = False).replace('"', '').replace("\\n", "\n") 
        except:
            return False


class WatsonConversation(object):
    """
    This class allows to connect with Watson Conversation service using a particular account and
    workspace.
    """
    def __init__(self, user, password, workspace):	
        self.conversation = ConversationV1(
            username = user,
            password = password,
            version = '2017-05-26'
        )

        self.workspace_id = workspace


    def responseFromWatson(self, input, context):
        """
        This function get a response from watson from a input text and a context.
        Response: json with Watson Response. (This json contains, response text, intents, entities, etc.)
        """
        try:
            return self.conversation.message(
                workspace_id = self.workspace_id,
                message_input = {'text': input},
                context = context
            )
        except:
            return False

