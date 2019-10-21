import sys
import pdb
import os
import threading
import time
import select
import traceback

sys.path.append('./modules/')
from mealy_machine import MealyMachine, State, Transition, InvalidInputException
import nao
from nao import NaoMotion, NaoSpeech, NaoEyes
from nao_listener import SpeechRecorder
from performance_manager import PerformanceManager

import google
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue

sys.path.append('../intent_parser/')
import intent_parser
from intent_parser import IntentRecognition, AudioInput


def clear_audio_file(soundfile):
    import os
    try:
        os.remove(soundfile)
        print("cleared audio file")
    except:
        print("error when clearing audio file")

class InteractionDriver:
    """
    Class which drives the actions of the nao based on a provided automata and
    user voice input
    """

    config_filepath = '../intent_parser/config/config_spacy.yml'

    def __init__(self, ip, port, interaction_id, automata_file_name, intent_file_name,
                    sound_file_name, base_silence, s):
        """
        :param ip: type string: string representation of the IP address nao is
        located at
        :param port: type int: int port to access nao on
        :param design: type string: name of design to follow. This may change
        the nao's behaviour
        :param automata_file_name: type string: string representation of
        the filepath to the automata .xml file.
        :param intent_file_name: type string: string representation of the
        filepath to the file or folder to be given to IntentRecognition()
        """
        #pdb.set_trace()
        self.IP = ip
        self.PORT = port
        self.soundfile = 'soundfile.wav'
        self.automata = MealyMachine.generate_from_xml(automata_file_name)
        self.soundfile = sound_file_name
        self.base_silence = base_silence
        self.s = s
        #pdb.set_trace()

        clear_audio_file(self.soundfile)
        self.intent_recognizer = IntentRecognition(intent_file_name,
            InteractionDriver.config_filepath)
        nao.init_broker(ip, port)
        self.eyes = NaoEyes('eyes{}'.format(interaction_id), ip, port)
        self.robot = PerformanceManager(ip, port, self.automata.design, interaction_id)
        self.robot.state_begin()
        self.robot.sittingPosition()

    def get_intents(self, transcript):
        """
        :param transcript: list of type string:
        """
        intents = []
        alternatives = []
        intent_data = self.intent_recognizer.parse_intent(transcript)
        intents.append(intent_data[0])
        alternatives.append(intent_data[2])
        return intents,alternatives

    def get_entities(self, transcript):
        """return: list of list of tuples"""
        entities = []
        print("Entities: {}".format(entities))
        entity_data = self.intent_recognizer.parse_entities(transcript)
        entities.append(entity_data)
        return entities


    def complete_interaction(self):
        """
        The primary method of this module. This method
        """
        """try:
            transition = self.automata.transition('Empty')
            self.robot.perform(transition.output,
                            self.automata.cur_output_text_list)
        except InvalidInputException as e:
            pass"""
        self.robot.begin_head_movements()
        try:
            while (self.automata.cur_state.num_transitions != 0):
                entities = []
                input = None
                self.eyes.hear()

                ready_to_read, ready_to_write, in_error = select.select([], [self.s], [])
                ready_to_write[0].sendall(b"listen")

                ready_to_read, ready_to_write, in_error = select.select([self.s], [], [], 3600)
                transcript = ready_to_read[0].recv(1024)
                transcript = transcript.decode("utf-8")
                print(transcript)

                '''
                print('ready to listen')
                self.soundfile = 'soundfile{}.wav'.format(time.time())

                input = None
                entities = []
                #pdb.set_trace()
                #self.eyes.hear()
                audio_thread_support = AudioThreadSupport()
                thread = threading.Thread(target=
                        audio_thread_support.record_speech, args=(
                        self.intent_recognizer, self.soundfile, self.base_silence, self.eyes))
                thread.start()
                self.eyes.hear()

                empty_transition = self.automata.cur_state.empty_transition
                if empty_transition is not None:
                    timeout_duration = empty_transition.timeout
                    print('waiting ' + str(timeout_duration) +
                        ' seconds to transition on empty')
                    for i in range(int(timeout_duration*1000)):
                        if audio_thread_support.is_recording():
                            print("audio thread is recording!")
                            break
                        #print("about to sleep for 0.3 seconds")
                        time.sleep(.001)
                    if not audio_thread_support.is_recording():
                        print('timed out')
                        audio_thread_support.timeout()
                '''

                if transcript != "#timeout#":
                    '''
                    print('not timed out')
                    transcripts = audio_thread_support.get_transcripts()
                    print("clearing audio file")
                    clear_audio_file(self.soundfile)
                    print("done clearing audio file")
                    print(transcripts)
                    '''

                    if len(transcript) == 0:
                        continue

                    if transcript.strip() == "exit":
                        self.eyes.end_hear()
                        break

                    try:
                        inputs, alternative_array = self.get_intents(transcript)
                        input = inputs[0]
                        alternatives = alternative_array[0]
                        print("~alternatives~")
                        print(alternatives)
                    except IndexError as e:
                        continue
                    entities = self.get_entities(transcript)
                    print("Entities: {}".format(entities))
                else:
                    input = 'Empty'
                    alternatives = []

                test_trans = self.automata.pre_transition(input)

                # find alternative to empty output
                if test_trans.output == "error":
                    transition = self.automata.transition(input)
                    for alt in alternatives:
                        alt_trans = self.automata.pre_transition(alt[0])
                        if alt_trans.output != "error":
                            print("went with an alternative transition with confidence {}".format(alt[1]))
                            transition = self.automata.transition(alt[0])
                            break
                else:
                    transition = self.automata.transition(input)

                print("driver current state: " + self.automata.cur_state.state_id)
                #print("driver current gesture: " + str(self.automata.cur_state._State__gesture.attrib['ref']))
                #gesture = str(self.automata.cur_state._State__gesture.attrib['ref'])
                print("driver current gesture: " + transition.gesture)
                gesture = transition.gesture

                if transition.output == 'error':
                    entities = []
                    for key in self.automata.cur_state.transitions:
                        #pdb.set_trace()
                        print(key)
                        entities.append(key)
                print("Entities: {}".format(entities))

                self.robot.begin_gesture(gesture)
                self.robot.perform(transition.output, entities, transition.speech)
                self.robot.end_gesture(gesture)

            self.robot.rest()
        except:
            try:
                traceback.print_exc()
            except:
                pass
            raise

        self.robot.end_head_movements()

        ready_to_read, ready_to_write, in_error = select.select([], [self.s], [])
        ready_to_write[0].sendall(b"endlisten")

        ready_to_read, ready_to_write, in_error = select.select([self.s], [], [], 3600)
        transcript = ready_to_read[0].recv(1024)
        #self.automata.reset()

if __name__ == "__main__":
    InteractionDriver("169.254.28.227", 9559, 'Information_Desk', 'interaction.xml',
        '../intent_parser/projects/default/help_desk/', 'soundfile.wav', 0)
