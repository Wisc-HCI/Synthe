""" This module gives tools to represent mealy machine automata and to
convert constructed automata to and from an XML format as specified in
/learner/automata_xml_format.xml

Honestly, it should probably be broken into a mealy machine module and a module
specific to this project's automata traversal specifics, but oh well. Maybe
I'll come back and do it later.
"""
import xml.etree.ElementTree as ET
import pdb
import sys
from threading import Lock
import thread
import time

class InvalidInputException(Exception):
    """ This exception is raised when State.get_transition() is used to attempt
    to access a transition with an invalid input (e.g. the state cannot
    transition on that input.)
    """

    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


class MealyMachine():
    """
    This class models a Mealy Machine automata
    """

    def __init__(self, name, design, num_states, init_state):
        """ name: type string
        design: type string
        -used to select specific QA files
        num_states: type int: number of states in the automata
        -static
        init_state: type int: The state the machines begins work on
        -static
        """
        self.__name = name
        self.__new__design = design
        self.__num_states = num_states
        self.__states = []
        for i in range(num_states):
            self.__states.append(State(i))
        self.__init_state = self.__states[init_state]
        self.__cur_state = self.__init_state

    @classmethod
    def generate_from_xml(cls, filename):
        """:param filename: XML file to generate the mealy machine from
        The format for this file is specified in automata_xml_format.xml,
        and convert_to_xml() produces files in this format"""
        #xml parser
        if len(sys.argv) < 5:
            tree = ET.parse(filename)
        else:
            tree = ET.parse(sys.argv[2])
            print sys.argv[2]
        root = tree.getroot()

        name = "unnamed"
        for value in root.iterfind('name'):
            name = value

        design = "delivery"
        for value in root.iterfind('design'):
            design = value.text

        #Generate States and Transitions
        num_states = 0
        init_state = 0
        states = []

        for elem in root.iterfind('state'):
            id = elem.attrib['id']
            #speech = []
            #speech_raw_data = elem.find('speech')
            #for value in speech_raw_data.iterfind('value'):
            #    speech.append(value.text)
            #gaze = elem.find('gaze')
            #gesture = elem.find('gesture')
            #states.append(State(id, speech, gaze, gesture))
            states.append(State(id))

            num_states = num_states + 1
            if elem.attrib['init'] == "true":
                init_state = int(elem.attrib['id'])

        self = cls(name, design, num_states, init_state)
        self.__states = states
        self.__init_state = states[init_state]
        self.__cur_state = states[init_state]

        """for elem in root.iterfind('state'):
            num_states += 1
            if elem.attrib['init'] == "true":
                init_state = int(elem.attrib['id'])
                #print("FOUND INIT")
        #print "Number of states:", num_states"""

        for elem in root.iterfind('transition'):
            timeout = None
            for timeout_data in elem.iterfind('timeout'):
                timeout = float(timeout_data.attrib['timeout'])
            speech = []
            speech_raw_data = elem.find('speech')
            for value in speech_raw_data.iterfind('value'):
                speech.append(value.text)
            gesture = elem.find('gesture').attrib['ref']
            self.add_transition(
                int(elem.find('source').attrib['ref']),
                int(elem.find('target').attrib['ref']),
                elem.find('input').attrib['ref'],
                elem.find('output').attrib['ref'],
                speech,
                gesture,
                timeout
            )
        #pdb.set_trace()
        self.list_graph()
        #pdb.set_trace()
        return self

    def convert_to_xml(self, filename):
        """
        does nothing. don't use this method.
        """
        pass

    def add_transition(self, source, target, input, output, speech, gesture, timeout=None):
        """
        :param source: type int: state which transition originates from
        :param target: type int: state which transition transitions to
        :param input: type string: input this transition should be followed on
        :param output: type string: output this transition produces
        :param timeout: type float: time, in seconds, an automata should wait
        in source before transitioning along this empty transition

        Creates a transition from source to target on input,
        returning output
        """
        #pdb.set_trace()
        new_transition = Transition(output, self.__states[target], speech, gesture, timeout)
        self.__states[source].add_transition(new_transition, input)

    def transition(self, input):
        """
        :param input: type string: cause the mealy machine to transition along
        the given input.
        Will return None if that state has no transitions.
        Otherwise, raises InvalidInputException if that input is not a
        valid transition for that state.
        """
        try:
            transition = self.__cur_state.get_transition(input)
            if transition is None:
                return None
            self.__cur_state = transition.target
            print('Transitioning on: ' + input)
            print('Current State: ' + str(self.__cur_state.state_id))
        except InvalidInputException as e:
            print('Cannot transition on that input from this state.')
            transition = Transition('error', self.__cur_state, "", "None")
        return transition

    def pre_transition(self,input):
        """
        :param input: type string: cause the mealy machine to transition along
        the given input.
        Will return None if that state has no transitions.
        Otherwise, raises InvalidInputException if that input is not a
        valid transition for that state.
        """
        try:
            transition = self.__cur_state.get_transition(input)
            if transition is None:
                return None
            print('Possible next State: ' + str(self.__cur_state.state_id))
        except InvalidInputException as e:
            print('Cannot transition on that input from this state.')
            transition = Transition('error', self.__cur_state, "", "None")
        return transition

    def reset(self):
        """sets the current state to the init state, resetting the machine"""
        self.__cur_state = self.__init_state

    def list_graph(self):
        """prints the self object to standard out"""
        for state in self.__states:
            print '### State: ' + str(state.state_id)
            print('Number of transitions: ' + str(state.num_transitions))
            for key, transition in state.transitions.iteritems():
                print ( 'key: (' + key +
                        ') | source: ' + str(state.state_id) +
                        ' | target: ' + str(transition.target.state_id) )
            print('______________________________\n')

    @property
    def states(self):
        return self.__states

    @property
    def design(self):
        return self.__new__design

    @property
    def cur_state(self):
        return self.__cur_state

    @property
    def init_state(self):
        return self.__init_state

    @property
    def cur_output_text_list(self):
        return self.__cur_state.speech

class Transition():
    def __init__(self, output, target, speech, gesture, timeout=None):
        """
        :param output: type string: behavior this transition outputs
        :param target: type int: the state this will transition to
        :param timeout: type float: The time in seconds to wait for an input
        before transitioning along this empty transition. Transitions which
        transition on empty inputs must have a timeout.
        """
        self.output = output
        self.target = target
        self.speech = speech
        self.gesture = gesture
        self.timeout = timeout

    @property
    def output(self):
        return self.output

    @property
    def target(self):
        return self.target

class State():
    def __init__(self, state_id):
        """
        :param state_id: type int: int id of this state
        :param speech: list of type string: possible speech outputs to output
        with text to speech.
        :param gaze: type string: gaze behaviour. Must be one of the types
        specified in automata_xml_format.xml or None
        :param gesture:  gesture behaviour. Must be one of the types
        specified in automata_xml_format.xml or None
        """
        self.__state_id = state_id
        self.__transitions = {}
        self.num_transitions = 0
        self.empty_transition = None

    def add_transition(self, transition, input):
        """adds a new transition to the self State object. This transition can
        be accessed later with get_transition().

        :param transition: transition object to be added
        :param input: input letter this transition should be taken on.
        """
        #pdb.set_trace()
        self.__transitions[input] = transition
        if input == 'Empty':
            self.empty_transition = transition
        self.num_transitions = self.num_transitions + 1

    def get_transition(self, input):
        """
        retrieves a previously added transition

        :param input: type string: the method will return the transition taken
        with input as an input
        :exception: InvalidInputException: if self has transitions, but input
        is not associated with any.
        """

        if self.num_transitions == 0:
            return None
        if input in self.__transitions:
            return self.__transitions[input]
        else:
            message = ('error: state ' + str(self.__state_id) +
                ' cannot transition ' + 'on an input of ' + input)
            raise InvalidInputException(message)

    def get_phrase(self):
        """get a random phrase from the list of possible speech outputs"""
        import random
        ndx = random.randint(0, length(self.__speech)-1)
        return self.__speech[ndx]

    @property
    def state_id(self):
        return self.__state_id

    @property
    def transitions(self):
        return self.__transitions

    @property
    def speech(self):
        return self.__speech

    @property
    def gaze(self):
        return self.__gaze

    @property
    def gesture(self):
        return self.__gesture
