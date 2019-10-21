import sys
#sys.path.append("pynaoqi-python2.7-2.1.4.13-mac64")
sys.path.append("pynaoqi-python2.7-2.1.4.13-linux64")
import operator
import threading
from threading import Lock
import time
import random
from copy import copy
from naoqi import ALProxy
import numpy as np
from Protocol import Protocol

IP = "10.130.229.213"
PORT = 9559

class Gaze():
	def __init__(self, design):
		self.design = design
		self.Behaviors = {}       # all microinteractions and their current behaviors
		self.Protocols = []       # unchanging list of protocols for the group
		self.CurrMicrointeraction = None   # the currently running microinteraction
		self.CurrBehavior = None  # the currently running behavior

		# the active or queued threads
		# just as it is possible to have multiple different gaze behaviors competing
		#     for each other, it is possible for multiple different microinteractions
		#     to be undergoing the same gaze behavior
		self.GAZE_AT = {}
		self.GAZE_REFERENTIAL = {}
		self.GAZE_COGNITIVE = {}
		self.GAZE_INTIMATE = {}
		self.GAZE_ELSE = {}
		self.threadDicts = {"GAZE_AT": self.GAZE_AT,
							"GAZE_REFERENTIAL": self.GAZE_REFERENTIAL,
							"GAZE_COGNITIVE": self.GAZE_COGNITIVE,
							"GAZE_INTIMACY": self.GAZE_INTIMATE,
							"GAZE_ELSE": self.GAZE_ELSE}

		# self.loop_lock
		self.loop_lock = [True]
		self.lock = Lock()

	def GazeAt(self, microinteraction):
		head_at_human = ALProxy("ALMotion", IP, PORT)
		names = ["HeadPitch", "HeadYaw"]
		angles = [0, 0]
		head_at_human.setStiffnesses("Body", 1.0)
		head_at_human.setAngles(names, angles, 0.1)
		print("Gaze at!")

		while self.loop_lock[0] == True:
			time.sleep(0.1)

	def GazeIntimacy(self, microinteraction):
		print("Gaze intimacy!")
		head_intimacy = ALProxy("ALMotion", IP, PORT)
		angle_list = [0.1396, -0.1396]
		head_intimacy.setStiffnesses("Head", 1.0)
		while self.loop_lock[0] == True:
			head_intimacy.setAngles("HeadYaw", random.choice(angle_list), 0.1)
			print("Gaze intimacy!")
			time_length = np.random.normal(1.96, 0.32)

			# check every 0.5 seconds if the loop_lock still holds
			if self.checkLoopLock(time_length) == True:
			#	self.GazeAt(microinteraction)
				break

			#self.GazeAt(microinteraction)
			names = ["HeadPitch", "HeadYaw"]
			angles = [0, 0]
			head_intimacy.setAngles(names, angles, 0.1)
			print "Gaze at!"
			time_between = np.random.normal(4.75, 1.39)

			# check every 0.5 seconds if the loop_lock still holds
			if self.checkLoopLock(time_between) == True:
				break

	def GazeCognitive(self, microinteraction):
		# look up and then down
		# call GazeIntimacy
		names = ["HeadPitch", "HeadYaw"]
		angles = [-0.2491, 0.1396]
		head_cognition = ALProxy("ALMotion", IP, PORT)
		head_cognition.setAngles(names, angles, 0.05)
		head_cognition.setStiffnesses("Body", 1.0)
		time.sleep(1)
		head_cognition.setAngles(names, [0.0, 0.0], 0.1)
		time_length = np.random.normal(1.96, 0.32)
		time.sleep(time_length)
		print "Gaze cognitive! Intimacy should follow."
		self.GazeIntimacy(microinteraction)

	def GazeReferential(self, microinteraction, para=None):
		print "Gaze referential!"
		head = ALProxy("ALMotion", IP, PORT)
		head.setStiffnesses("Body", 1.0)
		names = ["HeadPitch", "HeadYaw"]
		if microinteraction == "Handoff":
			if para == "left":
				angles = [0.3359041213989258, 0.3819241523742676]
			else:
				angles = [0.37885594367980957, -0.6075060367584229]
			head.setAngles(names, angles, 0.1)
		elif microinteraction == "Instruct" and para != None and "Pick up a piece of bread" in para.strip():
			print para
			instruction = -1
			if para.strip() == "First instruction. Pick up a piece of bread and place it on the plate":
				t = 1.5
				instruction = 1
			elif para == "Second instruction. Pick up the slices of ham and cheese, and place the ham on top of the bread, and the cheese on top of the ham":
				t = 2
				instruction = 2
			else:
				t = 0.8
				instruction = 3
			angles_sandwich = [0.40953004360198975, -0.5507478713989258]
			angles_plate = [0.4724442660808563, 0.22238802909851074]
			angles_halfway = [0.4324442660808563, -0.32238802909851074]

			if self.design == "Instruction-Action-1":
				time.sleep(0.1)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(1.5)
				head.setAngles(names, angles_plate, 0.3)

				time.sleep(2)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(2)
				head.setAngles(names, angles_plate, 0.3)

				time.sleep(1)

				time.sleep(3.8)
				head.setAngles(names, angles_sandwich, 0.2)
				#time.sleep(0.8)
				#head.setAngles(names, angles_plate, 0.3)

				counter = 0
				while self.loop_lock[0] == True and counter < 1.5:
					time.sleep(0.1)
					counter += 0.1

				head.setAngles(names, angles_sandwich, 0.3)
				time.sleep(1)
				head.setAngles(names, angles_plate, 0.3)
			elif self.design == "Instruction-Action-2":
				time.sleep(0.1)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(1.5)
				head.setAngles(names, angles_plate, 0.3)

				# and then pick up a piece of bacon
				time.sleep(1.5)
				head.setAngles(names, angles_sandwich, 0.3)
				time.sleep(1)
				head.setAngles(names, angles_plate, 0.3)

				time.sleep(6)

				#egg
				time.sleep(1.5)
				head.setAngles(names, angles_sandwich, 0.3)
				time.sleep(1)
				head.setAngles(names, angles_plate, 0.3)

				counter = 0
				while self.loop_lock[0] == True and counter < 1.5:
					time.sleep(0.1)
					counter += 0.1

			else:
				time.sleep(0.1)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(1.5)
				head.setAngles(names, angles_plate, 0.3)

				# and add some mayonnaise
				time.sleep(1.5)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(1)
				head.setAngles(names, angles_halfway, 0.1)

				# cucumbers
				time.sleep(1.0)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(0.5)
				head.setAngles(names, angles_plate, 0.2)

				time.sleep(1.5)
				head.setAngles(names, angles_halfway, 0.2)
				time.sleep(1.0)
				head.setAngles(names, angles_plate, 0.2)

				#egg
				time.sleep(1)
				#head.setAngles(names, angles_halfway, 0.2)
				time.sleep(1.5)
				time.sleep(0.5)
				#head.setAngles(names, angles_plate, 0.3)

				#egg
				time.sleep(0.5)
				head.setAngles(names, angles_sandwich, 0.2)
				time.sleep(1)
				head.setAngles(names, angles_plate, 0.3)

				counter = 0
				while self.loop_lock[0] == True and counter < 1.5:
					time.sleep(0.1)
					counter += 0.1

			#if instruction == 1:
			#	time.sleep(1)
			#elif instruction == 3:
			#	time.sleep(2)
			#else:
			#	time.sleep(1.5)
			#head.setAngles(names, angles_sandwich, 0.2)
			#time.sleep(t)
			#head.setAngles(names, angles_plate, 0.2)


			#if instruction == 2:
			#	counterLim = 3
			#elif instruction == 3:
			#	counterLim = 2
			#else:
			#	counterLim = 0.2

			#if instruction == 3:
			#	counter = 0
			#	while self.loop_lock[0] == True and counter < 1.5:
			#		time.sleep(0.1)
			#		counter += 0.1

			#	head.setAngles(names, angles_sandwich, 0.3)
			#	time.sleep(1)
			#	head.setAngles(names, angles_plate, 0.2)

			#	counter = 0
			#	while self.loop_lock[0] == True and counter < counterLim:
			#		time.sleep(0.1)
			#		counter += 0.1

			#else:
			#	counter = 0
			#	while self.loop_lock[0] == True and counter < counterLim:
			#		time.sleep(0.1)
			#		counter += 0.1

		else:
			angles = [0.20, 0.0]
			time.sleep(1)
			head.setAngles(names, angles, 0.1)

		while self.loop_lock[0] == True:
			time.sleep(0.1)

		self.GazeAt(microinteraction)

	def GazeElse(self, microinteraction):
		while self.loop_lock[0] == True:
			print "Gaze else!"
			time.sleep(1)

	def AddProtocols(self, protocols):    # sets the current priority-protocol
		for prot in protocols:
			self.Protocols.append(prot)
		self.Protocols.sort(key=operator.attrgetter('numMicros'))

	def RemoveProtocols(self):
		self.Protocols = []

	def addBehavior(self, microinteraction, behavior, para=None):
		# add the behavior to the list of currently-active behaviors
		self.lock.acquire()
		self.Behaviors[microinteraction] = behavior
		if behavior == "GAZE_AT":
			self.GAZE_AT[microinteraction] = threading.Thread(target=self.GazeAt, args=(microinteraction, ))
		if behavior == "GAZE_REFERENTIAL":
			self.GAZE_REFERENTIAL[microinteraction] = threading.Thread(target=self.GazeReferential, args=(microinteraction, para ))
		if behavior == "GAZE_COGNITIVE":
			self.GAZE_COGNITIVE[microinteraction] = threading.Thread(target=self.GazeCognitive, args=(microinteraction, ))
		if behavior == "GAZE_INTIMACY":
			self.GAZE_INTIMATE[microinteraction] = threading.Thread(target=self.GazeIntimacy, args=(microinteraction, ))
		if behavior == "GAZE_ELSE":
			self.GAZE_ELSE[microinteraction] = threading.Thread(target=self.GazeElse, args=(microinteraction, ))

		# choose a behavior to run based on the protocol that currently applies
		self.ChooseProcess()
		self.lock.release()

	def killBehavior(self, microinteraction, behavior):
		# IF it still exists, then remove the behavior from the list of currently-active behaviors
		self.lock.acquire()
		if microinteraction in self.Behaviors:
			del self.Behaviors[microinteraction]
			# print the current processes
			for key,value in self.Behaviors.iteritems():
				print "~~~~"
				print key
				print value
				print "~~~~"

			# get the thread, remove it
			threads = self.threadDicts[behavior]
			thread = threads[microinteraction]
			del threads[microinteraction]

			# if the one we want to kill is the one that is currently running, kill it now and wait for it to die
			if self.CurrMicrointeraction == microinteraction:
				print microinteraction
				print "we are trying to kill the process that is currently running"
				self.loop_lock[0] = False
				thread.join()
				self.CurrMicrointeraction = None
				self.CurrBehavior = None

			# reset the loop_lock
			self.loop_lock[0] = True

			# choose a behavior to run based on the protocol that currently applies
			print "attempting to kill gaze"
			self.ChooseProcess()
		self.lock.release()

	def FindBestProcess(self):
		# print the current processes
		print "HERE ARE ALL THE VALUES"
		for key,value in self.Behaviors.copy().iteritems():
			print "~~~~"
			print key
			print value
			print "~~~~"
		print "DONE PRINTING ALL THE VALUES"


		microinteraction = None
		behavior = None

		# is there a protocol that matches up with the current set of behaviors?
		print "CHECKING THE PROTOCOL"
		protocol = None
		for prot in self.Protocols:
			goodProt = True
			for mic, beh in prot.MicrointBehaviorPairs.iteritems():
				print "MICRO: {}, BEH: {}".format(mic,beh)
				if mic not in self.Behaviors or self.Behaviors[mic] != beh:
					print "THIS IS NOT A GOOD PROT"
					goodProt = False

			if goodProt:
				protocol = prot
				break

		print 'Current microinteracton is {}'.format(microinteraction)

		if protocol != None:
			print "SELECTING A PROTOCOL"
			behavior = protocol.ChoiceBehavior
			microinteraction = protocol.ChoiceMicro
		else: # else, just pick the highest ranking behavior!
			print "SELECTING THE BEST POSSIBLE MICRO-BEH"
			for micro, beh in self.Behaviors.iteritems():
				print micro
				if beh == "GAZE_ELSE" and microinteraction == None:
					microinteraction = micro
					behavior = beh
				elif beh == "GAZE_AT" and (behavior == None or behavior == "GAZE_ELSE"):
					microinteraction = micro
					behavior = beh
				if beh == "GAZE_REFERENTIAL" or beh == "GAZE_INTIMACY" or beh == "GAZE_COGNITIVE":
					microinteraction = micro
					behavior = beh
					break

		print 'Chosen microinteracton is {}'.format(microinteraction)
		return microinteraction,behavior

	def ChooseProcess(self):
		# print the current processes
		microinteraction,behavior = self.FindBestProcess()

		# If there is a currently-running behavior
		if self.CurrMicrointeraction != None and self.CurrBehavior != None:
			# if that is not the best behavior anymore, usurp
			if self.CurrMicrointeraction != microinteraction or self.CurrBehavior != behavior:
				# get the thread, remove it
				threads = self.threadDicts[self.CurrBehavior]
				thread = threads[self.CurrMicrointeraction]
				del threads[self.CurrMicrointeraction]
				del self.Behaviors[self.CurrMicrointeraction]

				self.loop_lock[0] = False
				thread.join()

				# reset the loop_lock, begin the next thread
				self.loop_lock[0] = True
				self.CurrMicrointeraction = microinteraction
				self.CurrBehavior = behavior
				thread = self.threadDicts[behavior][microinteraction]
				thread.start()

		# else (we just killed something, because things can't die on their own anymore)
		else:
			# IF some threads exist, run the best
			if microinteraction != None and behavior != None:
				self.loop_lock[0] = True
				self.CurrMicrointeraction = microinteraction
				self.CurrBehavior = behavior
				thread = self.threadDicts[behavior][microinteraction]
				thread.start()


		'''
		# kill the current behavior and start another
		if (self.CurrMicrointeraction != None):
			self.loop_lock[0] = False
			threads = self.threadDicts[self.CurrBehavior]
			if self.CurrMicrointeraction in threads:
				thread = threads[self.CurrMicrointeraction]
				thread.join()
				del threads[self.CurrMicrointeraction]
				print "gaze killed"

		# if there is a new process, start the new process
		if (behavior != None):
			self.loop_lock[0] = True
			threads = self.threadDicts[behavior]
			if microinteraction in threads:
				thread = threads[microinteraction]
				self.CurrMicrointeraction = microinteraction
				self.CurrBehavior = behavior
				if not thread.isAlive():
					thread.start()
			else:
				self.CurrMicrointeraction = None
		'''

	def checkLoopLock(self, timer):
		leave = False

		while timer > 0:
			if self.loop_lock[0] == False:
				leave = True
				break
			timeToSleep = min(timer, 0.5)
			timer -= 0.5
			time.sleep(timeToSleep)

		return leave

	def getNumThreads(self):
		counter = 0
		for key1,val1 in self.threadDicts:
			for key2,val2 in val1:
				counter += 1
		return counter
