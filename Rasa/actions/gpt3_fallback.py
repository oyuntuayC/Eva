import openai
import os
#from dotenv import load_dotenv
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

#load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")
#openai.api_key = "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"
openai.api_key = "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"

class ActionGPT3Fallback(Action):
    def name(self) -> str:
        return "action_gpt3_fallback"
    
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="That is a bit out of scope, but here is what I know.")
        request = tracker.latest_message['text']
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an AI assistant in the Tanger building of University of Pompeu Fabra. You are helpful, clever, and very friendly. You give very concise answers."},
                {"role": "user", "content": request}
            ],
            temperature=0.8,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        ).choices[0].message.content
        dispatcher.utter_message(text=response)
        #return [SlotSet("request", request), SlotSet("response", response)]
        return []

# entity example prompt:
# Extract name entity from text with two possible role: 'user' and 'professor'. 

# Example: Do you know where is Marti?
# Output: [{name: Marti; role: professor}]

# Example: My name is Jose.
# Output: [{name: Jose; role: user}]

# I'm Jack and I am looking for Nuria.
# Output: [{name: Jack; role: user}, {name: Nuria; role: professor}]