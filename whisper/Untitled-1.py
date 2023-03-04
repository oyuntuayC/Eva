
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
    tts("Hi","en",client)

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