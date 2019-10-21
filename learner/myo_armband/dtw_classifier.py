#from lstm import *
from sklearn import svm
from preprocessor import *
from get_features import *
from chunk import *
from matplotlib import pyplot as plt
import numpy as np
import pickle
import operator
import _thread
import myo
import socket
import select
import sys
import time

from scipy.spatial.distance import euclidean

from fastdtw import fastdtw

class SessionListener(myo.DeviceListener):

	def __init__(self):
		self.acceleration = []
		self.gyroscope = []
		self.collecting = False

	def on_paired(self, event):
		print("Hello, {}!".format(event.device_name))
		#event.device.vibrate(myo.VibrationType.short)
	def on_unpaired(self, event):
		return False	# Stop the hub

	def on_locked(self,event):
		print("locked")
	def on_unlocked(self,event):
		print("unlocked")
	def on_emg(self,event):
		emg = event.emg
		print(emg)
	def on_orientation(self, event):
		orientation = event.orientation
		accel = event.acceleration
		gyro = event.gyroscope
		timest = event.timestamp
		# ... do something with that

		self.acceleration.append((accel,timest))
		self.gyroscope.append((gyro,timest))

	def get_acc_gyro_data(self):
		return self.acceleration, self.gyroscope

	def clear_accel_gyro(self):
		self.acceleration = []
		self.gyroscope = []

class GestureRecognizer:

	def __init__(self, arg):
		self.recording = False
		self.analyzing = False
		self.gp = GestureParser()
		self.s = socket.socket()
		self.debug = arg

		if arg != "debug":
			# connect to the server on local computer
			self.s.connect((sys.argv[1], 8878))

	def begin_no_connect(self):
		self.recording = True
		self.done_analysis = False

		print("received start signal in debug")
		_thread.start_new_thread(self.recognize, ("dtw_thread",))
		print("started thread")
		time.sleep(20)
		self.recording = False

		while not self.done_analysis:
			pass

	def begin(self):

		while True:
			print("waiting for start signal")

			while self.analyzing:
				pass

			ready_to_read, ready_to_write, in_error = select.select([self.s], [], [], 3600)
			data = ready_to_read[0].recv(1024)
			if not data:
				break
			string = data.decode("utf-8")
			if string != "sigstart":
				continue
			else:
				self.recording = True

			print("received start signal")
			_thread.start_new_thread(self.recognize, ("dtw_thread",))

			while True:
				print("waiting for end signal")
				ready_to_read, ready_to_write, in_error = select.select([self.s], [], [], 3600)
				data = ready_to_read[0].recv(1024)
				if not data:
					break
				string = data.decode("utf-8")
				print("received string: {}".format(string))
				if string != "sigend":
					continue
				else:
					self.recording = False
					print("received end signal")
					break

	def recognize(self, threadname):
		all_data = []
		myo.init('sdk/myo.framework/myo')
		hub = myo.Hub()
		listener = SessionListener()

		listener.clear_accel_gyro()

		start_time = time.time()
		while hub.run(listener.on_event, 500):
			if not self.recording:
				break
		end_time = time.time()
		self.analyzing = True
			#Plot(listener).main()
		accel_ts_data = listener.acceleration
		gyro_ts_data = listener.gyroscope

		accel_data = []
		gyro_data = []
		ts_data = []
		for d in accel_ts_data:
			accel_data.append(d[0])
			ts_data.append(d[1]/1000000.0)
		for d in gyro_ts_data:
			gyro_data.append(d[0])

		if len(ts_data) == 0 and self.debug != "debug":
			print("GESTURES --> sending NO data back to server")
			ready_to_read, ready_to_write, in_error = select.select([], [self.s], [], 3600)
			ready_to_write[0].send(bytes("start: {} data: {}".format(start_time, ''), 'utf-8'))
			print("GESTURES --> done sending NO data")
			self.analyzing = False
			return

		print(ts_data[0])
		print(ts_data[-1])

		within_interval_index = -1
		for d in range(0,len(ts_data)):
			if ts_data[-1] - ts_data[d] <= end_time - start_time:
				within_interval_index = d
				break

		ts_data = ts_data[within_interval_index:]
		accel_data = accel_data[within_interval_index:]
		gyro_data = gyro_data[within_interval_index:]

		x = []
		y = []
		z = []
		gx = []
		gy = []
		gz = []
		tim = []
		for point in accel_data:
			x.append(point[0])
			y.append(point[1])
			z.append(point[2])

		for point in gyro_data:
			gx.append(point[0])
			gy.append(point[1])
			gz.append(point[2])

		for tstamp in ts_data:
			tim.append(tstamp)

		data = [x,y,z,gx,gy,gz,tim,"all"]
		all_data.append(data)

		# get the linspace
		linsp = np.linspace(start_time,end_time,len(x))

		chunks = self.gp.parse(all_data, linsp)

		if self.debug != "debug":
			print("GESTURES --> sending data back to server")
			print("data: {}".format(chunks))
			ready_to_read, ready_to_write, in_error = select.select([], [self.s], [], 3600)
			ready_to_write[0].send(bytes("start: {} data: {}".format(start_time, chunks), 'utf-8'))
			print("GESTURES --> done sending data")
			self.analyzing = False

		self.done_analysis = True

class GestureParser:

	def __init__(self):
		pass

	def plot_samp(self, name, idx, flat_idxs, sample_x):
		print("plotting")
		plt.subplot(6, 1, 1)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][0])

		plt.subplot(6, 1, 2)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][1])

		plt.subplot(6, 1, 3)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][2])

		plt.subplot(6, 1, 4)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][3])

		plt.subplot(6, 1, 5)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][4])

		plt.subplot(6, 1, 6)
		plt.cla()
		for x in flat_idxs:
			plt.axvline(x,color="333333")
		plt.plot(sample_x[idx][5])

		plt.savefig(name)
		#plt.show()

	def get_train_test_data(self):

		with open("data_train.pkl", "rb") as fp:
			train = pickle.load(fp)

		train_x = []
		train_y = []
		test_x = []
		test_y = []
		num_none_train = 0
		num_point_train = 0
		num_beat_train = 0

		rest = []
		for t in train:
			if t[-1] == "rest":
				rest = [t[0],t[1],t[2],t[3],t[4],t[5]]
				continue
			l = [t[0],t[1],t[2],t[3],t[4],t[5]]
			train_x.append(l)
			if t[-1] == "point":
				train_y.append([1,0,0,0,0])
			elif t[-1] == "present":
				train_y.append([0,1,0,0,0])
			elif t[-1] == "wave":
				train_y.append([0,0,1,0,0])
			elif t[-1] == "beat":
				train_y.append([0,0,0,1,0])
			else: # beat
				train_y.append([0,0,0,0,1])

		return train_x, train_y, rest

	def convert_idx_to_class(self,idx):
		if idx == 0:
			return "point"
		elif idx == 1:
			return "present"
		elif idx == 2:
			return "wave"
		elif idx == 3:
			return "beat"
		elif idx == 4:
			return "none"

	def parse(self, sample_x_raw, linsp):
		train_x, train_y, rest = self.get_train_test_data()

		# obtain preprocessed data
		# perform low-pass filter
		# remove still frames
		preproc = Preprocessor()
		bounds_train = preproc.find_active_frames(train_x)

		# parse the sample and timestamp data
		#with open("data_sample.pkl", "rb") as fp:
		#	sample = pickle.load(fp)

		sample_x = []
		for t in sample_x_raw:
			l = [t[0],t[1],t[2],t[3],t[4],t[5],t[6]] # t[6] is the timestamp data
			sample_x.append(l)

		active_frames_x, flat_idxs_x = preproc.get_idx_active_frames(sample_x[0][0])
		active_frames_y, flat_idxs_y = preproc.get_idx_active_frames(sample_x[0][1])
		active_frames_z, flat_idxs_z = preproc.get_idx_active_frames(sample_x[0][2])

		# offset everything by rest
		rest_vals = []
		for arr in rest:
			rest_vals.append(np.average(np.array(arr)))

		print(len(rest_vals))

		for t_x in train_x:
			for i in range(0,len(t_x)):
				comp = t_x[i]
				comp[:] = [x - rest_vals[i] for x in comp]

		print(len(sample_x[0]))
		for samp_x in sample_x:
			for i in range(0,len(samp_x)-1):
				comp = samp_x[i]
				comp[:] = [x - rest_vals[i] for x in comp]

		# trim the edges of the training data
		for i in range(len(train_x)):
			for j in range(len(train_x[i])):
				train_x[i][j] = train_x[i][j][bounds_train[i][0]:bounds_train[i][1]+1]

		# normalize everything based on maximum observed value
		maxs = []
		for i in range(0,6):
			maximum = 0
			for t_x in train_x:
				max_val = max(max(t_x[i]), abs(min(t_x[i])))
				if max_val > maximum:
					maximum = max_val
			maxs.append(maximum)

		for t_x in train_x:
			for i in range(0,len(t_x)):
				comp = t_x[i]
				maximum = maxs[i]
				comp[:] = [x / maximum for x in comp]
		for samp_x in sample_x:
			for i in range(0,len(samp_x)-1):
				comp = samp_x[i]
				maximum = maxs[i]
				comp[:] = [x / maximum for x in comp]

		flat_idxs = [0]
		for i in range(1,len(sample_x[0][0])):
			if i in flat_idxs_x and i in flat_idxs_y and i in flat_idxs_z:
				flat_idxs.append(i)
		if len(sample_x[0][0])-1 not in flat_idxs:
			flat_idxs.append(len(sample_x[0][0])-1)

		#plot_samp("",0,[],train_x)
		#self.plot_samp("sample4.png",0,flat_idxs,sample_x)

		gaps = []
		starter = flat_idxs[0]
		curr_end = flat_idxs[0]
		for idx in flat_idxs[1:]:
			if idx - curr_end <= 1:
				curr_end = idx
			else:
				gaps.append((starter,curr_end))
				curr_end = idx
				starter = idx

		if starter != idx:
			gaps.append((starter,idx))

		gaps_to_split = []

		window = 5
		starter = 0
		for gap in gaps:
			if gap[0] == 0:
				continue
			# find the end idx for the data: 
			end_idx = gap[0]

			# find the start idx for the data:
			start_ts = sample_x[0][-1][gap[0]] - window
			while True:
				if sample_x[0][-1][starter] > start_ts:
					break
				else:
					starter += 1

			start_idx = starter

			# get each gap into a dictionary
			gaps_in_window = []
			for other_gap in gaps:
				if other_gap[1] > start_idx and other_gap[0] <= end_idx:
					gaps_in_window.append(other_gap)

			print("gaps in window: {}".format(gaps_in_window))

			# get all combinations of gestures, classify as chunk
			for start_gap in gaps_in_window:
				for end_gap in gaps_in_window:
					if not (start_gap[0] >= end_gap[0]) and not (start_gap[1] >= end_gap[1]):

						in_g2s = False
						for gap2split in gaps_to_split:
							if (start_gap,end_gap) == gap2split:
								in_g2s = True
						if in_g2s:
							continue
						else:
							gaps_to_split.append((start_gap,end_gap))

		# split gaps into 4 threads
		th_gaps = [[],[],[],[]]
		index = 0
		for gap in gaps_to_split:
			th_gaps[index].append(gap)
			index = (index+1)%4

		gap_indicator1 = [False]
		gap_indicator2 = [False]
		gap_indicator3 = [False]
		gap_indicator4 = [False]

		chunks = []

		print(gaps)
		
		_thread.start_new_thread(self.gap_threader, ("gap_thread1", sample_x, train_x, th_gaps[0], gap_indicator1, chunks))
		_thread.start_new_thread(self.gap_threader, ("gap_thread2", sample_x, train_x, th_gaps[1], gap_indicator2, chunks))
		_thread.start_new_thread(self.gap_threader, ("gap_thread3", sample_x, train_x, th_gaps[2], gap_indicator3, chunks))
		_thread.start_new_thread(self.gap_threader, ("gap_thread4", sample_x, train_x, th_gaps[3], gap_indicator4, chunks))
		

		while not (gap_indicator1[0] and gap_indicator2[0] and gap_indicator3[0] and gap_indicator4[0]):
			pass

		# print the chunks
		print("~~~~")
		for chunk in chunks:
			print(str(chunk))

		'''
		# classify each chunk
		window = 5
		starter = 0
		chunks = []
		for gap in gaps:
			if gap[0] == 0:
				continue
			# find the end idx for the data: 
			end_idx = gap[0]

			# find the start idx for the data:
			start_ts = sample_x[0][-1][gap[0]] - window
			while True:
				if sample_x[0][-1][starter] > start_ts:
					break
				else:
					starter += 1

			start_idx = starter

			# get each gap into a dictionary
			gaps_in_window = []
			for gap in gaps:
				if gap[1] > start_idx and gap[0] <= end_idx:
					gaps_in_window.append(gap)

			#print(gaps_in_window)

			# get all combinations of gestures, classify as chunk
			for start_gap in gaps_in_window:
				for end_gap in gaps_in_window:
					if not (start_gap[0] >= end_gap[0]) and not (start_gap[1] >= end_gap[1]):

						# compose the data array
						dx = sample_x[0][0]
						dy = sample_x[0][1]
						dz = sample_x[0][2]
						dgx = sample_x[0][3]
						dgy = sample_x[0][4]
						dgz = sample_x[0][5]

						# using DTW
						x = sample_x[0][0][start_gap[1]:end_gap[0]]
						y = train_x[0][0]
						distance0, path = fastdtw(x, y, dist=euclidean)
						print("{} - {}".format(start_gap,end_gap))
						#plt.subplot(2, 1, 1)
						#plt.plot(x)
						#plt.subplot(2, 1, 2)
						#plt.plot(y)
						x = sample_x[0][1][start_gap[1]:end_gap[0]]
						y = train_x[0][1]
						distance1, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][2][start_gap[1]:end_gap[0]]
						y = train_x[0][2]
						distance2, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][3][start_gap[1]:end_gap[0]]
						y = train_x[0][3]
						distance3, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][4][start_gap[1]:end_gap[0]]
						y = train_x[0][4]
						distance4, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][5][start_gap[1]:end_gap[0]]
						y = train_x[0][5]
						distance5, path = fastdtw(x, y, dist=euclidean)
						
						x = sample_x[0][0][start_gap[1]:end_gap[0]]
						y = train_x[1][0]
						distance6, path = fastdtw(x, y, dist=euclidean)
						#print(distance6)
						x = sample_x[0][1][start_gap[1]:end_gap[0]]
						y = train_x[1][1]
						distance7, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][2][start_gap[1]:end_gap[0]]
						y = train_x[1][2]
						distance8, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][3][start_gap[1]:end_gap[0]]
						y = train_x[1][3]
						distance9, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][4][start_gap[1]:end_gap[0]]
						y = train_x[1][4]
						distance10, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][5][start_gap[1]:end_gap[0]]
						y = train_x[1][5]
						distance11, path = fastdtw(x, y, dist=euclidean)

						x = sample_x[0][0][start_gap[1]:end_gap[0]]
						y = train_x[2][0]
						distance12, path = fastdtw(x, y, dist=euclidean)
						#print(distance12)
						x = sample_x[0][1][start_gap[1]:end_gap[0]]
						y = train_x[2][1]
						distance13, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][2][start_gap[1]:end_gap[0]]
						y = train_x[2][2]
						distance14, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][3][start_gap[1]:end_gap[0]]
						y = train_x[2][3]
						distance15, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][4][start_gap[1]:end_gap[0]]
						y = train_x[2][4]
						distance16, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][5][start_gap[1]:end_gap[0]]
						y = train_x[2][5]
						distance17, path = fastdtw(x, y, dist=euclidean)

						#plt.show()

						point_score = distance0 + distance1 + distance2 + distance3 + distance4 + distance5
						present_score = distance6 + distance7 + distance8 + distance9 + distance10 + distance11
						wave_score = distance12 + distance13 + distance14 + distance15 + distance16 + distance17
						#present_score = distance18 + distance19 + distance20 + distance21 + distance22 + distance23

						print("{}  {}  {}  {}  {}  {}".format(distance0,distance1,distance2,distance3,distance4,distance5))
						print("{}  {}  {}  {}  {}  {}".format(distance6,distance7,distance8,distance9,distance10,distance11))
						print("{}  {}  {}  {}  {}  {}".format(distance12,distance13,distance14,distance15,distance16,distance17))
						#print("{}		{}		{}		{}		{}		{}".format(distance18,distance19,distance20,distance21,distance22,distance23))

						chooser_arr = [point_score, present_score, wave_score]
						minimum = min(chooser_arr)
						classification = chooser_arr.index(minimum)

						# switch to beat if the classification isn't strong enough
						if minimum > 100:
							classification = 3

						print("{} {} {} --- {}".format(point_score, present_score, wave_score, self.convert_idx_to_class(classification)))
						chunks.append(GestureChunk(start_gap[1], end_gap[0], self.convert_idx_to_class(classification), minimum))
		'''

		# prioritize chunks
		# first collect beat chunks
		beat_chunks = []
		for chunk in chunks:
			if chunk.classification == "beat":
				beat_chunks.append(chunk)
		for chunk in beat_chunks:
			chunks.remove(chunk)

		chunks.sort(key=operator.attrgetter('length'))

		added_chunks = []

		for chunk in chunks:

			overlapping_chunks = []
			for added_chunk in added_chunks:
				if (chunk.start_idx >= added_chunk.start_idx and chunk.start_idx < added_chunk.end_idx) or (chunk.end_idx <= added_chunk.end_idx and chunk.end_idx > added_chunk.start_idx):
					overlapping_chunks.append(added_chunk)

			is_higher_prob = True
			for overlapping_chunk in overlapping_chunks:
				if chunk.probability > overlapping_chunk.probability:
					is_higher_prob = False

			if is_higher_prob:
				added_chunks.append(chunk)
				for ch in overlapping_chunks:
					added_chunks.remove(ch)

		for chunk in beat_chunks:

			overlapping_chunks = []
			for added_chunk in added_chunks:
				if (chunk.start_idx >= added_chunk.start_idx and chunk.start_idx <= added_chunk.end_idx) or (chunk.end_idx <= added_chunk.end_idx and chunk.end_idx >= chunk.start_idx):
					overlapping_chunks.append(added_chunk)

			if len(overlapping_chunks) == 0:
				added_chunks.append(chunk)

		print("~~~~")
		for chunk in added_chunks:
			print(str(chunk))

		to_return = ""
		for chunk in added_chunks:
			# convert chunk start and end time
			chunk.start_time = linsp[chunk.start_idx]
			chunk.end_time = linsp[chunk.end_idx]
			to_return += chunk.stringify()

		return to_return

	def gap_threader(self, threadname, sample_x, train_x, gap_pairs, indicator, chunks):
		print("in the threader {} with gaps {}".format(threadname, gap_pairs))
		'''
		window = 5
		starter = 0
		for gap in gaps:
			if gap[0] == 0:
				continue
			# find the end idx for the data: 
			end_idx = gap[0]

			# find the start idx for the data:
			start_ts = sample_x[0][-1][gap[0]] - window
			while True:
				if sample_x[0][-1][starter] > start_ts:
					break
				else:
					starter += 1

			start_idx = starter

			# get each gap into a dictionary
			gaps_in_window = []
			for other_gap in other_gaps:
				if other_gap[1] > start_idx and other_gap[0] <= end_idx:
					gaps_in_window.append(other_gap)

			print("gaps in {} window: {}".format(threadname, gaps_in_window))

			# get all combinations of gestures, classify as chunk
			for start_gap in gaps_in_window:
				for end_gap in gaps_in_window:
					if not (start_gap[0] >= end_gap[0]) and not (start_gap[1] >= end_gap[1]):

						# check chunks
						i = 0
						to_continue = False
						while i < len(chunks):
							ch = chunks[i]
							if ch.start_idx == start_gap[1] and ch.end_idx == end_gap[0]:
								to_continue = True
								break
							i += 1
		'''
		for gap_pair in gap_pairs:
			start_gap = gap_pair[0]
			end_gap = gap_pair[1]

			# compose the data array
			dx = sample_x[0][0]
			dy = sample_x[0][1]
			dz = sample_x[0][2]
			dgx = sample_x[0][3]
			dgy = sample_x[0][4]
			dgz = sample_x[0][5]

			# using DTW
			x = sample_x[0][0][start_gap[1]:end_gap[0]]
			y = train_x[0][0]
			distance0, path = fastdtw(x, y, dist=euclidean)
			print("{} - {}".format(start_gap,end_gap))
			#plt.subplot(2, 1, 1)
			#plt.plot(x)
			#plt.subplot(2, 1, 2)
			#plt.plot(y)
			x = sample_x[0][1][start_gap[1]:end_gap[0]]
			y = train_x[0][1]
			distance1, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][2][start_gap[1]:end_gap[0]]
			y = train_x[0][2]
			distance2, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][3][start_gap[1]:end_gap[0]]
			y = train_x[0][3]
			distance3, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][4][start_gap[1]:end_gap[0]]
			y = train_x[0][4]
			distance4, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][5][start_gap[1]:end_gap[0]]
			y = train_x[0][5]
			distance5, path = fastdtw(x, y, dist=euclidean)
					
			x = sample_x[0][0][start_gap[1]:end_gap[0]]
			y = train_x[1][0]
			distance6, path = fastdtw(x, y, dist=euclidean)
			#print(distance6)
			x = sample_x[0][1][start_gap[1]:end_gap[0]]
			y = train_x[1][1]
			distance7, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][2][start_gap[1]:end_gap[0]]
			y = train_x[1][2]
			distance8, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][3][start_gap[1]:end_gap[0]]
			y = train_x[1][3]
			distance9, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][4][start_gap[1]:end_gap[0]]
			y = train_x[1][4]
			distance10, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][5][start_gap[1]:end_gap[0]]
			y = train_x[1][5]
			distance11, path = fastdtw(x, y, dist=euclidean)

			x = sample_x[0][0][start_gap[1]:end_gap[0]]
			y = train_x[2][0]
			distance12, path = fastdtw(x, y, dist=euclidean)
			#print(distance12)
			x = sample_x[0][1][start_gap[1]:end_gap[0]]
			y = train_x[2][1]
			distance13, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][2][start_gap[1]:end_gap[0]]
			y = train_x[2][2]
			distance14, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][3][start_gap[1]:end_gap[0]]
			y = train_x[2][3]
			distance15, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][4][start_gap[1]:end_gap[0]]
			y = train_x[2][4]
			distance16, path = fastdtw(x, y, dist=euclidean)
			x = sample_x[0][5][start_gap[1]:end_gap[0]]
			y = train_x[2][5]
			distance17, path = fastdtw(x, y, dist=euclidean)

			'''
						x = sample_x[0][0][start_gap[1]:end_gap[0]]
						y = train_x[3][0]
						distance18, path = fastdtw(x, y, dist=euclidean)
						#print(distance18)
						x = sample_x[0][1][start_gap[1]:end_gap[0]]
						y = train_x[3][1]
						distance19, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][2][start_gap[1]:end_gap[0]]
						y = train_x[3][2]
						distance20, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][3][start_gap[1]:end_gap[0]]
						y = train_x[3][3]
						distance21, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][4][start_gap[1]:end_gap[0]]
						y = train_x[3][4]
						distance22, path = fastdtw(x, y, dist=euclidean)
						x = sample_x[0][5][start_gap[1]:end_gap[0]]
						y = train_x[3][5]
						distance23, path = fastdtw(x, y, dist=euclidean)
			'''

			#plt.show()

			point_score = distance0 + distance1 + distance2 + distance3 + distance4 + distance5
			present_score = distance6 + distance7 + distance8 + distance9 + distance10 + distance11
			wave_score = distance12 + distance13 + distance14 + distance15 + distance16 + distance17
			#present_score = distance18 + distance19 + distance20 + distance21 + distance22 + distance23

			print("{}  {}  {}  {}  {}  {}".format(distance0,distance1,distance2,distance3,distance4,distance5))
			print("{}  {}  {}  {}  {}  {}".format(distance6,distance7,distance8,distance9,distance10,distance11))
			print("{}  {}  {}  {}  {}  {}".format(distance12,distance13,distance14,distance15,distance16,distance17))
			#print("{}		{}		{}		{}		{}		{}".format(distance18,distance19,distance20,distance21,distance22,distance23))

			# voting
			'''
						counts = [0,0,0,0] # point, sweep, present, group
						dx = [distance0,distance6,distance12,distance18]
						dy = [distance1,distance7,distance13,distance19]
						dz = [distance2,distance8,distance14,distance20]
						dgx = [distance3,distance9,distance15,distance21]
						dgy = [distance4,distance10,distance16,distance22]
						dgz = [distance5,distance11,distance17,distance23]
						counts[dx.index(min(dx))] += 1
						counts[dy.index(min(dy))] += 1
						counts[dz.index(min(dz))] += 1
						counts[dgx.index(min(dgx))] += 1
						counts[dgy.index(min(dgy))] += 1
						counts[dgz.index(min(dgz))] += 1
			'''

			chooser_arr = [point_score, present_score, wave_score]
			minimum = min(chooser_arr)
			classification = chooser_arr.index(minimum)

			# switch to beat if the classification isn't strong enough
			if minimum > 100:
				classification = 3

			print("{} {} {} --- {}".format(point_score, present_score, wave_score, self.convert_idx_to_class(classification)))
			chunks.append(GestureChunk(start_gap[1], end_gap[0], self.convert_idx_to_class(classification), minimum))

		indicator[0] = True

gr = GestureRecognizer("connect" if sys.argv[1] != "debug" else "debug")
if sys.argv[1] == "debug":
	gr.begin_no_connect()
else:
	gr.begin()
