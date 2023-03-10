# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from rasa_sdk import Action, Tracker, ValidationAction
from rasa_sdk.executor import CollectingDispatcher
from thefuzz import fuzz, process
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import os
import sqlite3

from .gpt3_fallback import ActionGPT3Fallback

class ActionConfirmAppointment(Action):
    def name(self) -> Text:
        return "action_confirm_appointment"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        order = tracker.get_slot("ordinal")
        time = tracker.get_slot("time_appointment")
        name_professor_list = tracker.get_slot("name_professor_list")
        if not order or not time or not name_professor_list:
            return []
        dispatcher.utter_message(f"Just to confirm, your appointment with {name_professor_list[order-1]} is scheduled on {time.lower()}~")
        return [SlotSet("name_professor", name_professor_list[order-1])]
            
class ActionSetAppointment(Action):
    def name(self) -> str:
        return "action_set_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        # get the values of the required slots
        name_professor = tracker.get_slot("name_professor")
        # time_appointment = tracker.get_slot("time_appointment")
        name_user = tracker.get_slot("name_user")
        time = tracker.get_slot("time_appointment")
        # connect to the database
        conn = sqlite3.connect('./appointments.db')
        c = conn.cursor()
        # create the appointments table if it doesn't exist
        # c.execute('''CREATE TABLE IF NOT EXISTS appointments (name_user text, name_professor text, time_from text, time_to text, time_type, time_grain)''')
        c.execute('''CREATE TABLE IF NOT EXISTS appointments (name_user text, name_professor text, time_body text)''')
        # insert the appointment into the database

        # if time and time["type"] == "value":
        #     c.execute("INSERT INTO appointments VALUES (?, ?, ?, ?, ?)", (name_user, name_professor, time["value"], None, "value", time["grain"]))
        # elif time and time["type"] == "value":
        #     c.execute("INSERT INTO appointments VALUES (?, ?, ?, ?, ?)", (name_user, name_professor, time["from"]["value"], time["to"]["value"], "interval", time["from"]["grain"]))

        c.execute("INSERT INTO appointments VALUES (?, ?, ?)", (name_user, name_professor, time))

        # commit the changes and close the database connection
        conn.commit()
        conn.close()
        if time:
            dispatcher.utter_message(f"All set! We will now send a confirmation email to {name_professor}.")
        # set the slots to None to clear them
        return [SlotSet("time_appointment", None)]

class ActionFetchProfessorRoom(Action):
    def name(self) -> str:
        return "action_fetch_professor_room"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        name_professor = tracker.get_slot("name_professor")
        
        office_room = findProfessorOffice(name_professor)
        if office_room:
            #dispatcher.utter_message(f"The office room of {name_professor} is {office_room}")
            dispatcher.utter_message(text=f"The office room of {name_professor} is {office_room}")
            # return [SlotSet("office_room", office_room)]
            return []
        else:
            # dispatcher.utter_message("Sorry I couldn't find this professors info.")
            return []

class ActionResetAppointmentForm(Action):

    def name(self) -> Text:
        return "action_reset_appointment_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("name_professor", None), SlotSet("time_appointment", None),SlotSet("ordinal", None), SlotSet("name_professor_list", None)]

class ActionResetOfficeForm(Action):

    def name(self) -> Text:
        return "action_reset_office_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("name_professor", None),SlotSet("ordinal", None), SlotSet("name_professor_list", None)]
       
class ActionResetNameMe(Action):

    def name(self) -> Text:
        return "action_reset_name_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("name_user", None)]

class ActionStart(Action):
    def name(self) -> Text:
        return "action_start"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        # an `action_listen` should be added at the end as a user message follows
        events.append(ActionExecuted("action_listen"))

        return events

def findProfessorName(name_professor:str):
    if(len(name_professor)>=3):
        data = pd.read_csv("actions/office_name.csv", sep=";", encoding = 'unicode_escape')

        for _, row in data.iterrows():
            row['n'] = fuzz.ratio(name_professor.upper() , str(row['n']))
        
        data.sort_values('n',ascending = False,inplace=True)        
        threshold = data.iloc()[0][2]*0.9
        data = data[data['n'] > threshold]
        data.drop_duplicates(subset='fn', keep='first', inplace=True)
        return data['fn'].tolist()
    else:
        return None

def findProfessorOffice(name_professor:str):
    data = pd.read_csv("actions/stuff.csv")
    mask = data['NOMBRE']== name_professor
    if data[mask].empty:
        return None
    else:
        return data[mask]['DESPACHO'].values[0]
        
def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

class ValidateAllSlots(ValidationAction):
    def name(self) -> Text:
        return "action_validate_slot_mappings"

    def validate_name_professor(
      self, slot_value: Any, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        name_professor = slot_value
        name_professor_list=[]
        name_professor_list = findProfessorName(name_professor)
        if name_professor_list:
            if len(name_professor_list) > 1:
                return {"name_professor_list": name_professor_list, "ordinal": None}
            elif len(name_professor_list) == 1:
                return {"name_professor_list": name_professor_list, "ordinal": 1, "requested_slot": None}
        else:
            dispatcher.utter_message("Sorry, we can't find anyone with this name.")
            return {}
        
    def validate_time_appointment(
      self, slot_value: Any, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        time = tracker.latest_message['entities'][0]['text']
        return {"time_appointment": time}

class ActionAskAppointmentFormOrdinal(Action):
    def name(self) -> Text:
        return "action_ask_appointment_form_ordinal"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        name_professor_list = tracker.get_slot("name_professor_list")
        buttonList = []
        if name_professor_list:
            if len(name_professor_list) > 1:
                for i in range(len(name_professor_list)):
                    buttonList.append({"payload": ordinal(i+1), "title": name_professor_list[i]})
                dispatcher.utter_message(
                    text="It seems that there are several people with this name. Could you please select the one you're referring to?",
                    buttons=buttonList,
                )
            elif len(name_professor_list) == 1:
                return [SlotSet("ordinal", 1)]
        else:
            return []

class ActionAskOfficeFormOrdinal(Action):
    def name(self) -> Text:
        return "action_ask_office_form_ordinal"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        name_professor_list = tracker.get_slot("name_professor_list")
        buttonList = []
        if name_professor_list:
            if len(name_professor_list) > 1:
                for i in range(len(name_professor_list)):
                    buttonList.append({"payload": ordinal(i+1), "title": name_professor_list[i]})
                dispatcher.utter_message(
                    text="It seems that there are several people with this name. Could you please select the one you're referring to?",
                    buttons=buttonList,
                )
            elif len(name_professor_list) == 1:
                return [SlotSet("ordinal", 1)]
        else:
            return []

class ActionConfirmNameOffice(Action):
    def name(self) -> Text:
        return "action_confirm_name_office"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        name_professor_list = tracker.get_slot("name_professor_list")
        order = tracker.get_slot("ordinal")
        if name_professor_list and order:
            dispatcher.utter_message(
                text=f"Are you looking for {name_professor_list[order-1]}?"
            )
            return [SlotSet("name_professor", name_professor_list[order-1])]
        else:
            return []

class ActionMap(Action):
    def name(self) -> Text:
        return "action_map"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        origin = tracker.get_slot("origin")
        destination = tracker.get_slot("destination")
        if not origin:
            origin = "place_id:ChIJj7h5wzyjpBIROJNdwFWz97k" # Tanger building
            dispatcher.utter_message(custom=[map(origin,destination)])
            return [SlotSet("origin", None),SlotSet("destination", None)]
        elif not destination:
            return [SlotSet("origin", None),SlotSet("destination", None)]
        else:
            dispatcher.utter_message(custom=[map(origin,destination)])
            return [SlotSet("origin", None),SlotSet("destination", None)]

class ActionEvents(Action):
    def name(self) -> Text:
        return "action_events"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        url = 'https://eventum.upf.edu/'
        selector = '#upcoming > div.row.event-card-container > div'

        with urllib.request.urlopen(url) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            divs = soup.select(selector)
            chunk = ''
            for i in range(3):
                try:
                    divs[i].find('a', {"class": "o_card__button"}).decompose()
                except:
                    pass
                chunk += str(divs[i]).replace('src="/','src="https://eventum.upf.edu/')
            dispatcher.utter_message(custom=[chunk])
            # for div in divs:
            #     sub_div = div.select_one('div > div')
            #     print(sub_div)
        return []
    
class ActionReadings(Action):
    def name(self) -> Text:
        return "action_readings"

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        iframe = '<iframe class= "calender" frameborder="0" width="600" height="500" scrolling="no" src="https://calendar.google.com/calendar/b/1/embed?showTitle=0&amp;mode=AGENDA&amp;height=800&amp;wkst=2&amp;bgcolor=%23FFFFFF&amp;src=upf.edu_7haufqkt5je4vjat0oos01var0%40group.calendar.google.com&amp;color=%23875509&amp;src=upf.edu_r21r1qqqhfhq9jrbo8uf927hc8%40group.calendar.google.com&amp;color=%235F6B02&amp;src=upf.edu_4r1fbqh71lg3acsvfucnl8ud6k%40group.calendar.google.com&amp;color=%23c8102e&amp;src=upf.edu_s4lv7tk0med4uc5bed7vgpdt3k%40group.calendar.google.com&amp;color=%2342104A&amp;src=upf.edu_k4aomjbdqhke8s518u027oejt0%40group.calendar.google.com&amp;color=%23333333&amp;src=upf.edu_nspmrvsm8b2p98k7qdor7o06i8%40group.calendar.google.com&amp;color=%2323164E&amp;src=upf.edu_m451scd01bnikdut0l4j2vp2m8%40group.calendar.google.com&amp;color=%232952A3&amp;src=upf.edu_mf241kap986is84pn5p68dg7uk%40group.calendar.google.com&amp;color=%23865A5A&amp;src=upf.edu_p1116ugskrd9858200184uuneg%40group.calendar.google.com&amp;color=%238C500B&amp;src=upf.edu_5veerfbk6dj26dr1fudk0ugbcg%40group.calendar.google.com&amp;color=%2328754E&amp;src=upf.edu_dfidh32drpt038m8lla9ife6g0%40group.calendar.google.com&amp;color=%2323164E&amp;ctz=Europe%2FMadrid" style="border-width:0;width: calc(100% + 70px);"  __idm_id__="44883969"></iframe>'
        dispatcher.utter_message(custom=[iframe])
        return []
    
def map(origin,destination):
    google_map_key= 'AIzaSyDD3X9nf5-eJGND24uVLuO6EOXRO6pjl58'
    mapIframe=f'<iframe height="300" style="border:0;width: calc(100% + 80px);" loading="lazy" allowfullscreen="" src="https://www.google.com/maps/embed/v1/directions?mode=transit&amp;origin={origin}&amp;destination={destination}&amp;key={google_map_key}"></iframe>'
    return mapIframe

# def findProfessorName(name_professor:str):
#     if(len(name_professor)>=3):
#         data = pd.read_csv("actions/stuff.csv")
#         fristName_f = pd.read_csv('actions/firstName_split_f.csv')
#         fristName_s = pd.read_csv('actions/firstName_split_s.csv')
#         lastName_f  = pd.read_csv('actions/lastName_split_f.csv')
#         lastName_s = pd.read_csv('actions/lastName_split_s.csv')
#         firstNameList_f = {}
#         firstNameList_s = {}
#         lastNameList_f = {}
#         lastNameList_s = {}
#         fullGroupName = {}

#         for index, row in fristName_f.iterrows():
#             irr = fuzz.ratio(name_professor.upper() , str(row['f']))
#             if (irr >= 60):
#                 firstNameList_f[index]=[irr]
#         for index, row in fristName_s.iterrows():
#             irr = fuzz.ratio(name_professor.upper() , str(row['s']))
#             if (irr >= 60):
#                 firstNameList_s[index]=[irr]

#         for index, row in lastName_f.iterrows():
#             irr = fuzz.ratio(name_professor.upper() , str(row[0]))
#             if (irr>=60):
#                 lastNameList_f[index] = [irr]
#         for index, row in lastName_s.iterrows():
#             irr = fuzz.ratio(name_professor.upper() , str(row[0]))
#             if (irr>=60):
#                 lastNameList_s[index] = [irr]

#         fullGroupName.update(firstNameList_f)
#         fullGroupName.update(firstNameList_s)
#         fullGroupName.update(lastNameList_f)
#         fullGroupName.update(lastNameList_s)
#         maxIrr = max(fullGroupName.values())
#         listAim =[maxIrr[0]*0.9]
#         fullGroupName2={k:v for k,v in fullGroupName.items()  if v>=listAim}

#         fullGroupNameSorted = sorted(fullGroupName2.items(),key = lambda x:x[1],reverse = True)
#         df_finalNameIndex = pd.DataFrame.from_dict(fullGroupNameSorted)
#         df_finalNameIndex.set_index([0], inplace=True)
#         finalNameList = []
#         for i in df_finalNameIndex.index:
#             finalNameList.append(data.loc[i,'NOMBRE'])

#         #giveyourNameList = list(set(finalNameList))
#         if(finalNameList):
#             return finalNameList
#     else:
#         return None