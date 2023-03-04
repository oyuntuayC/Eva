import openai
import os
#from dotenv import load_dotenv
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

#load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")
#openai.api_key = "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"
openai.api_key = "sk-1psKe0vLCz4mlPj9"

class ActionGPT3Fallback(Action):
    def name(self) -> str:
        return "action_gpt3_fallback"
    
    def run(self, dispatcher, tracker, domain):
        request = " ".join(tracker.latest_message['text'].split()[1:])
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"{request}",
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        ).choices[0].text
        dispatcher.utter_message(text=response)
        #return [SlotSet("request", request), SlotSet("response", response)]
        return []