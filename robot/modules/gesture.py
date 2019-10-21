import sys
sys.path.append("pynaoqi-python2.7-2.1.4.13-linux64")
#sys.path.append("pynaoqi-python2.7-2.1.4.13-mac64")
import operator
import threading
from threading import Lock
import time
from naoqi import ALProxy
from Protocol import Protocol
import numpy as np

IP = "10.130.229.213"
PORT = 9559


class Gesture():
    def __init__(self, design):
        self.design = design
        self.Behaviors = {}  # all microinteractions and their current behaviors
        self.Protocols = []  # unchanging list of protocols for the group
        self.CurrMicrointeraction = None  # the currently running microinteraction
        self.CurrBehavior = None  # the currently running behavior

        # the active or queued threads
        # just as it is possible to have multiple different gaze behaviors competing
        #     for each other, it is possible for multiple different microinteractions
        #     to be undergoing the same gaze behavior
        self.GESTURE_NONE = {}
        self.GESTURE_DIECTIC = {}
        self.GESTURE_BEAT = {}
        self.GESTURE_SIGNAL = {}
        self.threadDicts = {"GESTURE_NONE": self.GESTURE_NONE,
                            "GESTURE_DIECTIC": self.GESTURE_DIECTIC,
                            "GESTURE_BEAT": self.GESTURE_BEAT,
                            "GESTURE_SIGNAL": self.GESTURE_SIGNAL}

        # self.loop_lock
        self.loop_lock = [True]
        self.lock = Lock()

    def GestureNone(self, microinteraction):
        print "Gesture none!"
        motion = ALProxy("ALMotion", IP, PORT)
        posture = ALProxy("ALRobotPosture", IP, PORT)
        posture.post.goToPosture("Sit", 0.5)
        #motion.rest()
        time.sleep(3)

    def GestureSignal(self, microinteraction):
        while self.loop_lock[0] == True:
            time.sleep(0.1)
        #print "Gesture none!"
        #arm = ALProxy("ALMotion", IP, PORT)
        #arm.setStiffnesses("Body", 1.0)
        #names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand"]
        #angles = [0.20944, -0.0645772, .9442231, 1.50098, -0.6108652, 1.129228]
        #sit_angles = [0.9738937, -0.2645772, 1.2342231, 0.460098, 0.006108652, -1.129228]

        #while self.loop_lock[0] == True:

        #    counter = 0
        #    while counter < 5 and self.loop_lock[0] == True:
        #        counter += 0.1
        #        time.sleep(0.1)

        #    arm.setAngles(names, angles, 0.2)
        #    time.sleep(2)
        #    arm.setAngles(names, sit_angles, 0.2)
        #    time.sleep(2)

        #    self.GestureNone(microinteraction)

    def GestureDiectic(self, microinteraction, para):
        print "Gesture diectic!"

        arm = ALProxy("ALMotion", IP, PORT)
        arm.setStiffnesses("Body", 1.0)
        names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand"]
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
        #angles_sandwich = [0.7532360553741455, -0.4786500930786133, 0.31604599952697754, 0.7899680137634277, -0.6059720516204834, 0.7455999851226807]
        angles_sandwich = [0.5532360553741455, -0.4786500930786133, 0.31604599952697754, 0.7899680137634277,
                           -0.6059720516204834, 0.7455999851226807]
        #angles_plate = [0.7823820114135742, 0.3141592741012573, 0.5154659748077393, 0.6749181747436523, -0.7470998764038086, 0.806399941444397]
        angles_plate = [0.5823820114135742, 0.1141592741012573, 0.7154659748077393, 0.6749181747436523,
                        -0.7470998764038086, 0.806399941444397]

        angles_halfway = [0.5823820114135742, -0.2141592741012573, 0.7154659748077393, 0.6749181747436523,
                        -0.7470998764038086, 0.806399941444397]

        angles_plate_up = [0.5823820114135742, 0.1141592741012573, 0.9154659748077393, 0.6749181747436523,
                        -0.7470998764038086, 0.806399941444397]

        if "Pick up a piece of bread" in para.strip():
            if self.design == "Instruction-Action-1":
                time.sleep(0.1)
                arm.setAngles(names, angles_sandwich, 0.2)
                time.sleep(1.5)
                arm.setAngles(names, angles_plate, 0.3)

                time.sleep(2)
                arm.setAngles(names, angles_sandwich, 0.2)
                time.sleep(2)
                arm.setAngles(names, angles_plate, 0.3)

                time.sleep(1)

                rsit_angles = [0.9738937, -0.2645772, 1.2342231, 0.460098, 0.006108652, -1.129228]
                arm.setAngles(names, rsit_angles, 0.1)

                time.sleep(3.8)
                arm.setAngles(names, angles_sandwich, 0.2)
                #time.sleep(0.8)
                #arm.setAngles(names, angles_plate, 0.3)

                counter = 0
                while self.loop_lock[0] == True and counter < 1.5:
                    time.sleep(0.1)
                    counter += 0.1

                arm.setAngles(names, angles_sandwich, 0.3)
                time.sleep(1)
                arm.setAngles(names, angles_plate, 0.3)
            elif self.design == "Instruction-Action-2":
                time.sleep(0.1)
                arm.setAngles(names, angles_sandwich, 0.2)
                time.sleep(1.5)
                arm.setAngles(names, angles_plate, 0.3)

                # and then pick up a piece of bacon
                time.sleep(1.5)
                arm.setAngles(names, angles_sandwich, 0.3)
                time.sleep(1)
                arm.setAngles(names, angles_plate, 0.3)

                time.sleep(1.5)
                arm.setAngles(names, angles_plate_up, 0.3)
                time.sleep(1.5)
                arm.setAngles(names, angles_plate, 0.3)

                #egg
                time.sleep(1.5)
                arm.setAngles(names, angles_plate_up, 0.3)
                time.sleep(1.5)
                arm.setAngles(names, angles_plate, 0.3)

                #egg
                time.sleep(1.5)
                arm.setAngles(names, angles_sandwich, 0.3)
                time.sleep(1)
                arm.setAngles(names, angles_plate, 0.3)

                #time.sleep(1)

                #rsit_angles = [0.9738937, -0.2645772, 1.2342231, 0.460098, 0.006108652, -1.129228]
                #arm.setAngles(names, rsit_angles, 0.1)

                #time.sleep(6.8)
                #arm.setAngles(names, angles_sandwich, 0.2)
                #time.sleep(0.8)
                #arm.setAngles(names, angles_plate, 0.3)

                counter = 0
                while self.loop_lock[0] == True and counter < 1.5:
                    time.sleep(0.1)
                    counter += 0.1

                #arm.setAngles(names, angles_sandwich, 0.3)
                #time.sleep(1)
                #arm.setAngles(names, angles_plate, 0.3)
            else:
                time.sleep(0.1)
                arm.setAngles(names, angles_sandwich, 0.2)
                time.sleep(1.5)
                arm.setAngles(names, angles_plate, 0.3)

                # and add some mayonnaise
                time.sleep(1.5)
                arm.setAngles(names, angles_sandwich, 0.3)
                time.sleep(1)
                arm.setAngles(names, angles_halfway, 0.1)

                # cucumbers
                time.sleep(1)
                arm.setAngles(names, angles_sandwich, 0.2)
                time.sleep(0.5)
                arm.setAngles(names, angles_plate, 0.3)

                time.sleep(1.5)
                arm.setAngles(names, angles_plate_up, 0.3)
                time.sleep(1.0)
                arm.setAngles(names, angles_plate, 0.3)

                #egg
                time.sleep(2.5)
                arm.setAngles(names, angles_plate_up, 0.3)
                time.sleep(0.5)
                arm.setAngles(names, angles_plate, 0.3)

                #egg
                time.sleep(0.5)
                arm.setAngles(names, angles_sandwich, 0.3)
                time.sleep(1)
                arm.setAngles(names, angles_plate, 0.3)

                counter = 0
                while self.loop_lock[0] == True and counter < 1.5:
                    time.sleep(0.1)
                    counter += 0.1

        if "There should be a power cord" in para.strip():
            time.sleep(0.8)
            arm.setAngles(names, angles_halfway, 0.2)
            time.sleep(3.5)
            rsit_angles = [0.9738937, -0.2645772, 1.2342231, 0.460098, 0.006108652, -1.129228]
            arm.setAngles(names, rsit_angles, 0.2)
        #if instruction == 1:
        #    time.sleep(1)
        #elif instruction == 3:
        #    time.sleep(2)
        #else:
        #    time.sleep(1.5)
        #arm.setAngles(names, angles_sandwich, 0.2)
        #time.sleep(t)
        #arm.setAngles(names, angles_plate, 0.3)

        #if instruction == 3:
        #    counter = 0
        #    while self.loop_lock[0] == True and counter < 1.5:
        #        time.sleep(0.1)
        #        counter += 0.1

        #    arm.setAngles(names, angles_sandwich, 0.3)
        #    time.sleep(1)
        #    arm.setAngles(names, angles_plate, 0.3)

        counter = 0
        while self.loop_lock[0] == True:
            time.sleep(0.1)
            counter += 0.1
            if instruction == 3 and counter > 1:
                break

    def GestureBeat(self, microinteraction):
        print "Gesture beat"
        arm = ALProxy("ALMotion", IP, PORT)
        arm.setStiffnesses("Body", 1.0)

        rnames = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand"]
        lnames = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw", "LHand"]
        rstart = [0.6387905, -0.162316, 0.9180432, 0.3874631,
                        0.51169371, 1.20]
        lstart = [0.6702064, 0.0366519, -1.019272, -0.4415683,
                        -0.5802851, 1.20]
        rsit_angles = [0.9738937, -0.2645772, 1.2342231, 0.460098, 0.006108652, -1.129228]
        lsit_angles = [0.9040806, 0.2007129, -1.199041, -0.4485496, -0.00698132, -1.129228]

        whichArm = np.random.randint(2)

        if whichArm == 1:
            arm.setAngles(rnames, rstart, 0.2)
        else:
            arm.setAngles(lnames, lstart, 0.2)

        while self.loop_lock[0] == True:
            # randomly set a wait time
            t = np.random.lognormal(0,0.5)
            time.sleep(t)

            # amounts to update the angles
            rstart[0] += np.random.normal(0,1) * 0.05;
            rstart[1] += np.random.normal(0,1) * 0.05;
            rstart[2] += np.random.normal(0,1) * 0.05;
            rstart[3] += np.random.normal(0,1) * 0.05;
            rstart[4] += np.random.normal(0,1) * 0.05;

            lstart[0] += np.random.normal(0,1) * 0.05;
            lstart[1] += np.random.normal(0,1) * 0.05;
            lstart[2] += np.random.normal(0,1) * 0.05;
            lstart[3] += np.random.normal(0,1) * 0.05;
            lstart[4] += np.random.normal(0,1) * 0.05;

            if rstart[0] > .90:
                rstart[0] = 0.90
            if lstart[0] > .90:
                lstart[0] = 0.90

            if whichArm == 1:
                arm.setAngles(rnames, rstart, 0.03)
            else:
                arm.setAngles(lnames, lstart, 0.03)

        if whichArm == 1:
            arm.setAngles(rnames, rsit_angles, 0.2)
        else:
            arm.setAngles(lnames, lsit_angles, 0.2)
        time.sleep(1)
        #self.GestureNone(microinteraction)
        #arm.setStiffnesses("Body", 0.0)
        #time.sleep(4)


    def AddProtocols(self, protocols):  # sets the current priority-protocol
        for prot in protocols:
            self.Protocols.append(prot)
        self.Protocols.sort(key=operator.attrgetter('numMicros'))

    def RemoveProtocols(self):
        self.Protocols = []

    def addBehavior(self, microinteraction, behavior, para=None):
        # add the behavior to the list of currently-active behaviors
        self.lock.acquire()
        self.Behaviors[microinteraction] = behavior
        if behavior == "GESTURE_NONE":
            self.GESTURE_NONE[microinteraction] = threading.Thread(target=self.GestureNone, args=(microinteraction,))
        if behavior == "GESTURE_DIECTIC":
            self.GESTURE_DIECTIC[microinteraction] = threading.Thread(target=self.GestureDiectic,
                                                                       args=(microinteraction, para))
        if behavior == "GESTURE_BEAT":
            self.GESTURE_BEAT[microinteraction] = threading.Thread(target=self.GestureBeat,
                                                                        args=(microinteraction,))
        if behavior == "GESTURE_SIGNAL":
            self.GESTURE_SIGNAL[microinteraction] = threading.Thread(target=self.GestureSignal,
                                                                        args=(microinteraction,))
        # choose a behavior to run based on the protocol that currently applies
        self.ChooseProcess()
        self.lock.release()

    def killBehavior(self, microinteraction, behavior):
        # remove the behavior from the list of currently-active behaviors
        self.lock.acquire()
        if microinteraction in self.Behaviors:
            del self.Behaviors[microinteraction]
            # print the current processes
            for key, value in self.Behaviors.iteritems():
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
                self.loop_lock[0] = False
                thread.join()
                self.CurrMicrointeraction = None
                self.CurrBehavior = None

            # reset the loop_lock
            self.loop_lock[0] = True

            # choose a behavior to run based on the protocol that currently applies
            print "Attempting to kill gesture..."
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
                print mic
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
                if beh == "GESTURE_SIGNAL":
                    microinteraction = micro
                    behavior = beh
                    break
                elif beh == "GESTURE_DIECTIC" or beh == "GESTURE_BEAT":
                    microinteraction = micro
                    behavior = beh
                elif beh == "GESTURE_NONE":
                    microinteraction = micro
                    behavior = beh

        print 'Chosen microinteracton is {}'.format(microinteraction)
        return microinteraction,behavior

    def ChooseProcess(self):

        try:
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
        except:
            return
