import socket
import pickle
import select
import sys
import os
from threading import Thread
from intent_parser import *
import intent_parser
import wave
from scipy.io import wavfile
import numpy as np
from copy import deepcopy
import time

class Client():

	def __init__(self):
		self.s = socket.socket()
		self.record_flag = False

		# DO one of the following:
		# 1) if argument 2 exists and the argument is "train", then train a new file
		# 2) if argument 2 exists and the argument is "test", then test the file specified
		# 2) otherwise if the default directory is empty then exit prematurely
		# 3) otherwise (DEBUGGING PURPOSES ONLY), use the most recently-generated file

		# if not empty, determine the most recently-created subdirectory
		most_recent_model = None
		all_subdirs = ['./projects/default/{}'.format(d) for d in os.listdir('./projects/default/') if os.path.isdir('./projects/default/{}'.format(d))]

		# is the latest directory empty?
		directory_is_empty = True if len(all_subdirs) == 0 else False
		if not directory_is_empty:
			latest_subdir = max(all_subdirs, key=os.path.getmtime)

		# now for the if statements
		print(len(sys.argv))
		if len(sys.argv) > 2 and sys.argv[2] == "train" and len(sys.argv) > 3:
			# train a new model
			self.intent_parser_util = IntentRecognition('{}'.format(sys.argv[3]),
				'./config/config_spacy.yml')
		elif len(sys.argv) > 2 and sys.argv[2] == "train" and len(sys.argv) > 3:
			self.intent_parser_util = IntentRecognition('{}'.format(sys.argv[3]),
				'./config/config_spacy.yml')
		elif len(sys.argv) == 3:
			print("ERROR: please input a correct argument")
			exit(0)
		elif directory_is_empty:
			# we can't just train a new model because we don't know what to train!
			print("ERROR: please input a correct argument")
			exit(0)
		else:
			# use the most recently created model
			self.intent_parser_util = IntentRecognition('{}/'.format(latest_subdir),
				'./config/config_spacy.yml')

		self.sample_no = 0
		self.audio_filename = None
		self.increment_audio_file_name()

		# ensure .wav extension
		if ".wav" not in self.audio_filename:
			print("ERROR: audio filename must have .wav extension")
			exit(1)

		self.remove_sound_file()

	def remove_sound_file(self):
		# remove an existing file if it exists
		if os.path.exists(self.audio_filename):
			os.rename(self.audio_filename, "audio_files/{}".format(self.audio_filename))

	def increment_audio_file_name(self):
		self.sample_no += 1
		curr_time = time.time()
		self.audio_filename = "audio_{}_{}.wav".format(self.sample_no, curr_time)

	def connect(self):

		# connect to the server on local computer
		self.s.connect((sys.argv[1], 8888))

		# receive data from the server
		while True:
			print("main looping")
			ready_to_read, ready_to_write, in_error = select.select([self.s], [], [], 3600)
			data = ready_to_read[0].recv(1024)

			if not data:
				self.s.close()
				exit(0)

			string = data.decode("utf-8")
			if string != '':
				if string == "begin":

					#ack
					ready_to_read, ready_to_write, in_error = select.select([], [self.s], [], 3600)
					ready_to_write[0].send(b"ack")
					
					print(data)
					bodystorm_data = None   # mutable object to be used by the thread
					thread = Thread(target=self.gather_data, args=([bodystorm_data]))
					self.record_flag = True
					thread.start()

					# wait for the stop signal
					while True:
						print("looping")
						ready_to_read, ready_to_write, in_error = select.select([self.s], [], [])
						signal = ready_to_read[0].recv(1024)
						signal_string = signal.decode("utf-8")
						print(signal_string + " " + str(len(signal_string)))
						if signal_string == "end":
							print("attempting to end")
							self.record_flag = False
							thread.join()
							print("THREAD JOINED")
							break

					self.remove_sound_file()
					self.increment_audio_file_name()

	def gather_data(self, bodystorm_data):
		audio_listener = AudioInput(self.audio_filename)

		while self.record_flag:
			pass

		audio_listener.terminate_recording()

		data_string = self.speech_to_text()

		ready_to_read, ready_to_write, in_error = select.select([], [self.s], [])
		ready_to_write[0].send(data_string)

	def speech_to_text(self):
		# get the intent array
		# final tuple format: (intent, classification confidence, speaker, start time, end time, speech)
		unparsed_output = intent_parser.recognize_speech(self.audio_filename)
		final_output = []
		for item in unparsed_output:
			parse_data = self.intent_parser_util.parse_intent(item[0])
			print(parse_data)
			print(item)
			temp = (parse_data[0], parse_data[1], item[3], item[1], item[2], item[0])
			final_output.append(temp)

		print(final_output)

		# trim the final output -- likely contains speech from the other person!
		final_output = self.trim_speech_output(final_output)
		print(final_output)

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
		data_string = pickle.dumps(final_output)

		return data_string

	def trim_speech_output(self, final_output):
		new_final_output = []

		#wav = wave.open(self.audio_filename, mode="r")
		#(nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()
		#content = wav.readframes(nframes)
		#samples = np.fromstring(content, dtype=type(sampwidth))
		#print(np.shape(samples))
		#print(framerate)
		#print(nframes)

		# open the wav file
		fs, data = wavfile.read(self.audio_filename)
		data = data[:,0] # convert to a single column

		# store the wav data for each speaker
		speakers = {}

		# loop through each output (all speakers included)
		for output in final_output:
			start_time = output[3]
			end_time = output[4]
			speaker = output[2]

			# create new
			if speaker not in speakers:
				speakers[speaker] = []


			for i in range(int(round(start_time * fs)), int(round(end_time * fs))):
				speakers[speaker].append(abs(data[i]))

		# if there are only 1 or 2 detected speakers, just separate them and take the louder one
		if len(speakers) <= 2:
			print("speaker length is <= 2")

			speaker_averages = {}
			for speaker in speakers:
				speaker_averages[speaker] = np.mean(np.array(speakers[speaker]))

			# it is possible that no data was obtained at all
			if len(speaker_averages) > 0:
				correct_speaker = max(speaker_averages, key=speaker_averages.get)

			for output in final_output:
				if output[2] == correct_speaker:
					new_final_output.append(output)
			print(speaker_averages)
				#elif output[2] > 1: # the only real speakers are 0/1. We classify others as 0/1 based on volume
				#	if abs(speaker_averages[output[2]] - speaker_averages[correct_speaker]) <
		# OTHERWISE, run k-means clustering
		else:
			print("speaker length is > 3")
			threshold = np.mean([abs(i) for i in data])
			data_points = {}
			counter = 0
			mean_up = 0
			num_up = 0
			mean_down = 0
			num_down = 0
			for output in final_output:
				start_time = output[3]
				end_time = output[4]
				average_energy = 0
				for i in range(int(round(start_time * fs)), int(round(end_time * fs))):
					average_energy += abs(data[i])
				average_energy = average_energy/(int(round(end_time * fs)) - int(round(start_time * fs)))
				assignment = "up" if average_energy > threshold else "down"
				if assignment == "up":
					num_up += 1
					mean_up += average_energy
				else:
					num_down += 1
					mean_down += average_energy
				data_points[counter] = {"energy": average_energy, "class": assignment}
				counter += 1

			init_mean_up = 0 if num_up == 0 else mean_up*1.0/num_up
			init_mean_down = 0 if num_down == 0 else mean_down*1.0/num_down

			print("running lloyd's algorithm")
			assignments = self.lloyds_algorithm(data_points, init_mean_up, init_mean_down)
			print(assignments)

			for idx in assignments:
				if assignments[idx]["class"] == "up":
					new_final_output.append(final_output[idx])

		print(new_final_output)

		return new_final_output

	def lloyds_algorithm(self, points, init_mean_up, init_mean_down):
		mean_up = init_mean_up
		mean_down = init_mean_down
		while True:
			print("~~~~~")
			print(mean_up)
			print(mean_down)
			print("~~~~~")

			# do a deepcopy
			old_points = deepcopy(points)

			# assignment step
			for idx in old_points:
				if abs(old_points[idx]["energy"] - init_mean_up) < abs(old_points[idx]["energy"] - init_mean_down):
					points[idx]["class"] = "up"
				else:
					points[idx]["class"] = "down"

			# break step
			same = True
			for idx in points:
				if points[idx]["class"] != old_points[idx]["class"]:
					same = False
					break
			if same:
				break

			# update step
			mean_up = 0
			num_up = 0
			mean_down = 0
			num_down = 0
			for idx in points:
				if points[idx]["class"] == "up":
					num_up += 1
					mean_up += points[idx]["energy"]
				else:
					num_down += 1
					mean_down += points[idx]["energy"]
			mean_up = 0 if num_up == 0 else mean_up*1.0/num_up
			mean_down = 0 if num_down == 0 else mean_down*1.0/num_down

		return points


if __name__ == "__main__":
	client = Client()
	client.connect()
