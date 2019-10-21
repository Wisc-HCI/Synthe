from watson_developer_cloud import SpeechToTextV1

import os
from os.path import join, dirname, isfile
from pathlib import Path

import pickle
import json
import traceback
import queue
import threading
import _thread
import time
import sys

from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer, Metadata, Interpreter
from rasa_nlu import config

def pickle_recognize_speech(audio_file, pickle_file_count):
    """return: list of strings representing speech in the audio, delimited
        by substantial silence

        Don't use this method. It really isn't worth it."""
    pickle_file_name = (
        pickle_file_base_name + '_' + str(pickle_file_count) + '.p')
    try:
        #Attempt to load a stored json object from pickle_file_name.
        #open(pickle_file_name) will throw to the except
        #block if the file does not exist
        speech_recognition_results = pickle.load(
            open(pickle_file_name, 'rb'))
        print('Loaded previous instance of speech recognition from: '
            + pickle_file_name)
        print(json.dumps(speech_recognition_results, indent=2))
        transcripts = []
        for result in speech_recognition_results["results"]:
            transcripts.append(result["alternatives"][0]['transcript'])
        pickle_file_count = pickle_file_count + 1
    except (IOError, EOFError) as e:
        print('no pickle file found')
        #debug=True disables access to IBM Cloud to conserve access resources
        if not debug:
            speech_recognition_results = call_watson_tts(audio_file)
            #the speech_recognition_results item is an amalgam
            #of dicts and lists, but this should access the final
            #transcript decided on by text-to-speech.
            transcripts = []
            try:
                for result in speech_recognition_results["results"]:
                    transcripts.append(result["alternatives"][0]['transcript'])
            except TypeError as e:
                print("debug error handling")
                print("Output from Watson API: " + speech_recognition_results)
                print(speech_recognition_results["results"])
                print(speech_recognition_results["results"][0])
    return transcripts


def recognize_speech(audio_file):
    """ audio_file: type string: string filepath to a valid audio file
    Should be of filetype .wav
    Return type: list of tuple ([string audio_transcript],
                                [float start_time (in seconds)],
                                [float end_time (in seconds)],
                                [float confidence])
    list length == (# of unique speech instances in audio_file)
    """

    # for debugging purposes, if we want to load a preexisting transcript
    if len(sys.argv) > 5 and sys.argv[5] == "load_transcripts":
        with open("transcripts.json", "r") as infile:
            speech_recognition_results = json.load(infile)
    else:
        print("about to call watson tts")
        speech_recognition_results = call_watson_tts(audio_file)

    # we can also save our transcript
    if len(sys.argv) > 5 and sys.argv[5] == "save_transcripts":
        with open("transcripts.json", "w") as outfile:
            outfile.write(json.dumps(speech_recognition_results))

    transcripts = []
    try:
        curr_speaker = -1
        prev_speaker = -1
        curr_transcript = ""
        transcript_start = -1.0
        transcript_end = -1.0

        curr_idx = 0

        # if speaker_labels are not in the results, then we don't have any data
        if "speaker_labels" in speech_recognition_results:
            speaker_labels = speech_recognition_results["speaker_labels"]

        # parse as much data as exists
        for alternative in speech_recognition_results["results"]:
            for word_data in alternative["alternatives"]:
                for timestamp in word_data["timestamps"]:

                    curr_speaker = int(speaker_labels[curr_idx]['speaker'])
                    if prev_speaker == -1:
                        prev_speaker = curr_speaker
                        transcript_start = timestamp[1]

                    if curr_speaker == prev_speaker:
                        curr_transcript += "{} ".format(timestamp[0])
                        transcript_end = timestamp[2]

                    else:
                        print("{} -- {} to {} with speaker {}".format(curr_transcript, transcript_start, transcript_end, prev_speaker))
                        transcripts.append((post_process(curr_transcript), transcript_start, transcript_end, prev_speaker))
                        curr_transcript = "{} ".format(timestamp[0])
                        transcript_start = timestamp[1]
                        transcript_end = timestamp[2]
                        prev_speaker = curr_speaker

                    curr_idx += 1
            print("{} -- {} to {} with speaker {}".format(curr_transcript, transcript_start, transcript_end, prev_speaker))
            transcripts.append((post_process(curr_transcript), transcript_start, transcript_end, prev_speaker))
            curr_transcript = ""
            transcript_start = -1
            transcript_end = -1
            prev_speaker = -1

        '''
        for alternative in speech_recognition_results["results"]:
            result = alternative["alternatives"][0]

            audio_transcript = result['transcript']
            start_time = float(result["timestamps"][0][1])
            end_time = float(result["timestamps"][-1][2])
            confidence = float(result['confidence'])
            transcripts.append((audio_transcript, start_time,
                                end_time, confidence))
        '''

    #TODO: Delete this except block when done debugging
    except TypeError as e:
        print("debug error handling")
        print(speech_recognition_results["results"])
        print(speech_recognition_results["results"][0])
    except:
        print("ERROR: something bad happened during speech recognition")
        print("       returning a blank transcript")
        return []

    return transcripts

def post_process(text):
    word_list = text.split()
    return ' '.join([i for i in word_list if i != "%%HESITATION"])

def call_watson_tts(file):
    """return: json format of speech recognition as specified by the
    IBM Watson speech-to-text documentation
    """
    speech_to_text = SpeechToTextV1(
        username = 'cc4c341b-cd9f-4191-bc2a-091d7bd559ff',
        password = 'ceEVwJXL2gHl'
    )

    #print(join(dirname(__file__), './.', file))
    #with open(join(dirname(__file__), './.', file), 'rb') as audio_file:
    print(file)

    # wait until file exists
    while not os.path.exists(file):
        print("file does not yet exist")
        time.sleep(1)

    with open(file, 'rb') as audio_file:
        print('Requesting new voice recognition object')
        speech_recognition_results = speech_to_text.recognize(
            audio = audio_file,
            content_type='audio/wav',
            timestamps=True,
            word_alternatives_threshold=0.9,
            keywords=['colorado', 'tornado', 'tornadoes'],
            keywords_threshold=0.5,
            smart_formatting = True,
            speaker_labels=True)

    print('### speech recognition completed ###')
    #print(json.dumps(speech_recognition_results, indent=2))
    return speech_recognition_results


class AudioInput:
    """AudioInput allows calling programs to record audio and terminate
    recording at will.
    """
    exit_flag = 1

    def __init__(self, soundfile, mic_id):
        """ Pre: Running computer has access to working audio input
        Post: Recorded audio has been saved to my_soundfile
        Return: type string: filepath to recorded audio file
        Once called, will begin recording audio to the filepath specified by
        soundfile. Call terminate_recording() to end the recording
        """
        self.soundfile = soundfile
        _thread.start_new_thread(self.audio_input_thread, (soundfile,mic_id,))

    def audio_input_thread(self, my_soundfile, mic_id):
        import pyaudio
        import wave

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = mic_id["max_input_channels"]
        RATE = 44100
        WAVE_OUTPUT_FILENAME = my_soundfile

        p = pyaudio.PyAudio()

        stream = p.open(input_device_index=mic_id["id"],
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("AUDIOINPUT >> recording")

        frames = []
        self.exit_flag = 0
        while self.exit_flag != 1:
            data = stream.read(CHUNK,exception_on_overflow=False)
            frames.append(data)

        print("AUDIOINPUT >> done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        self.exit_flag = 0
        '''
        total_data_len = 0
        import sys
        q = queue.Queue()
        import sounddevice as sd
        import soundfile as sf
        try:
            self.exit_flag = 0
            def callback(indata, frames, time, status):
              """This is called (from a separate thread) for each audio block."""
              if status:
                  print(status, file=sys.stderr)
                  pass
              print(len(indata))
              q.put(indata.copy())
            # Make sure the file is opened before recording anything:
            with sf.SoundFile(my_soundfile, mode='x', samplerate=44100,
                            channels=2) as file:

                # device should be 3 for ubuntu, channels 2
                print("available devices")
                print(sd.query_devices())
                with sd.InputStream(channels=2, callback=callback):
                    print("starting record loop")
                    while self.exit_flag != 1:
                        print("yeee")
                        data = q.get()
                        print("obtained q data")
                        total_data_len += len(data)
                        file.write(data)
                        print("written ye")
                    print("broke from record loop")

                while not q.empty():
                    file.write(q.get())
        except Exception as e:
            print(e)
            try:
                os.remove(my_soundfile)
            except Exception as e:
                None
        self.exit_flag = 0
        print("TOTAL DATA LEN: {} at 44100 sr".format(total_data_len))
        '''

    def terminate_recording(self):
        """Post: recording to self.soundfile has been terminated."""
        if self.exit_flag == 1:
            return

        self.exit_flag = 1
        while self.exit_flag == 1:
            print("self.exit_flag: {}".format(self.exit_flag))
            time.sleep(1)
        self.exit_flag = 1

    def get_soundfile(self):
        """return: type string: self.soundfile"""
        return self.soundfile

    def clear_audio_file():
        try:
            os.remove(self.soundfile)
        except:
            pass



class IntentRecognition:
    """IntentRecognition provides a simplified interface for the rasaNLP
    intent recognition utility.
    """

    def __init__(self, filepath, config_file=None):
        """
        :param filepath: string filepath to either .json training data or an
        existing interpreter directory, both as specified by rasaNLU.
        :param config_file: string filepath to a spacy config file. In the
        source project, this file is always located in
        intent_parser/config/config_spacy.yml. This variable is only required
        if filepath points to .json training data

        post: an IntentRecognition object has been created and an intent
        interpreter has been constructed for it. If filepath points to a file,
        a new interpreter file system has been generated in /projects/default/
        with the data contained in filepath
        Else, the directory filepath is used for interpreter.
        """
        self.interpreter = None
        if isfile(filepath):
            print('Getting new interpreter data')
            model_directory = self.train_model(filepath, config_file)
            self.interpreter = Interpreter.load(model_directory)
        else:
            print('Using old interpreter data')
            self.interpreter = Interpreter.load(filepath)

    def train_model(self, data_file, config_file=None):
        """
        :param data_file: string filepath to training data file. The format of
        this file must conform to rasaNLU specifications
        :param config_file: string filepath to the spacy config file.
        Post: A new model directory was created in ./projects/default/
        Return: The new model directory's filepath
        """
        print('Training new model. This will take a minute')
        training_data = load_data(data_file)
        trainer = Trainer(config.load(config_file))
        trainer.train(training_data)
        model_directory = trainer.persist('./projects')
        return model_directory

    def parse_intent(self, intent_text):
        """
        :param intent_text: type string: text to recognize intent from
        :return: type tuple: (string intent, float confidence)
        """
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parse_output = self.interpreter.parse(intent_text)["intent"]
        intent = parse_output["name"]
        confidence = float(parse_output["confidence"])
        return (intent, confidence)

    def parse_entities(self, text):
        """
        :param text: type string: text to parse entities from
        :return: list of type tuple: (entity, value)
        """
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parse_output = self.interpreter.parse(text)["intent"]
        entities = []
        for entity_entry in self.interpreter.parse(text)['entities']:
            entity = entity_entry['entity']
            value = entity_entry['value']
            entities.append((entity, value))
        return entities
