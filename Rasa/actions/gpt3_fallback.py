import openai
import os
#from dotenv import load_dotenv
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

#load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class ActionGPT3Fallback(Action):
    def name(self) -> str:
        return "action_gpt3_fallback"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="That is a bit out of scope, but here is what I know.")
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

# name entity prompt:
# Extract name entity from text with two possible role: 'user' and 'professor'. 

# Example: Do you know where is Marti?
# Output: [{name: Marti; role: professor}]

# Example: My name is Jose.
# Output: [{name: Jose; role: user}]

# I'm Jack and I am looking for Nuria.
# Output: [{name: Jack; role: user}, {name: Nuria; role: professor}]

# group entity prompt:
# Extract 'group' entity from text with several possible name: 
# MTG: Music Technology Group
# Natural Language Processing
# NETS Network Technologies and Strategies Group
# NTSA: Nonlinear Time Series Analysis Group
# Physense: Sensing in Physiology and Biomedicine Group
# SIMBIOsys: Simulation, Imaging and Modelling for Biomedical Systems
# TALN; Natural Language Processing
# TIDE: Interactive & Distributed Technologies for Education
# UBICALAB: Ubiquitous Computing Applications Lab
# WN: Wireless Networking Group
# WSSC: Web Science and Social Computing

# Example: Do you know who is in Music Group?
# Output: [{group: MTG; fgroup: Music Technology Group}]

# Example: What's the full name of tide?
# Output:  [{group: TIDE; fgroup: Interactive & Distributed Technologies for Education}]

# Do you know where is the Natural Language group?
# Output: [{group: NLP; fgroup: Natural Language Processing}]

# direction request
# Extract location entity from text with two possible role: 'destination' and 'departure'. 

# Example: Do you know where is the Glories?
# Output: [{name: Glories; role: destination}]

# Example: Do you know how to get to the Sagrada Familia from Glories?
# Output: [{name: Glories; role: departure},{name: Sagrada Familia; role: destination}]

# Example: Do you know how to get to the Plaza Catalunya?
# Output:  [{name: Plaza Catalunya; role: destination}]