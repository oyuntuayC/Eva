#! python3.7

import argparse
import io
import os
import speech_recognition as sr
import whisper
import torch
import requests
import numpy as np
import soundfile as sf

from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from google.cloud import texttospeech
from sys import platform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tiny", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--language", default=None,
                        help="Don't use the english model.")
    parser.add_argument("--phrase_timeout", default=0,
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
    # How much empty space between recordings before we consider it a new line in the transcription
    phrase_timeout = args.phrase_timeout
    # POST API of rasa
    url = 'http://localhost:5005/webhooks/rest/webhook'
    # Request body
    req = {'message':''}
    # Google tts client
    client = texttospeech.TextToSpeechClient()
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

    transcription = ['Me> ...']
    
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
    recorder.listen_in_background(source, record_callback)

    # Ready.
    os.system('cls' if os.name=='nt' else 'clear')
    print("Me> ...")
    while True:
        try:
            now = datetime.utcnow()
            # If enough time has passed between recordings, consider the phrase complete.
            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout) and text:
                # Clear the current working audio buffer to start over with the new data.
                last_sample = bytes()
                # If we detected a pause between recordings, fix the current line.
                transcription[-1] = "Me> " + text
                # Translate request text
                if args.language:
                    try:
                        text = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl="+ args.language +"&tl=en&q=\"" + text + "\"").json()[0][0][0].strip("\"“”「」‘’`")
                    except:
                        print("Get request translation failed")
                # Try post Rasa server.
                transcription.append("Rasa> " + ".....")
                freshScreen(transcription)
                req['message'] = text
                try:
                    res = requests.post(url, json = req).json()                    
                except:
                    res = [{"text":"Sorry I don't understand."}]
                # Translate response text
                try:
                    if args.language:
                        res[0]['text'] = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=en&tl="+ args.language +"&q=\"" + res[0]['text'] + "\"").json()[0][0][0].strip("\"“”「」‘’`")
                except:
                    pass
                # Update Rasa's response
                transcription[-1] = "Rasa> "
                for i in range(len(res)):
                    if i == 0 and i < len(res) - 1:
                        transcription[-1] += res[i]['text']+"\n"
                    if i == 0:
                        transcription[-1] += res[i]['text']
                    elif i < len(res) - 1:
                        transcription[-1] += "\t" + res[i]['text']+"\n"
                    else:
                        transcription[-1] += "\t" + res[i]['text']
                freshScreen(transcription)
                try:
                    tts(res[0]['text'], args.language,client)
                except:
                    pass
                # try:
                #     transcription.append("Rasa> " + res.json())
                #     # transcription.append("Rasa> " + res.json()[0]['text'])
                # except:
                #     transcription.append("Rasa> Hi!")
                # Clear audio data received during request
                while not data_queue.empty():
                    data = data_queue.get()
                transcription.append("Me> " + "...")
                # Clear the console to reprint the updated transcription.
                freshScreen(transcription)
                # Flush stdout.
                # print('', end='', flush=True)
                phrase_time = None


            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                transcription[-1] += ".."
                freshScreen(transcription)

                # Concatenate our current audio data with the latest audio data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Write wav data to the temporary file as bytes.
                audio_array,_ = sf.read(wav_data)
                audio_array = audio_array.astype(np.float32)

                # Read the transcription.
                result = audio_model.transcribe(audio_array, language=args.language, fp16=torch.cuda.is_available())
                text = result['text'].strip()
                
                # This is the time we finished transcribe audio data from the queue.
                phrase_time = datetime.utcnow()

                # edit the existing one.
                transcription[-1] = "Me> " + text + "..."

                # Clear the console to reprint the updated transcription.
                freshScreen(transcription)
                # Flush stdout.
                # print('', end='', flush=True)

                # Infinite loops are bad for processors, must sleep.
            sleep(0.2)
        except KeyboardInterrupt:
            break

def freshScreen(transcription):
    os.system('cls' if os.name=='nt' else 'clear')
    for line in transcription:
        print(line, flush=True)

def tts(text,language,client):
    if not language:
        language = "en"
    input_text = texttospeech.SynthesisInput(text=text)
    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    song = AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")
    play(song)


if __name__ == "__main__":
    main()