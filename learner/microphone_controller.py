import pickle
import select
from PyQt5 import QtCore
from network_notifications import *
from audio_threadder import *
import sys

class MicrophoneController():

    def __init__(self, connector):
        self.at1 = AudioThreadder(1)
        self.at2 = AudioThreadder(2)
        self.message1 = None
        self.message2 = None

    def start_record(self, participant_names, mic_data):
        try:
            num_participants = len(participant_names)
            p1_mic_id = mic_data[participant_names[0]]

            # start audio thread
            print("beginning to record")
            self.at1.begin_recording(p1_mic_id)
            if num_participants > 1:
                p2_mic_id = mic_data[participant_names[1]]
                self.at2.begin_recording(p2_mic_id)

            print("returning true")
            return True

        except (Exception):
            print("SERVER >> Microphones disconnected")
            mic_notification = MicrophonesDisconnected("The microphones were disconnected. Please ask the experimenter for help.")
            mic_notification.exec_()

            return False

    def end_record(self, num_participants):
        try:

            # attempting to send the end message
            print("attempting to send the end message")
            self.at1.end_recording()
            self.message1 = self.at1.data_string
            if num_participants > 1:
                self.at2.end_recording()
                self.message2 = self.at2.data_string
            else:
                self.message2 = ""

            return None
            #return message1, message2
        except:
            print("SERVER >> Microphones disconnected during recording")

            return None

    def get_return_vals(self):
        if self.message1 is not None and self.message2 is not None:
            message1 = self.message1
            message2 = self.message2
            return message1, message2
        else:
            return None

    def clear_messages(self):
        self.message1 = None
        self.message2 = None
