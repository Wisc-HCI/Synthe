from alphabet import *
from copy import *
import random
from random import shuffle
import math

class Bodystorm():

	def __init__(self, design):
		self.SIGMA = None
		self.OMEGA = None
		self.GAZE = None
		self.SIGMA_map = None
		self.OMEGA_map = None
		self.SIGMA_map_rev = None
		self.OMEGA_map_rev = None
		self.GAZE_map = None
		self.GAZE_map_rev = None
		self.GESTURE_map = None
		self.GESTURE_map_rev = None

		self.demo_number = 1

		# UNCOMMENT
		self.populate_sigma_omega()

		self.design = design

	def populate_sigma_omega(self):
		self.initialize_maps()

		self.SIGMA = Alphabet.get_inputs()
		self.OMEGA = Alphabet.get_outputs()

		self.GAZE = Gaze.get_gazes()
		self.GESTURE = Gesture.get_gestures()

		self.fill_maps()

		self.demos = []
		#self.demos = [Demo([("Empty", Output("greeting")), ("greeting", Output("welcome")), ("gratitude", Output("Empty")), ("location_query", Output("location_statement")), ("gratitude", Output("confirm")), ("Empty", Output("farewell"))], "Session{}".format(self.demo_number))]
		#self.demo_number += 1

	def create_demo(self, input_arr, output_arr, gestures=[]):
		print("BODYSTORM >> creating demo from classified speech")

		# return if the demo is length 0
		if len(input_arr) < 1 and len(output_arr) < 1:
			return

		print("GESTURES")
		print(gestures)
		print("OUTPUT_ARR")
		print(output_arr)

		# parse the gestures array
		# start: 1553722212.6676118 data: [1553722214.0913858,1553722214.4122365,beat][1553722214.472396,1553722217.1194124,beat][1553722218.2223358,1553722220.0872793,beat]'
		gstr = gestures.decode("utf-8")
		start_idx = 7
		start_idx_end = gstr.find("data:") - 1
		data_idx = gstr.find("data:") + 6

		start_time = float(gstr[start_idx:start_idx_end])
		data_string = gstr[data_idx:]

		print(start_idx)
		print(start_idx_end)
		print(data_idx)
		print(start_time)
		print(data_string)

		data_components = []
		while True:
			if data_string.find('[') == -1:
				break
			data_components.append(data_string[1:data_string.find(']')])
			data_string = data_string[data_string.find(']')+1:]
			print(data_components)

		print(data_components) 

		data_tuples = []
		for dc in data_components:
			start_time_rel = float(dc[:dc.find(',')])
			dc = dc[dc.find(',')+1:]
			end_time_rel = float(dc[:dc.find(',')])
			dc = dc[dc.find(',')+1:]
			ges = dc
			data_tuples.append((start_time_rel - start_time, end_time_rel - start_time, "{}{}".format(ges[0].upper(),ges[1:])))

		print(data_tuples)

		# derive a set of boundaries for each speech utterance
		bnd = {}   # each tup in the output is mapped to a start and end to the boundary
		for i in range(len(output_arr)):
			if i == 0 and len(output_arr) > 1:
				bnd[output_arr[i]] = (output_arr[i][3] - ((output_arr[i][3])/2.0), output_arr[i][4] + (output_arr[i+1][3]-output_arr[i][4])/2.0)
			elif i == len(output_arr) - 1 and len(output_arr) > 1:
				bnd[output_arr[i]] = (output_arr[i][3] - ((output_arr[i][3] - output_arr[i-1][4])/2.0), output_arr[i][4]+1)
			elif len(output_arr) == 1:
				bnd[output_arr[i]] = (output_arr[i][3] - ((output_arr[i][3])/2.0), output_arr[i][4]+1)
			else:
				bnd[output_arr[i]] = (output_arr[i][3] - ((output_arr[i][3] - output_arr[i-1][4])/2.0), output_arr[i][4] + (output_arr[i+1][3]-output_arr[i][4])/2.0)

		gest_dict = {}
		for tup in output_arr:
			for gest_tup in data_tuples:
				gest_length = gest_tup[1] - gest_tup[0]

				if gest_length > bnd[tup][1] - bnd[tup][0] and (min(gest_tup[1],bnd[tup][1]) - max(gest_tup[0],bnd[tup][0]) >= (bnd[tup][1] - bnd[tup][0])*1.0/2) and gest_length > 1:
					print("gesture is longer than the speech time")
					if tup in gest_dict:
						if gest_dict[tup] == "beat":
							gest_dict[tup] = gest_tup[2]
					else:
						gest_dict[tup] = gest_tup[2]
				elif gest_length <= bnd[tup][1] - bnd[tup][0] and (min(gest_tup[1],bnd[tup][1]) - max(gest_tup[0],bnd[tup][0]) >= gest_length*1.0/2) and gest_length > 1:
					print("speech is longer than the gesture time")
					if tup in gest_dict:
						if gest_dict[tup] == "beat":
							gest_dict[tup] = gest_tup[2]
					else:
						gest_dict[tup] = gest_tup[2]

		demo = []

		# we need to merge the arrays
		total_array = []
		inp_idx = 0
		out_idx = 0

		while True:
			if inp_idx >= len(input_arr) and out_idx >= len(output_arr):
				break

			elif inp_idx >= len(input_arr):
				while out_idx < len(output_arr):
					total_array.append(("output", output_arr[out_idx]))
					out_idx += 1
				break
			elif out_idx >= len(output_arr):
				while inp_idx < len(input_arr):
					total_array.append(("input", input_arr[inp_idx]))
					inp_idx += 1
				break

			else:
				# if the next input comes before the next output
				if input_arr[inp_idx][3] < output_arr[out_idx][3]:
					total_array.append(("input", input_arr[inp_idx]))
					inp_idx += 1
				else:
					total_array.append(("output", output_arr[out_idx]))
					out_idx += 1

		# now that the arrays are merged, walk through them and add empties
		idx = 0
		prev = "output"
		while True:
			if idx >= len(total_array):
				if total_array[-1][0] == "input":
					total_array.append(("output", "Empty"))
				break

			if total_array[idx][0] == "output" and prev == "output":
				total_array.insert(idx, ("input", "Empty"))
			elif total_array[idx][0] == "input" and prev == "input":
				total_array.insert(idx, ("output", "Empty"))
			else:
				prev = total_array[idx][0]
				idx += 1

		# check that the total_array is even
		if len(total_array)%2 != 0:
			print("BODYSTORM >> ERROR: the demo does not have the same number of inputs and outputs")

		# check that the demo does not have repeating empties, and len(demo) is < 8
		# first find and merge repeated Empties
		print("BODYSTORM >> merging repeated Empties")
		self.merge_repeated_empty_inputs(total_array)
		self.merge_repeated_empty_outputs(total_array)

		# now check whether len(demo) <= 8
		# if > 8:
		# 1) remove duplicates
		# 2) (if still > 8) condense remaining empties
		# 3) (if still > 8) chop the end, replace with most common end
		#pass
		#print(total_array)

		# now, construct the demo
		idx = 0
		while True:
			if idx >= len(total_array):
				break

			if total_array[idx + 1][1] == "Empty":
				demo.append((Input(total_array[idx][1][0], speech=total_array[idx][1][5]), Output("Empty", speech="")))
			elif total_array[idx][1] == "Empty":
				time = 0
				if idx == 0:
					time = int(round(total_array[idx+1][1][3]))
				else:
					time = int(round(total_array[idx+1][1][3] - total_array[idx-1][1][4]))
				empty_inp = Input("Empty", "")
				empty_inp.time = time
				if total_array[idx+1][1] in gest_dict:
					demo.append((empty_inp, Output(total_array[idx+1][1][0], speech=total_array[idx+1][1][5], gesture=gest_dict[total_array[idx+1][1]])))
				else:
					demo.append((empty_inp, Output(total_array[idx+1][1][0], speech=total_array[idx+1][1][5])))
			else:
				if total_array[idx+1][1] in gest_dict:
					demo.append((Input(total_array[idx][1][0], speech=total_array[idx][1][5]), Output(total_array[idx+1][1][0], speech=total_array[idx+1][1][5], gesture=gest_dict[total_array[idx+1][1]])))
				else:
					demo.append((Input(total_array[idx][1][0], speech=total_array[idx][1][5]), Output(total_array[idx+1][1][0], speech=total_array[idx+1][1][5])))

			idx += 2

		self.demos.append(Demo(demo, "Session{}".format(self.demo_number), self.delete_demo))
		self.demo_number += 1

	def merge_repeated_empty_outputs(self, array):
		
		empty_idxs = []
		empty_tracking = False
		for i in range(len(array)):
			if array[i][0] == "input":
				continue
			if array[i][1] == "Empty" and empty_tracking == False:
				empty_tracking = True
				empty_idxs.append([])
				empty_idxs[-1].append(i)
			elif array[i][1] == "Empty" and empty_tracking:
				empty_idxs[-1].append(i)
			elif array[i][1] != "Empty" and empty_tracking:
				empty_tracking = False

				# remove any sets if idxs that are <=1
				if len(empty_idxs[-1]) <= 1: 
					empty_idxs = empty_idxs[:-1]

		# remove any sets if idxs that are <=1
		if len(empty_idxs) > 0 and len(empty_idxs[-1]) <= 1: 
			empty_idxs = empty_idxs[:-1]

		empty_idxs_fixes = []
		for empty_seq in empty_idxs:

			# special case: the empties are all at the end
			if empty_seq[-1] == len(array) - 1:
				max_confidence_idx = -1
				best_classification = "Empty"
				speech = ""
				for i in empty_seq:
					h_input = array[i-1]
					input_confidence = float(h_input[1][1])
					if input_confidence > max_confidence_idx:
						max_confidence_idx = input_confidence
						best_classification = h_input[1][0]

					speech += h_input[1][-1] + ". "

				# form a replacement tuple
				fix = [(best_classification, max_confidence_idx, -1, array[empty_seq[0]-1][1][3], array[empty_seq[-1]-1][1][4], speech)]
				empty_idxs_fixes.append(fix)

			# normal case
			else:
				max_confidence = [-1,-1]
				max_confidence_idxs = [-1,-1]
				best_classifications = ["Empty", "Empty"]
				speech = ["", ""]

				# add a dangler on the end
				empty_seq.append(empty_seq[-1] + 2)
				for i in empty_seq:
					h_input = array[i-1]
					#print(h_input)
					input_confidence = float(h_input[1][1])
					if input_confidence > max_confidence[1]:
						max_confidence[1] = input_confidence
						max_confidence_idxs[1] = i
						best_classifications[1] = h_input[1][0]

						# do the ol switcharoo
						if max_confidence[0] < max_confidence[1]:
							keep = [max_confidence,best_classifications,max_confidence_idxs]
							for best in keep:
								temp = best[1]
								best[1] = best[0]
								best[0] = temp

				if max_confidence_idxs[0] > max_confidence_idxs[1]:
					keep = [max_confidence,best_classifications,max_confidence_idxs]
					for best in keep:
						temp = best[1]
						best[1] = best[0]
						best[0] = temp

				del empty_seq[-1]


				# now we need to assign the speeches
				midpoint = math.floor(abs(max_confidence_idxs[0] - max_confidence_idxs[1])/2) + min(max_confidence_idxs)

				if midpoint%2==0:
					midpoint -= 1

				for i in empty_seq:
					if i <= midpoint:
						speech[0] += array[i-1][1][-1] + ". "
					else:
						speech[1] += array[i-1][1][-1] + ". "
				speech[1] += array[empty_seq[-1]+1][1][-1] + "."

				# set up the fix
				fix = [(best_classifications[0], max_confidence[0], -1 , array[empty_seq[0]-1][1][3], array[midpoint-1][1][4], speech[0]),
						(best_classifications[1], max_confidence[1], -1 , array[midpoint+1][1][4], array[empty_seq[-1]-1][1][4], speech[1])]
				#print(fix)
				empty_idxs_fixes.append(fix)

		if len(empty_idxs_fixes) != len(empty_idxs):
			print("BODYSTORM >> ERROR: fixing empties")
			exit()

		# going backwards, fix the elements
		for i in range(len(empty_idxs)):
			j = len(empty_idxs) - 1 - i    # counting backwards

			start_idx = empty_idxs[j][0]
			start_idx = empty_idxs[j][-1] + 1

			if start_idx == len(array):
				start_idx -= 1
			for k in range(start_idx, empty_idxs[j][0]-2, -1):

				del array[k]

			array.insert(empty_idxs[j][0]-1,("input", empty_idxs_fixes[j][0]))
			array.insert(empty_idxs[j][0],("output", "Empty"))
			if len(empty_idxs_fixes[j]) > 1:
				array.insert(empty_idxs[j][0]+1,("input", empty_idxs_fixes[j][1]))


	def merge_repeated_empty_inputs(self, array):

		empty_idxs = []
		empty_tracking = False
		for i in range(len(array)):
			if array[i][0] == "output":
				continue
			if array[i][1] == "Empty" and empty_tracking == False:
				empty_tracking = True
				empty_idxs.append([])
				empty_idxs[-1].append(i)
			elif array[i][1] == "Empty" and empty_tracking:
				empty_idxs[-1].append(i)
			elif array[i][1] != "Empty" and empty_tracking:
				empty_tracking = False

				# remove any sets if idxs that are <=1
				if len(empty_idxs[-1]) <= 1: 
					empty_idxs = empty_idxs[:-1]

		# remove any sets if idxs that are <=1
		if len(empty_idxs) > 0 and len(empty_idxs[-1]) <= 1: 
			empty_idxs = empty_idxs[:-1]

		empty_idxs_fixes = []
		for empty_seq in empty_idxs:

			# special case: the empties are all at the begining
			if empty_seq[0] == 0:
				max_confidence_idx = -1
				best_classification = "Empty"
				speech = ""
				for i in empty_seq:
					h_output = array[i+1]
					input_confidence = float(h_output[1][1])
					if input_confidence > max_confidence_idx:
						max_confidence_idx = input_confidence
						best_classification = h_output[1][0]

					speech += h_output[1][-1] + ". "

				# form a replacement tuple
				fix = [(best_classification, max_confidence_idx, -1, array[empty_seq[0]+1][1][3], array[empty_seq[-1]-1][1][4], speech)]
				empty_idxs_fixes.append(fix)

			# normal case
			else:
				max_confidence = [-1,-1]
				max_confidence_idxs = [-1,-1]
				best_classifications = ["Empty", "Empty"]
				speech = ["", ""]
				idxs = [-1,-1]

				# add a dangler on the beginning
				empty_seq.insert(0, empty_seq[0] - 2)
				for i in empty_seq:
					h_output = array[i+1]
					#print(h_output)
					input_confidence = float(h_output[1][1])
					if input_confidence > max_confidence[1]:
						max_confidence[1] = input_confidence
						max_confidence_idxs[1] = i
						best_classifications[1] = h_output[1][0]
						idxs[1] = i

						# do the ol switcharoo
						if max_confidence[0] < max_confidence[1]:
							keep = [max_confidence,best_classifications,max_confidence_idxs,idxs]
							for best in keep:
								temp = best[1]
								best[1] = best[0]
								best[0] = temp

				if idxs[0] > idxs[1]:
					keep = [max_confidence,best_classifications,max_confidence_idxs,idxs]
					for best in keep:
						temp = best[1]
						best[1] = best[0]
						best[0] = temp

				del empty_seq[0]

				# now we need to assign the speeches
				midpoint = math.floor(abs(max_confidence_idxs[0] - max_confidence_idxs[1])/2) + min(max_confidence_idxs)

				if midpoint%2==1:
					midpoint -= 1

				for i in empty_seq:
					if i <= midpoint:
						speech[0] += array[i-1][1][-1] + ". "
					else:
						speech[1] += array[i-1][1][-1] + ". "
				speech[1] += array[empty_seq[-1]+1][1][-1] + "."

				# set up the fix
				fix = [(best_classifications[0], max_confidence[0], -1 , array[empty_seq[0]-1][1][3], array[midpoint-1][1][4], speech[0]),
						(best_classifications[1], max_confidence[1], -1 , array[midpoint+1][1][4], array[empty_seq[-1]+1][1][4], speech[1])]
				#print(fix)
				empty_idxs_fixes.append(fix)

		if len(empty_idxs_fixes) != len(empty_idxs):
			print("BODYSTORM >> ERROR: fixing empties")
			exit()

		#print(array)

		# going backwards, fix the elements
		#print("before")
		#print(array)
		for i in range(len(empty_idxs)):
			j = len(empty_idxs) - 1 - i    # counting backwards

			start_idx = empty_idxs[j][0]
			start_idx = empty_idxs[j][-1] + 1

			end_idx = 1 if len(empty_idxs_fixes[j]) == 1 else 2
			for k in range(start_idx, empty_idxs[j][0]-end_idx, -1):
				#print(k)

				del array[k]

			if len(empty_idxs_fixes[j]) == 1:
				array.insert(0,("input","Empty"))
				array.insert(1,("output", empty_idxs_fixes[j][0]))
			else:
				array.insert(empty_idxs[j][0]-1,("output",empty_idxs_fixes[j][0]))
				array.insert(empty_idxs[j][0],("input","Empty"))
				array.insert(empty_idxs[j][0]+1,("output",empty_idxs_fixes[j][1]))
		#print("after")
		#print(array)

	def create_demo_from_commandline(self, demo_list):
		'''
		NOTE: this class is for debugging purposes only!
		'''

		# return if the demo is length 0
		if len(demo_list) < 1:
			return

		demo_array = []
		for item in demo_list:
			demo_item = (Input(item[0], "blah\nblah\nblah\nblah\nblah\nblah"), Output(item[1], random.choice(["1", "2", "3", "4", "5", "6", "7"]), gesture=random.choice(["Point", "Present", "Wave", "Beat", "None"])))
			demo_array.append(demo_item)
		demo_object = Demo(demo_array, "Session{}".format(self.demo_number), self.delete_demo)
		self.demos.append(demo_object)
		self.demo_number += 1

	def initialize_maps(self):
		self.SIGMA_map = {}
		self.OMEGA_map = {}
		self.SIGMA_map_rev = {}
		self.OMEGA_map_rev = {}

		self.GAZE_map = {}
		self.GAZE_map_rev = {}
		self.GESTURE_map = {}
		self.GESTURE_map_rev = {}

	def fill_maps(self):

		self.check_preconditions()

		counter = 0
		for item in self.SIGMA:
			self.SIGMA_map[item] = counter
			self.SIGMA_map_rev[counter] = item
			counter += 1
		counter = 0
		for item in self.OMEGA:
			self.OMEGA_map[item] = counter
			self.OMEGA_map_rev[counter] = item
			counter += 1

		# gaze
		counter = 0
		for item in self.GAZE:
			self.GAZE_map[item] = counter
			self.GAZE_map_rev[counter] = item
			counter += 1

		# gesture
		counter = 0
		for item in self.GESTURE:
			self.GESTURE_map[item] = counter
			self.GESTURE_map_rev[counter] = item
			counter += 1

	def get_active_demos(self):
		active_demos = []
		for demo in self.demos:
			if demo.activated:
				active_demos.append(demo)
		return active_demos

	def get_max_demo_len(self, demos=None):
		self.check_preconditions()

		if demos is None:
			demos = self.demos

		return 0 if len(demos) == 0 else len(max(demos,key=len))

	def exists_in_demos(self, inp, out, demos=None):
		if demos is None:
			demos = self.demos

		return_val = False
		for demo_object in demos:
			demo = demo_object.demo_array
			for pair in demo:
				if inp == pair[0].inp and out == pair[1].output:
					return_val = True

		return return_val

	def check_preconditions(self):
		if self.SIGMA is None or self.OMEGA is None:
			print("BODYSTORM >> ERROR: unable to create demos")
			exit(1)

	def delete_demo(self, demo):
		self.demos.remove(demo)

	def get_used_sigmas(self, demos=None):
		if demos is None:
			demos = self.demos
		used_sigmas = {}

		counter = 0
		for demo in demos:
			for item in demo.demo_array:
				if item[0].inp not in used_sigmas:
					used_sigmas[item[0].inp] = counter
					counter += 1

		return used_sigmas

	def get_used_omegas(self, demos=None, n=-1, relaxed=False):
		if demos is None:
			demos = self.demos
		used_omegas = {}

		counter = 0
		print("relaxed? {}".format(relaxed))
		for demo in demos:
			for item in demo.demo_array:
				if not relaxed:
					if item[1].output not in used_omegas:
						used_omegas[item[1].output] = counter
						counter += 1
				else:
					if item[1].relaxed_output not in used_omegas:

						## TEMPORARY BUG FIX
						if item[1].relaxed_output is None:
							print("NONE: {}".format(item[1].output))
						else:
							print("not none: {}".format(item[1].output))
							used_omegas[item[1].relaxed_output] = counter
							counter += 1
		print(used_omegas)

		# other states might exist that we need to fill in with omegas
		omegas = copy(self.OMEGA)
		shuffle(omegas)
		if len(used_omegas) < n:
			omega_counter = 0
			omegas_needed = n - len(used_omegas)

			for om in self.OMEGA:
				if om not in used_omegas:
					used_omegas[om] = counter
					counter += 1

					omega_counter += 1
					if omega_counter >= omegas_needed:
						break

		return used_omegas

	def __str__(self):
		string = ""
		for demo in self.demos:
			string += demo.pretty_string()
		return string

class Demo():

	def __init__(self, demo_array, name, callback=None):
		self.demo_array = demo_array

		self.delete_callback=callback
		self.should_be_deleted=False

		# parameters for the string
		self.id = -1
		self.name = name if name is not None else "Example"
		self.satisfied = 1

		# activated
		self.activated = True

	def setActivated(self, val):
		self.activated = val
		if val == False:
			self.satisfied = 0

	def markForDeletion(self):
		self.should_be_deleted=True
		if self.delete_callback is not None:
			self.delete_callback(self)

	def is_same(self, demo):
		if len(self.demo_array) != len(demo.demo_array):
			return False
		else:
			is_same = True
			for i in range(len(self)):
				if self.demo_array[i][0].inp != demo.demo_array[i][0].inp:
					is_same = False
					break
				elif self.demo_array[i][1].output != demo.demo_array[i][1].output:
					is_same = False
					break
				elif self.demo_array[i][1].gesture != demo.demo_array[i][1].gesture:
					is_same = False
					break
				#elif self.demo_array[i][1].gesture != demo.demo_array[i][1].gesture:
				#	is_same = False
				#	break
			return is_same

	def pretty_string(self):
		string = "START >>>    "
		for item in self.demo_array:
			string += "{} -> {}    ".format(item[0].inp, item[1].output)
		return string

	def __len__(self):
		return len(self.demo_array)

	def __str__(self):
		args = ("{}".format(self.name), "Length: {}".format(len(self)), "Sat.: {}".format(int(round(self.satisfied*100))))
		string = "{0:<0} {1:>12} {2:>12}%".format(*args)
		return string

class Output():

	def __init__(self, output, speech="", gesture="None"):

		self.output = output
		self.relaxed_output = None

		# parameters for the demo
		self.gaze = "Intimacy Modulating"
		self.gesture = gesture
		self.speech = speech
		self.time = 2

		# TODO: this is really hacky and must be removed
		self.updated_gesture = False

	def __str__(self):
		return self.output

class Input():
	def __init__(self, inp, speech=""):
		self.inp = inp
		self.time = 2
		self.speech = speech

	def __str__(self):
		return self.inp
