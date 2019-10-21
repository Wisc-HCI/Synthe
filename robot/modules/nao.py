import threading
import thread
import time
import random
import signal
import sys
import numpy as np

sys.path.append("./modules/")
from gaze import Gaze
from gesture import Gesture
sys.path.append("pynaoqi-python2.7-2.1.4.13-linux64")
#sys.path.append("pynaoqi-python2.7-2.1.4.13-mac64")
import naoqi
from naoqi import ALModule
from naoqi import ALBroker
from naoqi import ALProxy

def init_broker(IP, PORT):
    """
    Starts the naoqi broker.
    Must be called prior to using any naoqi capabilies.
    """
    return ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       IP,         # parent broker IP
       PORT)       # parent broker port


class NaoMotion(ALModule):
    """
    This class serves to enable controlling the motion of the nao robot.
    """

    IP = '10.130.229.217'
    PORT = 9559

    def __init__(self, name, design, ip = '10.130.229.217', port = 9559):
        """
        :param name: string name for this ALModule
        :param design: string design for this ALModule
        :param ip: string representation of the IP the nao is located at.
        :param port: int port the nao is recieving input on.

        :pre: global method init_broker has been called
        """
        self.name = name
        self.IP = ip
        self.port = port
        ALModule.__init__(self, self.name)
        #self.gaze = Gaze(design)
        #self.gesture = Gesture(design)

        self.larm_lock = threading.Lock()
        self.rarm_lock = threading.Lock()
        self.lhand_lock = threading.Lock()
        self.rhand_lock = threading.Lock()
        self.head_lock = threading.Lock()
        self.lock_gaze = False
        self.end_gaze = False
        self.end_gesture = False
        autoMove = ALProxy("ALAutonomousMoves", self.IP, port)
        autoMove.setExpressiveListeningEnabled(False)

    def getName(self):
        return self.name

    def intimacyModulating(self):
        """Extends the nao's right arm"""
        thread.start_new_thread(self.__intimacy_mod, ())

    def __intimacy_mod(self):
        head_intimacy = ALProxy("ALMotion", self.IP, self.PORT)
        angle_list = [0.1396, -0.1396]
        head_intimacy.setStiffnesses("Head", 1.0)
        while True:
            head_intimacy.setAngles("HeadYaw", random.choice(angle_list), 0.1)
            time_length = np.random.normal(1.96, 0.32)
            time.sleep(time_length)

            # check every 0.5 seconds if the loop_lock still holds
            if self.end_gaze:
                break

            while self.lock_gaze:
                pass

            names = ["HeadPitch", "HeadYaw"]
            angles = [0, 0]
            head_intimacy.setAngles(names, angles, 0.05)
            time_between = np.random.normal(4.75, 1.39)
            time.sleep(time_between)

            # check every 0.5 seconds if the loop_lock still holds
            if self.end_gaze:
                break
        head_intimacy.setStiffnesses("Head", 0.0)
        self.end_gaze = False

    def endIntimacyMod(self):
        self.end_gaze = True

    def faceDetection(self):
        faceDet = ALProxy("ALFaceDetection", self.IP, self.PORT)
        period = 500

        # update the subscribed list
        subscribedTo[faceDet] = "faceID"
        faceDet.subscribe("faceID", period, 0.0)

        faceMem = ALProxy("ALMemory", self.IP, self.PORT)
        val = faceMem.getData("FaceDetected")
        print(val)

        # remove from subscribed list
        faceDet.unsubscribe("faceID")
        del subscribedTo[faceDet]

        if (val and isinstance(val, list) and len(val) == 2):
            return True
        return False

    def faceTracker(self, faceSize):
        tracker = ALProxy("ALTracker", self.IP, self.PORT)
        targetName = "Face"
        tracker.registerTarget(targetName, faceSize)
        tracker.track(targetName)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Interrupted by user")
        tracker.stopTracker()
        tracker.unregisterAllTargets()

    def centerHead(self):
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        #exr.setStiffnesses("Head", 1.0)
        names = ["HeadYaw"]
        angles = [0]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1)
        self.lock_gaze = False
        #exr.setStiffnesses("Head", 0)

    def openLefthand(self):
        """opens the nao's left hand"""

        self.lhand_lock.acquire()
        openl = ALProxy("ALMotion", self.IP, self.PORT)
        openl.openHand('LHand')
        #time.sleep(2)
        self.lhand_lock.release()

    def openRighthand(self):
        """opens the nao's right hand"""

        self.rhand_lock.acquire()
        openr = ALProxy("ALMotion", self.IP, self.PORT)
        openr.openHand('RHand')
        time.sleep(1)
        self.rhand_lock.release()

    def closeLefthand(self):
        """closes the nao's left hand"""

        self.lhand_lock.acquire()
        closel = ALProxy("ALMotion", self.IP, self.PORT)
        closel.closeHand('LHand')
        self.lhand_lock.release()

    def closeRighthand(self):
        """closes the nao's right hand"""

        self.rhand_lock.acquire()
        closer = ALProxy("ALMotion", self.IP, self.PORT)
        closer.closeHand('RHand')
        time.sleep(1)
        self.rhand_lock.release()

    def leftarmExtended(self):
        """Extends the nao's left arm"""
        thread.start_new_thread(self.__extend_left, ())

    def __extend_left(self):
        """Extends the nao's left arm"""
        self.larm_lock.acquire()
        exl = ALProxy("ALMotion", self.IP, self.PORT)
        exl.setStiffnesses("LArm", 1.0)
        names = ["LShoulderPitch", "LWristYaw", "LShoulderRoll", "LElbowRoll", "LElbowYaw"]
        angles = [0.3, -1.3, 0, -0.5, -2.0]
        fractionMaxSpeed = 0.2
        exl.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(3)
        self.larm_lock.release()

    def rightarmExtended(self):
        """Extends the nao's right arm"""
        thread.start_new_thread(self.__extend_right, ())

    def __extend_right(self):
        """Extends the nao's right arm"""
        self.rarm_lock.acquire()
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("RArm", 1.0)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw"]
        angles = [0.3, 1.3, 0, 0.5, 2.0]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.5)
        self.rarm_lock.release()

    def leftarmRetracted(self):
        """Retracts the nao's left arm"""
        thread.start_new_thread(self.__retract_left, ())

    def __retract_left(self):
        """Retracts the nao's left arm"""
        self.larm_lock.acquire()
        rel = ALProxy("ALMotion", self.IP, self.PORT)
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw", "LHand"]
        angles = [1.4495880603790283, 0.10426998138427734, -0.9924559593200684, -0.8345379829406738,
                  -1.5938677787780762, 0.6855999827384949]
        rel.setAngles(names, angles, 0.2)
        time.sleep(4)
        self.larm_lock.release()

    def rightarmRetracted(self):
        """Retracts the nao's right arm"""
        thread.start_new_thread(self.__retract_right, ())

    def __retract_right(self):
        """Retracts the nao's right arm"""
        self.rarm_lock.acquire()
        rer = ALProxy("ALMotion", self.IP, self.PORT)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"]
        angles = [1.1495880603790283, -0.10426998138427734, -0.25, 1.1345379829406738, -0.00378778, 1.8]
        rer.setAngles(names, angles, 0.2)
        time.sleep(4)
        self.rarm_lock.release()

    def waved(self):
        """Makes the nao point left"""
        thread.start_new_thread(self.__wave, ())

    def __wave(self):
        self.lock_gaze = True
        self.rarm_lock.acquire()

        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("RArm", 1.0)
        #exr.setStiffnesses("Head", 1.0)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "HeadYaw", "RHand"]
        angles = [-1.1, -.4, -0.47, 1.35, 0.0, -0.2, 1.8]
        fractionMaxSpeed = 0.3
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(0.5)

        angles = [-1.1, -.4, -0.97, 0.35, 0.0, -0.2, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(0.5)

        angles = [-1.1, -.4, -0.47, 1.35, 0.0, -0.2, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(0.5)

        angles = [-1.1, -.4, -0.97, 0.35, 0.0, -0.2, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(0.5)

        angles = [-1.1, -.4, -0.47, 1.35, 0.0, -0.2, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(0.5)

        angles = [1.1495880603790283, -0.10426998138427734, -0.25, 1.1345379829406738, -0.00378778,
                      -0.6855999827384949, 1.8]
        exr.setAngles(names, angles, 0.2)
        time.sleep(2)

        self.rarm_lock.release()
        self.centerHead()
        self.end_gesture = False

    def beatGestured(self):
        """Makes the nao point left"""
        thread.start_new_thread(self.__beat_gestured, ())

    def __beat_gestured(self):
        self.lock_gaze = True
        self.larm_lock.acquire()
        self.rarm_lock.acquire()
        arm = ALProxy("ALMotion", self.IP, self.PORT)
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

        while True:
            # randomly set a wait time
            t = np.random.lognormal(0,0.5)
            if self.end_gesture:
                break
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

            if self.end_gesture:
                break

        if whichArm == 1:
            arm.setAngles(rnames, rsit_angles, 0.2)
        else:
            arm.setAngles(lnames, lsit_angles, 0.2)
        time.sleep(1)
        self.larm_lock.release()
        self.rarm_lock.release()
        self.centerHead()
        self.end_gesture = False

    def endGesture(self):
        self.end_gesture = True

    def pointedLeft(self):
        """Makes the nao point left"""
        thread.start_new_thread(self.__point_left, ())

    def __point_left(self):
        """makes the nao point to the left"""
        self.lock_gaze = True
        self.larm_lock.acquire()
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("LArm", 1.0)
        #exr.setStiffnesses("Head", 1.0)
        names = ["LShoulderPitch", "LWristYaw", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "HeadYaw", "LHand"]
        angles = [0, 0.4, 0.6, -0.05, -1.5, 0.5, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.5)
        #exr.setStiffnesses("Head", 0)
        self.larm_lock.release()
        self.centerHead()

    def pointedRight(self):
        """Makes the nao point left"""
        thread.start_new_thread(self.__point_right, ())

    def __point_right(self):
        """makes the nao point to the left"""
        self.lock_gaze = True
        self.rarm_lock.acquire()
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("RArm", 1.0)
        #exr.setStiffnesses("Head", 1.0)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "HeadYaw", "RHand"]
        angles = [0, -.4, -0.76, 0.05, 1.5, -1, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.5)
        #exr.setStiffnesses("Head", 0)
        self.rarm_lock.release()
        self.centerHead()


    def pointed(self):
        """Makes the nao point left"""
        thread.start_new_thread(self.__point_center, ())

    def __point_center(self):
        """makes the nao point to the left"""
        self.lock_gaze = True
        self.rarm_lock.acquire()
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("RArm", 1.0)
        #exr.setStiffnesses("Head", 1.0)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "HeadYaw", "RHand"]
        angles = [0, -.4, -0.2, 0.05, 1.5, -0.2, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.5)
        #exr.setStiffnesses("Head", 0)
        self.rarm_lock.release()
        self.centerHead()
        self.end_gesture = False

    def presented(self):
        """makes the nao look like it's presenting something"""
        thread.start_new_thread(self.__present, ())

    def __present(self):
        """makes the nao look like it's presenting something"""
        self.lock_gaze = True
        self.rarm_lock.acquire()
        exr = ALProxy("ALMotion", self.IP, self.PORT)
        exr.setStiffnesses("RArm", 1.0)
        #exr.setStiffnesses("Head", 1.0)
        names = ["RShoulderPitch", "RWristYaw", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "HeadYaw", "RHand"]
        angles = [0.41, 1.39, 0.31, 0.03, 1.43, 0.27, 1.8]
        fractionMaxSpeed = 0.2
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.0)
        angles = [0.41, 1.39, -0.34, 0.03, 1.43, -.05, 0]
        fractionMaxSpeed = 0.1
        exr.setAngles(names, angles, fractionMaxSpeed)
        time.sleep(1.5)
        #exr.setStiffnesses("Head", 0)
        self.rarm_lock.release()
        self.centerHead()
        self.end_gesture = False

    def wait_until_still(self):
        """block until the nao is done moving its limbs"""

        self.lhand_lock.acquire()
        self.rhand_lock.acquire()
        self.larm_lock.acquire()
        self.rarm_lock.acquire()
        self.lhand_lock.release()
        self.rhand_lock.release()
        self.larm_lock.release()
        self.rarm_lock.release()

    def prepare_experiment(self):
        """
        Puts the nao into a resting position.
        Should be called prior to using any other NaoMotion capabilites
        """
        self.wait_until_still()
        postureProxy = ALProxy("ALRobotPosture", self.IP, self.PORT)
        motionProxy = ALProxy("ALMotion", self.IP, self.PORT)
        postureProxy.goToPosture("Sit", 1.0)
        motionProxy.rest()
        self.wait_until_still()

    def final_pose(self):
        """
        moves the nao into a default resting position. Should be called
        whenever NaoMotion is no longer being used.
        """
        self.wait_until_still()
        postureProxy = ALProxy("ALRobotPosture", self.IP, self.PORT)
        motionProxy = ALProxy("ALMotion", self.IP, self.PORT)
        postureProxy.goToPosture("Sit", 1.0)
        motionProxy.rest()
        self.wait_until_still()

    def sittingPosition(self):
        try:
            postureProxy = ALProxy("ALRobotPosture", self.IP, 9559)
            motionProxy = ALProxy("ALMotion", self.IP, 9559)
        except Exception, e:
            print "Could not create proxy to ALRobotPosture"
            print "Error was: ", e

        postureProxy.goToPosture("Sit", 1.0)
        motionProxy.rest()


class NaoSpeech(ALModule):

    """
    NaoSpeech serves as a wrapper class for abstracted calls to naoqi's
    text-to-speech capabilities
    """

    def __init__(self, name, ip = '10.130.229.217', port = 9559):
        """
        :param name: string name for this ALModule
        :param design: string design for this ALModule
        :param ip: string representation of the IP the nao is located at.
        :param port: int port the nao is recieving input on.

        :pre: global method init_broker has been called
        """
        self.name = name
        self.speech_token = threading.Lock()
        self.ip = ip
        self.port = port
        ALModule.__init__(self, self.name)
        self.tts = ALProxy('ALTextToSpeech', self.ip, self.port)

    def speak(self, text):
        """
        :param text: type string: the text to be spoken by the nao unit

        :post: the nao unit at IP and PORT has said text
        """
        self.tts.say(text)

class NaoEyes(ALModule):

    """
    NaoSpeech serves as a wrapper class for abstracted calls to naoqi's
    text-to-speech capabilities
    """

    def __init__(self, name, ip = '10.130.229.217', port = 9559):
        """
        :param name: string name for this ALModule
        :param design: string design for this ALModule
        :param ip: string representation of the IP the nao is located at.
        :param port: int port the nao is recieving input on.

        :pre: global method init_broker has been called
        """
        self.name = name
        self.ip = ip
        self.port = port
        ALModule.__init__(self, self.name)
        self.tts = ALProxy('ALLeds', self.ip, self.port)

        self.leftnames = ["Face/Led/Green/Left/0Deg/Actuator/Value",
                          "Face/Led/Green/Left/90Deg/Actuator/Value",
                          "Face/Led/Green/Left/180Deg/Actuator/Value",
                          "Face/Led/Green/Left/270Deg/Actuator/Value"]
        self.tts.createGroup("left_eyes", self.leftnames)

        self.rightnames = ["Face/Led/Green/Right/0Deg/Actuator/Value",
                          "Face/Led/Green/Right/90Deg/Actuator/Value",
                          "Face/Led/Green/Right/180Deg/Actuator/Value",
                          "Face/Led/Green/Right/270Deg/Actuator/Value"]
        self.tts.createGroup("right_eyes", self.rightnames)

    def hear(self):
        """
        :param text: type string: the text to be spoken by the nao unit

        :post: the nao unit at IP and PORT has said text
        """
        self.tts.off("FaceLeds")
        self.tts.on("right_eyes")
        self.tts.on("left_eyes")

    def end_hear(self):
        self.tts.off("right_eyes")
        self.tts.off("left_eyes")
        self.tts.on("FaceLeds")
