import xml.etree.cElementTree as ET

import sys
sys.path.append('../intent_parser/')
from intent_parser import IntentRecognition

class Exporter():

	def __init__(self):
		self.ir = IntentRecognition('../intent_parser/projects/default/help desk', '../intent_parser/config/config_spacy.yml')

	def indent(self, elem, level=0):
		'''
		https://norwied.wordpress.com/2013/08/27/307/
		'''

		i = "\n" + level*"  "
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = i + "  "
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				self.indent(elem, level+1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i

	def export_to_xml(self, interaction, bodystorm):

		print("EXPORTER >> exporting to XML")

		transition_relation = interaction.results

		root = ET.Element("mma")

		# will change later so that it isn't hardcoded
		name = ET.SubElement(root, "name").text = "Interaction"
		design = ET.SubElement(root, "design").text = bodystorm.design

		# create a state-transition mapping (id -> transition object)
		curr_state = -1
		state2transitions = {}
		for st in range(0,interaction.n+1):
			state2transitions[st] = []
		print(state2transitions)

		curr_transition_id = 0
		for transition in transition_relation:
			if int(str(transition[2])) > -1:
				new_transition = Transition()
				new_transition.id = curr_transition_id
				new_transition.source_state_id = int(str(transition[0]))
				new_transition.target_state_id = int(str(transition[2]))
				new_transition.input_letter = transition[1]
				new_transition.output_letter = bodystorm.OMEGA_map_rev[int(str(transition[3]))]

				# get the gesture
				tr_tup = (int(str(transition[0])), str(transition[1]), int(str(transition[2])), int(str(transition[3])))
				if tr_tup in interaction.gesture_map:
					new_transition.gesture = bodystorm.GESTURE_map_rev[int(str(interaction.gesture_map[tr_tup]))]
				else:
					new_transition.gesture = "None"

				# get the speech
				speeches = interaction.speech_map[int(str(transition[0]))][str(transition[1])]
				for speech in speeches:
					new_transition.speech.append(self.convert_speech(speech,bodystorm.OMEGA_map_rev[int(str(transition[3]))]))
				state2transitions[int(str(transition[0]))].append(new_transition)

				curr_transition_id += 1

		# iterate through the states
		for st in state2transitions:
			state = ET.SubElement(root, "state", {'id':str(st),
												  'init':("True" if st == 0 else "False")})

			for tr in state2transitions[st]:
				transition = ET.SubElement(state, "transition", {'id':str(tr.id)})

		# iterate through the transitions
		for st in state2transitions:
			for tr in state2transitions[st]:
				transition = ET.SubElement(root, "transition", {'id':str(tr.id)})
				source = ET.SubElement(transition, "source", {'ref':str(tr.source_state_id)})
				target = ET.SubElement(transition, "target", {'ref':str(tr.target_state_id)})
				inp = ET.SubElement(transition, "input", {'ref':tr.input_letter})
				output = ET.SubElement(transition, "output", {'ref':tr.output_letter})
				gesture = ET.SubElement(transition, "gesture", {'ref':tr.gesture})
				speech = ET.SubElement(transition, "speech")
				for spk in tr.speech:
					value = ET.SubElement(speech, "value").text = spk
				timeout = ET.SubElement(transition, "timeout", {'timeout':"3"})

		# add indentations (https://norwied.wordpress.com/2013/08/27/307/)
		self.indent(root)

		tree = ET.ElementTree(root)
		tree.write("../robot/interactions/test_interaction.xml", encoding='utf-8', xml_declaration=True)

	def convert_speech(self, speech, omega):

		# remove apostrophes from speech
		speech.replace("'", "")

		# supply entities list
		possible_entities = ["socks",
							"shoes",
							"clothes",
							"plates",
							"silverware",
							"food",
							"snacks",
							"chocolate",
							"books",
							"paper",
							"deodorant",
							"pants",
							"produce",
							"magazines",
							"candy",
							"chips",
							"mens clothing",
							"womens clothing",
							"boys clothing",
							"girls cothing",
							"toothpaste",
							"makeup",
							"bicycles",
							"toys",
							"cameras",
							"phones",
							"tablets",
							"routers",
							"charger cords"]

		# handle the hesitation
		speech_split = speech.split(' ')
		for i in range(len(speech_split)):
			if speech_split[i] == "%HESITATION":
				speech_split[i] == "um,"
		new_speech = ""
		for item in speech_split:
			new_speech += item
			new_speech += " "
		speech = new_speech

		if omega == "location_statement" or omega == "location_unknown" or omega == "price_statement":

			# add the entities to the parsed_output
			entities = self.ir.parse_entities(speech)
			print("ENTITIES for {}".format(omega))
			print(entities)
			if len(entities) > 0:
				for ent in entities:
					ent_id = ent[0]
					ent_val = ent[1]
					start_idx = speech.find(ent_val)
					end_idx = start_idx + len(ent_val)
					begin = speech[0:start_idx]
					end = speech[end_idx+1:]
					speech = "{}{} {}".format(begin,ent_id.upper(),end)

			# in the event that certain entities were not captured, brute force add them
			for ent in possible_entities:
				if ent in speech:
					start_idx = speech.find(ent)
					end_idx = start_idx + len(ent)
					begin = speech[0:start_idx]
					end = speech[end_idx+1:]
					speech = "{}{} {}".format(begin,"TARGET",end)

		# also handle possibility of a price statement
		if omega == "price_statement":
			numerals = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "dollar", "dollars"]
			speech_split = speech.split(' ')
			seen_price = False
			for i in range(len(speech_split)):

				# try to convert chars to numbers
				is_number = False
				for char in speech_split[i]:
					try:
						float(char)
						is_number = True
					except ValueError:
						pass
				if is_number:
					if seen_price:
						speech_split[i] = ""
					else:
						speech_split[i] = "PRICE"
					seen_price = True

				# handle speech split
				elif speech_split[i] in numerals:
					if seen_price:
						speech_split[i] = ""
					else:
						speech_split[i] = "PRICE"
					seen_price = True
				else:
					seen_price = False

			new_speech = ""
			for item in speech_split:
				new_speech += item
				new_speech += " "
			speech = new_speech

		return speech
		'''
		# get the intent_parser object
		ir = IntentRecognition('./projects/default/help_desk', './config/config_spacy.yml')

		# add the entities to the parsed_output
		final_final_output = []
		for output in final_output:
			transcript = output[5]
			entities = ir.parse_entities(transcript)
			one = output[0]
			two = output[1]
			three = output[2]
			four = output[3]
			five = output[4]
			six = output[5]
			if len(entities) > 0:
				for ent in entities:
					ent_id = ent[0]
					ent_val = ent[1]
					start_idx = six.find(ent_val)
					end_idx = start_idx + len(ent_val)
					begin = six[0:start_idx]
					end = six[end_idx+1:]
					six = "{}{}{}".format(begin,ent_id.upper(),end)

			# also handle possibility of a price statement
			numerals = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "dollar", "dollars"]
			speech_split = six.split(' ')
			seen_price = False
			for i in range(len(speech_split)):
				if speech_split[i] in numerals:
					if seen_price:
						speech_split[i] = ""
					else:
						speech_split[i] = "PRICE"
					seen_price = True
				else:
					seen_price = False
			new_six = ""
			for item in speech_split:
				new_six += item

			final_final_output.append((one, two, three, four, five, six))

		data_string = pickle.dumps(final_final_output)
		'''

class Transition():
	def __init__(self):
		self.id = -1
		self.source_state_id = -1
		self.target_state_id = -1 # should map to the output letter
		self.input_letter = ""
		self.output_letter = "" # should map to the target state
		self.gesture = "None"
		self.speech = []
