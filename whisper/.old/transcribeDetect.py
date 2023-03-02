#! python3.7

import argparse
import io
import os
import speech_recognition as sr
import whisper
import torch
import requests

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="small", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--language", default=None,
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=100,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=0.5,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)  
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()
    
    # The last time a recording was retreived from the queue.
    phrase_time = None
    # Current raw audio bytes.
    last_sample = bytes()
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feauture where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramtically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False
    # POST API of rasa
    url = 'http://localhost:5005/webhooks/rest/webhook'
    # Request body
    req = {'message':''}
    # Important for linux users. 
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")   
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)
        
    # Load / Download model
    model = args.model
    if args.model != "large" and args.language == None:
        model = model + ".en"
    audio_model = whisper.load_model(model)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    temp_file = NamedTemporaryFile().name
    transcription = ['']
    
    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to recieve audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Cue the user that we're almost ready.
    print("Model loaded.\n")

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # Ready.
    os.system('cls' if os.name=='nt' else 'clear')
    print("Me: ....")

    while True:
        try:
            now = datetime.utcnow()
            # If enough time has passed between recordings, consider the phrase complete.
            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout) and text!=None:
                # Clear the current working audio buffer to start over with the new data.
                last_sample = bytes()
                # If we detected a pause between recordings, fix the current line.
                transcription[-1] = "Me: " + text
                # Translate request text
                if args.language!=None:
                    try:
                        text = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl="+ args.language +"&tl=en&q=\"" + text + "\"").json()[0][0][0]
                    except:
                        print("Get request translation failed")
                # Try post Rasa server.
                transcription.append("Rasa: " + "...." + text)
                freshScreen(transcription)
                req['message'] = text
                try:
                    res = requests.post(url, json = req).json()[0]['text']
                    # translate response text
                    if args.language!=None:
                        res = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=en&tl="+ args.language +"&q=\"" + res + "\"").json()[0][0][0]
                except:
                    print("Get response or translation failed")
                transcription[-1] = res
                freshScreen(transcription)
                # try:
                #     transcription.append("Rasa: " + res.json())
                #     # transcription.append("Rasa: " + res.json()[0]['text'])
                # except:
                #     transcription.append("Rasa: Hi!")
                # Clear audio data received during request
                while not data_queue.empty():
                    data = data_queue.get()
                transcription.append("Me: " + "....")
                # Clear the console to reprint the updated transcription.
                freshScreen(transcription)
                # Flush stdout.
                # print('', end='', flush=True)
                phrase_time = None


            # Pull raw recorded audio from the queue.
            if not data_queue.empty():

                # Concatenate our current audio data with the latest audio data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # make log-Mel spectrogram and move to the same device as the model
                mel = whisper.log_mel_spectrogram(last_sample).to(audio_model.device)
                # Use AudioData to convert the raw data to wav data.
                # audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                # wav_data = io.BytesIO(audio_data.get_wav_data())

                # Write wav data to the temporary file as bytes.
                # with open(temp_file, 'w+b') as f:
                #    f.write(wav_data.read())

                # Read the transcription.
                # result = audio_model.transcribe(temp_file, language=args.language, fp16=torch.cuda.is_available())
                result = audio_model.decode(mel, language=args.language, fp16=torch.cuda.is_available())
                text = result['text'].strip()
                
                # This is the time we finished transcribe audio data from the queue.
                phrase_time = datetime.utcnow()

                # edit the existing one.
                transcription[-1] = "Me: " + text + "...."

                # Clear the console to reprint the updated transcription.
                freshScreen(transcription)
                # Flush stdout.
                # print('', end='', flush=True)

                # Infinite loops are bad for processors, must sleep.
            sleep(0.25)
        except KeyboardInterrupt:
            break

def freshScreen(transcription):
    os.system('cls' if os.name=='nt' else 'clear')
    for line in transcription:
        print(line, flush=True)

if __name__ == "__main__":
    main()