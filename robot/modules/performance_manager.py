import time
import sys
import numpy as np
import random
import pdb
from database import Database, InvalidItemException

sys.path.append("pynaoqi-python2.7-2.1.4.13-mac64")
from nao import NaoMotion, NaoSpeech

#TODO: Fill out behaviors

class PerformanceManager:
    """
    Host class to the perform method.
    """

    def __init__(self, ip, port, design, interaction_id):
        """
        :pre: './databases/' + design + '.json' is a filepath to a valid .json
        file

        :param ip: type string: string representation of the IP address nao is
        located at
        :param port: type int: int port to access nao on
        :param design: type string: name of design to follow. This may change
        the nao's behaviour
        """

        self.motion = NaoMotion('motion{}'.format(interaction_id), design, ip, port)
        self.speech = NaoSpeech('speech{}'.format(interaction_id), ip, port)
        self.design = design
        self.database = Database(design)
        self.recent_entity = None

        self.perform_switch =    {
            'Help Desk':{
                'Empty':self.empty,
                'error':self.error,
                'database_failure':self.item_does_not_exist,

                'greeting':self.greet,
                'help_query':self.help_query,
                'farewell':self.farewell,
                'affirm_deny':self.affirm_deny,
                'gratitude':self.gratitude,
                'please_wait':self.please_wait,
                'request_help':self.request_help,
                'you_are_welcome':self.you_are_welcome,
                'confused':self.confused,
                'displeasure':self.displeasure,
                'repair_request':self.repair_request,
                'instruction':self.info_desk_instruction,

                'welcome':self.welcome,
                'location_statement':self.location_statement,
                'location_query':self.location_query,
                'location_unknown':self.location_unknown,
                'instruction':self.info_desk_instruction,
                'price_query':self.price_query,
                'price_statement':self.price_statement
            },

            'Delivery':{
                'Empty':self.empty,
                'error':self.error,
                #TODO: What should a database error for a delivery look like?
                'database_failure':self.error,

                'greeting':self.greet,
                'state_purpose':self.state_purpose,
                'farewell':self.farewell,
                'affirm_deny':self.affirm_deny,
                'gratitude':self.gratitude,
                'please_wait':self.please_wait,
                'request_help':self.request_help,
                'you_are_welcome':self.you_are_welcome,
                'confused':self.confused,
                'displeasure':self.displeasure,
                'repair_request':self.repair_request,
                'question':self.question,
                'answer':self.answer,
                'sign_request':self.sign_request,

                'ID_query':self.id_query,
                'confirm_ID':self.confirm_id,
                'deny_ID':self.deny_id,
                'handoff':self.handoff,
                'handoff_request':self.handoff_request,
            }
        }

        self.gesture_switch = {
            'Point':self.motion.pointed,
            'Present':self.motion.presented,
            'Wave':self.motion.waved,
            'Beat':self.motion.beatGestured
        }

    def state_begin(self):
        self.speech.speak("Preparing interaction.")

    def begin_head_movements(self):
        self.motion.intimacyModulating()

    def end_head_movements(self):
        self.motion.endIntimacyMod()

    def begin_gesture(self, gesture):
        if gesture != "None" and gesture != "0":
            self.gesture_switch[gesture]()

    def perform(self, output_action, entities, speech):
        """
        Disambiguating method to call different behavior methods.

        :param output_action: string action that should be taken. The appropriate values for
        this parameter are listed in the dict below
        :param speech_output_list: list of type string: list of phrases nao could use
        as speech output.
        """

        print('output action: ' + output_action)
        print("entities: {}".format(entities))
        print("SPEECH: {}".format(speech))


        if len(entities) > 0 and len(entities[0]) > 0 and not output_action == 'error':
            print("going into the entity info...")
            entity, entry = self.get_entity_info(entities)
            if entry is not None:
                self.recent_entity = entities[0][0][1]

        try:
            self.perform_switch[self.design][output_action](entities, speech)
        except InvalidItemException:
            self.perform_switch[self.design]['database_failure'](entities, speech)

    def end_gesture(self, gesture):
        self.motion.endGesture()
        print("waiting for gesture to end")
        while self.motion.end_gesture and gesture != "None" and gesture != "0":
            pass
        print("gesture ended")
        if gesture != "None" and gesture != "0" and gesture != "Left point":
            self.motion.rightarmRetracted()
        elif gesture != "None" and gesture != "0":
            self.motion.leftarmRetracted()

    def rest(self):
        self.motion.prepare_experiment()

    def select_from_output_list(self, output_list):
        """DEPRECATED: Returns a psudeorandom entry in output_list"""
        import random
        ndx = random.randint( 0, (len(output_list)-1) )
        return output_list[ndx]

    def get_entity_info(self, entities, recent_entity=None):
        print("inside entity info. Entities = {}".format(entities))
        if entities is not None:
            entity = entities[0][0][1]
        else:
            entity = recent_entity
        print("here is the entity: {}".format(entity))
        entry = self.database.get_data(entity)
        return entity, entry

    """
    :param entities: list of type string: entities with which to dynamically
        form outputs.
    Behavior methods group.
    Change these methods to establish how nao
    performs a certain behavior
    """

    def greet(self, entities, speech):
        output_text = 'Hi there'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def state_purpose(self, entities, speech):
        output_text = 'I am here to deliver a package.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def help_query(self, entities, speech):
        output_text = 'How can I help you?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def price_query(self, entities, speech):
        output_text = 'What are the price of socks?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def price_statement(self, entities, speech):
        print("Entities: {}".format(entities))
        if len(entities) > 0 and len(entities[0]) > 0:
            entity, entry = self.get_entity_info(entities)
            if entry is not None:
                price = entry[u"price"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_ps_with_entities(price, entity, speech)
                #output_text = 'The price of {} is {}.'.format(entity, price)
            else:
                output_text = self.find_blank_speech("PRICE", speech, "I'm sorry, I didn't understand the item you said.")
        elif self.recent_entity is not None:
            entity, entry = self.get_entity_info(None, recent_entity=self.recent_entity)
            if entry is not None:
                price = entry[u"price"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_ps_with_entities(price, entity, speech)
                #output_text = 'The price of {} is {}.'.format(entity, price)
            else:
                output_text = self.find_blank_speech("PRICE", speech, "I'm sorry, I didn't understand the item you said.")
        else:
            output_text = "What would you like the price for?"

        self.speech.speak(output_text)

    def find_blank_speech(self, ent, speech, backup):
        chosen_speech = backup
        candidate_speech = []
        for spk in speech:
            if ent not in spk:
                candidate_speech.append(spk)
        if len(candidate_speech) > 0:
            chosen_speech = random.choice(candidate_speech)
        return chosen_speech

    def combine_ps_with_entities(self, price, entity, speech):
        backup_speech = "The price of TARGET is PRICE."
        candidate_speech = []
        for spk in speech:
            if  "PRICE" in spk:
                candidate_speech.append(spk)
        if len(candidate_speech) > 0:
            chosen_speech = random.choice(candidate_speech)
        else:
            chosen_speech = backup_speech

        chosen_speech.replace("PRICE", price)
        if "TARGET" in chosen_speech:
            chosen_speech.replace("TARGET", entity)

        return chosen_speech

    def farewell(self, entities, speech):
        output_text = 'goodbye'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def affirm_deny(self, entities, speech):
        output_text = 'yes'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def gratitude(self, entities, speech):
        output_text = 'thank you'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def please_wait(self, entities, speech):
        output_text = 'can you wait for one moment please'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def request_help(self, entities, speech):
        output_text = 'Can you help me?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def confused(self, entities, speech):
        output_text = 'I am confused.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def repair_request(self, entities, speech):
        output_text = 'repair request placeholder'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def displeasure(self, entities, speech):
        output_text = 'This is taking too long.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def welcome(self, entities, speech):
        if self.design=="Information_Desk":
            output_text = 'Welcome to the store!'
            if len(speech) > 0:
                output_text = random.choice(speech)
            self.speech.speak(output_text)

    def location_statement(self, entities, speech):
        print("Entities: {}".format(entities))
        if len(entities) > 0 and len(entities[0]) > 0:
            print("found an entity in the location statement")
            entity, entry = self.get_entity_info(entities)
            if entry is not None:
                location = entry[u"location"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_ls_with_entities(location, entity, speech)
                self.recent_entity = entities[0][0][1]
            else:
                output_text = self.find_blank_speech(entity, speech, "I'm sorry, I didn't catch what you are looking for.")
        elif self.recent_entity is not None:
            print("resorting to previous entity in location statement")
            entity, entry = self.get_entity_info(None, recent_entity=self.recent_entity)
            print("obtained previous entry")
            if entry is not None:
                location = entry[u"location"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_ls_with_entities(location, entity, speech)
            else:
                output_text = self.find_blank_speech(entity, speech, "I'm sorry, I didn't catch what you are looking for.")
        else:
            output_text = "What are you looking for?"

        self.speech.speak(output_text)

    def combine_ls_with_entities(self, location, entity, speech):
        backup_speech = "The TARGET is in LOCATION."
        candidate_speech = []
        for spk in speech:
            if  "LOCATION" in spk:
                candidate_speech.append(spk)
        if len(candidate_speech) > 0:
            chosen_speech = random.choice(candidate_speech)
        else:
            chosen_speech = backup_speech

        chosen_speech.replace("LOCATION", location)
        if "TARGET" in chosen_speech:
            chosen_speech.replace("TARGET", entity)

        return chosen_speech

    def item_does_not_exist(self, entities, speech):
        print("Item does not exist")

    def location_query(self, entities, speech):
        print(entities)
        #if entities is not None:
        #    self.recent_entity = entities[0]
        output_text = 'Could you tell me where the socks are?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    #TODO: fill with entity
    def location_unknown(self, entities, speech):
        print("Entities: {}".format(entities))
        if len(entities) > 0 and len(entities[0]) > 0:
            entity, entry = self.get_entity_info(entities)
            if entry is not None:
                location = entry[u"location"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_lu_with_entities(entity, speech)
            else:
                output_text = self.find_blank_speech("TARGET", speech, "I'm sorry, I didn't catch what you are looking for.")
        elif self.recent_entity is not None:
            entity, entry = self.get_entity_info(None, recent_entity=self.recent_entity)
            if entry is not None:
                location = entry[u"location"]
                plurality = entry[u"plur_sing"]
                output_text = self.combine_lu_with_entities(entity, speech)
            else:
                output_text = self.find_blank_speech("TARGET", speech, "I'm sorry, I didn't catch what you are looking for.")
        else:
            output_text = "What are you looking for?"

        self.speech.speak(output_text)

    def combine_lu_with_entities(self, entity, speech):
        chosen_speech = random.choice(speech)

        if "TARGET" in chosen_speech:
            chosen_speech.replace("TARGET", entity)

        return chosen_speech


    #TODO: fill with entity
    def info_desk_instruction(self, entities, speech):
        output_text = 'To find the go all the way down to the end of the store, turn right, and head through the fourth aisle on your left.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def handoff_request(self, entities, speech):
        output_text = 'Can I hand you your package?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def handoff(self, entities, speech):
        output_text = 'Here you go!'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def id_query(self, entities, speech):
        output_text = 'Are you Alex?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def confirm_id(self, entities, speech):
        output_text = 'Yes, I am a delivery robot here to deliver your package.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def deny_id(self, entities, speech):
        output_text = 'That is not me.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    #TODO: add a list of questions that the robot can understand
    def question(self, entities, speech):
        output_text = 'Who is the package from, and what is in it?'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    #TODO: add a list of answers that the robot can understand (may require splitting up into different chatito file)

    def answer(self, entities, speech):
        output_text = 'To answer your question, the package is from your friend David, and contains plates.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def sign_request(self, entities, speech):
        output_text = 'Please sign for the package and let me know when you are done.'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def you_are_welcome(self, entities, speech):
        output_text = 'you are welcome'
        if len(speech) > 0:
            output_text = random.choice(speech)
        self.speech.speak(output_text)

    def empty(self, entities, speech):
        """This is how the nao should behave on an empty transition"""
        pass

    def error(self, valid_inputs, speech=None):
        """
        :param valid_inputs: list of type string: list of inputs that the
            current state can successfully transition on.
        This state will be entered if the participant
        supplies the incorrect input.
        """
        output_text = ("I'm sorry, I didn't understand. I can understand ")
        for input in valid_inputs:
            output_text = output_text + input + ", "
        self.speech.speak(output_text)

    def shut_down(self):
        """Should be called at the end of the performance."""
        self.motion.final_pose()

    def sittingPosition(self):
        self.motion.sittingPosition()
