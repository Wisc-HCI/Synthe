from watson_developer_cloud import SpeechToTextV1

from os.path import join, dirname, isfile
from pathlib import Path

import pickle
import json
import traceback
import Queue as queue
import threading
import thread
import time

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
    return transcripts

def post_process(text):
    word_list = text.split()
    return ' '.join([i for i in word_list if i != "%%HESITATION"])


def recognize_speech(audio_file):
    """ audio_file: type string: string filepath to a valid audio file
    Should be of filetype .wav
    Return type: list of tuple ([string audio_transcript],
                                [float start_time (in seconds)],
                                [float end_time (in seconds)],
                                [float confidence])
    list length == (# of unique speech instances in audio_file)
    """

    speech_recognition_results = call_watson_tts(audio_file)
    transcripts = []
    try:
        for alternative in speech_recognition_results["results"]:
            result = alternative["alternatives"][0]

            audio_transcript = post_process(result['transcript'])
            start_time = float(result["timestamps"][0][1])
            end_time = float(result["timestamps"][-1][2])
            confidence = float(result['confidence'])
            transcripts.append((audio_transcript, start_time,
                                end_time, confidence))

    #TODO: Delete this except block when done debugging
    except TypeError as e:
        print("debug error handling")
        print("Output from Watson API: " + speech_recognition_results)
        print(speech_recognition_results["results"])
        print(speech_recognition_results["results"][0])
    except:
        print("ERROR: something bad happened during speech recognition")
        print("       returning a blank transcript")
        return []

    return transcripts


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
    with open(file, 'rb') as audio_file:
        print('Requesting new voice recognition object')
        speech_recognition_results = speech_to_text.recognize(
            audio = audio_file,
            content_type='audio/wav',
            timestamps=True,
            word_alternatives_threshold=0.9,
            keywords=['colorado', 'tornado', 'tornadoes'],
            keywords_threshold=0.5,
            smart_formatting = True)

    print('### speech recognition completed ###')
    #print(json.dumps(speech_recognition_results, indent=2))
    return speech_recognition_results


class AudioInput:
    """AudioInput allows calling programs to record audio and terminate
    recording at will.
    """
    exit_flag = 1

    def __init__(self, soundfile):
        """ Pre: Running computer has access to working audio input
        Post: Recorded audio has been saved to my_soundfile
        Return: type string: filepath to recorded audio file
        Once called, will begin recording audio to the filepath specified by
        soundfile. Call terminate_recording() to end the recording
        """
        self.soundfile = soundfile
        _thread.start_new_thread(self.audio_input_thread, (soundfile,))

    def audio_input_thread(self, my_soundfile):
        print("starting the audio input thread")
        import sys
        q = queue.Queue()
        import sounddevice as sd
        import soundfile as sf
        try:
            self.exit_flag = 0
            def callback(indata, frames, time, status):
              """This is called (from a separate thread) for each audio block."""
              if status:
                  #print(status, file=sys.stderr)
                  pass
              q.put(indata.copy())
            # Make sure the file is opened before recording anything:
            with sf.SoundFile(my_soundfile, mode='x', samplerate=44100,
                            channels=2) as file:
                print sd.query_devices()
                print("attempted to query devices")
                # device should be 1 for ubuntu, channel 2
                with sd.InputStream(device=2, channels=2, callback=callback):

                    while self.exit_flag != 1:
                        file.write(q.get())

                while not q.empty():
                    file.write(q.get())
        except Exception as e:
            print(e)
            """try:
                os.remove(my_soundfile)
            except Exception as e:
                None"""
        self.exit_flag = 0

    def terminate_recording(self):
        """Post: recording to self.soundfile has been terminated."""
        if self.exit_flag == 1:
            return

        self.exit_flag = 1
        while self.exit_flag == 1:
            time.sleep(.1)
        self.exit_flag = 1

    def get_soundfile(self):
        """return: type string: self.soundfile"""
        return self.soundfile

    """def clear_audio_file():
        try:
            os.remove(self.soundfile)
        except:
            pass"""



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
        #if "intent_ranking" in self.interpreter.parse(intent_text):
        alternatives = self.parse_alternative_intents(self.interpreter.parse(intent_text)["intent_ranking"])
        #else:
        #    alternatives = []
        return (intent, confidence, alternatives)

    def parse_alternative_intents(self,parse_output):
        alternatives = []
        raw_alternative_data = parse_output
        for item in raw_alternative_data:
            if float(item["confidence"]) > 0:
                tup = (item["name"],float(item["confidence"]))
                idx = 0
                for alt in alternatives:
                    if alt[1] > tup[1]:
                        idx += 1
                    else:
                        break
                alternatives.insert(idx,tup)
        return alternatives

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
        print(text)
        print(self.interpreter.parse(text))
        print("*************")
        print(self.interpreter.parse(text)['entities'])
        print("*************")
        for entity_entry in self.interpreter.parse(text)['entities']:
            print(entity_entry)
            entity = entity_entry['entity']
            value = entity_entry['value']
            print("here is the entity: {}".format(entity))
            print("here is the value: {}".format(value))
            entities.append((entity, value))
        return entities
