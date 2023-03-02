
#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import requests

import speech_recognition as sr

# POST API of rasa
url = 'http://localhost:5005/webhooks/rest/webhook'
# Request body
req = {'message':''}

# obtain audio from the microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    while True:
        audio = r.listen(source)
        # recognize speech using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            text = r.recognize_google(audio)
            print("Me: " + text)
            req['message'] = text
            res = requests.post(url, json = req)
            #print("Rasa: " + res.json()[0]['text'])
            print(res.json())
        except sr.UnknownValueError:
            
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))