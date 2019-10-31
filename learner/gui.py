import sys
import os
import json
from PyQt5.QtCore import QSize, QRect, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFrame, QScrollArea, QSlider, QComboBox, QGroupBox, QProgressBar, QPushButton, QListWidget, QListWidgetItem, QMainWindow, QAction, QSpinBox, QCheckBox
from PyQt5.QtGui import QImage, QPalette, QBrush, QIcon, QPixmap, QPainter, QColor, QFont
import traceback
import imp
from bodystorming_simulation import *
from sat_solver import *
from controller import *
from webviewer import *
from bodystorm_history import *
from connection_label import *
from simulate_record_buttons import *
from examples_pane import *
from vis_buttons import *
from filemanager import *
from slider import *
from robot_chooser import *
from solution_database import *
from robot_controller import *
from armband_controller import *
from status_pane import *
from new_design_dialog import *
from audio_input_pane import *
from microphone_controller import *
import numpy as np
import time
import random
import pickle
import _thread
import argparse
import difflib

class App(QMainWindow):

    '''
    Run the gui
    '''

    # communicate from parent to child thread
    terminate = QtCore.pyqtSignal()
    resized = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.title = 'Synthé'
        self.left = 10
        self.top = 10
        desktop = QApplication.desktop()
        screen_resolution = desktop.screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()
        #self.width, self.height = 1000, 750

        self.bodystorm = None
        self.solution = None
        self.solution_db = SolutionDatabase()

        self.bodystorm_listener = None

        # participants
        self.p1_is_robot = True

        # wait for already-running threads
        self.thread_wait = False

        # thread counter
        self.threadcount = 0

        # see if we need to be in debug mode or not
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--debug", help="run Synthé in debug mode",
                        action="store_true")
        parser.add_argument("-r", "--userobot", default=0, help="run Synthé with the Nao robot",
                        action="store")
        parser.add_argument("-c", "--cwd", default="", help="the current working directory",
                        action="store")
        args = parser.parse_args()
        self.userobot = args.userobot
        self.debug = args.debug
        self.cwd = args.cwd
        if self.cwd == "":
            print("ERROR: must provide a working directory to run Synthé")
            exit(1)

        self.initialized = False
        self.initUI()
        self.initialized = True

    def initUI(self):
        print("GUI >> starting design process at {}".format(time.time()))

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # the graph window
        self.label = QLabel(self)
        self.label.setFrameShape(QFrame.Box)
        self.label.setGeometry(self.left-5, self.top-5, self.width - 410, self.height - 105)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet('background-color: white')
        self.traceView = ExampleDrawerContainer(parent=self.label)
        self.traceView.setGeometry(self.left-10, self.top-10, self.width - 410, self.height - 105)
        self.webView = WebViewer(self, self.label, self.cwd)
        self.webView.setGeometry(self.left-10, self.top-10, self.width - 410, self.height - 105)
        self.statusView = StatusPane(self.label)
        self.statusView.remove_status("all")

        # necessary for not loading in old graphs
        self.font_size = 12
        self.nonverbal_behaviors = False
        #self.webView.make_blank_graphs()

        # the properties window
        self.plotlabel1 = QLabel(self)
        self.plotlabel1.setFrameShape(QFrame.Box)
        self.plotlabel1.setGeometry(self.left+(self.width - 410), self.top - 5, 395, self.height - 105)

        self.bodystorm_history = BodystormHistory("Demonstrations", parent=self.plotlabel1, frame=self)

        # simulate and record button
        self.robot_connector = RobotController(self,userobot=self.userobot)
        self.simulate_button = SimulateButton('Simulate', self.plotlabel1, self, self.robot_connector)
        self.simulate_button.clicked.connect(self.simulate)
        self.button = RecordButton('Record', self.plotlabel1, self)

        self.armband_connector = ArmbandController(self)

        # whether we want to link to the audio recorder or not
        if not self.debug:
            self.button.clicked.connect(self.record)
        else:
            self.button.clicked.connect(self.command_line_record)
        self.button.setCheckable(True)

        # mechanism to connect to clients
        self.connector = ConnectionLabel(self.bodystorm_history, self)

        # mechanism to control microphones
        self.bodystorm_listener = MicrophoneController(self)

        # mechanism for keeping track of which microphones are active
        self.participants_to_devices = {}
        self.participant_names = []

        # menu bar
        self.mainMenu = self.menuBar()
        fileMenu = self.mainMenu.addMenu('File')
        resetButton = QAction('New Design', self)
        resetButton.triggered.connect(self.reset_improv)
        saveButton = QAction('Save Traces', self)
        saveButton.triggered.connect(self.save_traces)
        loadButton = QAction('Load Traces', self)
        loadButton.triggered.connect(self.load_traces)
        fileMenu.addAction(resetButton)
        fileMenu.addAction(saveButton)
        fileMenu.addAction(loadButton)
        connect_menu = self.mainMenu.addMenu('Devices')
        connectButton = QAction('Choose Audio Inputs', self)
        connectButton.triggered.connect(self.open_audio_pref)
        connect_menu.addAction(connectButton)
        if found_myo:
            connectArmbandButton = QAction('Connect Armband', self)
            connectArmbandButton.triggered.connect(self.armband_connector.onclick)
            calibrate_armband_button = QAction('Calibrate Armband', self)
            calibrate_armband_button.triggered.connect(self.armband_connector.calibrate)
            connect_menu.addAction(connectArmbandButton)
            connect_menu.addAction(calibrate_armband_button)
        if self.userobot==1:
            connectRobotButton = QAction('Connect Robot', self)
            connectRobotButton.triggered.connect(self.robot_connector.on_click)
            connect_menu.addAction(connectRobotButton)

        self.parameters_group = QGroupBox("Parameters", parent=self.plotlabel1)
        self.parameters_group.setGeometry(10, self.plotlabel1.height() - 270 - 110 - 10, self.plotlabel1.width() - 20, 100)

        self.visualization_group = QGroupBox("View Options", parent=self.plotlabel1)
        self.visualization_group.setGeometry(10, self.plotlabel1.height() - 160 - 110 - 10, self.plotlabel1.width() - 20, 170)

        self.vis_buttons = VisButtons(self.visualization_group, self)
        self.slider = StateSizeChooser(self.parameters_group, self)

        self.font_selector_label = QLabel("Font Size", self.visualization_group)
        self.font_selector_label.move(10, 120)
        self.font_selector_label.setFont(QFont("Veranda", 10))
        self.font_selector = QSpinBox(self.visualization_group)
        self.font_selector.setGeometry(60, 113, 50, 25)
        self.font_selector.setMinimum(6)
        self.font_selector.setMaximum(24)
        self.font_selector.setValue(self.font_size)
        self.font_selector.valueChanged.connect(self.change_font_size)

        self.checkbox_label = QLabel("Display nonverbal behaviors", self.visualization_group)
        self.checkbox_label.move(10, 145)
        self.checkbox_label.setFont(QFont("Veranda", 10))
        self.checkbox = QCheckBox(self.visualization_group)
        self.checkbox.setGeometry(150, 140, 50, 25)
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.change_nonverbal_behavior_display)

        self.progress_group = QGroupBox("", parent=self.plotlabel1)
        self.progress_group.setGeometry(10, self.plotlabel1.height() - 100, self.plotlabel1.width() - 20, 90)

        self.progress_description = QLabel("", self.progress_group)
        self.progress_description.setGeometry(40, 30, 200,30)
        self.progress_label = QLabel("0%", self.progress_group)
        self.progress_label.setGeometry(self.progress_group.width() - 60, 40, 30, 10)
        self.progress_bar = QProgressBar(self.progress_group)
        self.progress_bar.setGeometry(40, 40, self.progress_group.width() - 80, 40)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.progress_label.hide()
        self.progress_description.hide()

        #print("done initializing")
        # call backend
        self.threads = []
        #self.set_up_server()
        #print("done with initial update")

        self.resized.connect(self.resizeWindow)

        self.show()

    def resizeEvent(self, event):
        self.resized.emit()
        return super(App, self).resizeEvent(event)

    def resizeWindow(self):
        if self.initialized:
            self.width = self.frameGeometry().width()
            self.height = self.frameGeometry().height()
            self.label.setGeometry(self.left-5, self.top-5, self.width - 410, self.height - 40)
            self.webView.setGeometry(self.left-10, self.top-10, self.width - 410, self.height - 40)
            self.plotlabel1.setGeometry(self.left+(self.width - 410), self.top - 5, 395, self.height - 40)
            self.parameters_group.setGeometry(10, self.plotlabel1.height() - 270 - 110 - 10, self.plotlabel1.width() - 20, 100)
            self.visualization_group.setGeometry(10, self.plotlabel1.height() - 160 - 110 - 10, self.plotlabel1.width() - 20, 170)
            self.font_selector_label.move(10, 120)
            self.font_selector.setGeometry(60, 113, 50, 25)
            self.checkbox_label.move(10, 145)
            self.checkbox.setGeometry(150, 140, 50, 25)
            self.progress_group.setGeometry(10, self.plotlabel1.height() - 100, self.plotlabel1.width() - 20, 90)
            self.progress_label.setGeometry(self.progress_group.width() - 60, 40, 30, 10)
            self.progress_bar.setGeometry(40, 40, self.progress_group.width() - 80, 40)
            self.plotlabel1.update()
            self.update()

    def reset_improv(self):
        self.new_design_dialog = NewDesignDialog()
        self.new_design_dialog.exec_()
        if self.new_design_dialog.name is not None:
            name = self.new_design_dialog.name
            design = self.new_design_dialog.design
            ip = self.new_design_dialog.ip
            self.robot_connector.HOST = ip
            self.setup_new_design(design)

    def setup_new_design(self,design_path="alphabets.Help Desk.alphabet"):
        self.slider.sp.setValue(5)

        # decide on the design
        self.bodystorm = Bodystorm(design_path)
        self.solution = None
        self.solution_db.clear_db()
        self.bodystorm_history.bodystorm_list.clear()
        self.webView.make_blank_graphs()
        #self.update_model(5)
        self.webView.load_blank_html()

        # need to tell bodystorm history and examples pane what the alphabet is
        self.bodystorm_history.Alphabet = self.bodystorm.Alphabet
        self.traceView.Alphabet = self.bodystorm.Alphabet

    def update_progress_bar(self, value, description):
        if value > 100:
            value = 100
        elif value < 0:
            value = 0

        if value == 0:
            self.statusView.remove_status("updating")
        self.progress_label.setText("{}%".format(value))
        self.progress_description.setText(description)
        self.progress_bar.setValue(value)

    def show_progress_bar(self):
        self.progress_bar.show()
        self.progress_label.show()
        self.progress_description.show()

    def hide_progress_bar(self):
        self.progress_bar.hide()
        self.progress_label.hide()
        self.progress_description.hide()

    def expand_examples(self):
        self.userDialog = ExamplesPane(self.bodystorm, self.update_model)
        self.userDialog.exec_()

    def record(self):

        # do not do anything if the server has not been completely initialized
        if self.bodystorm is None or len(self.participant_names) < 1:
            print(self.bodystorm)
            print(len(self.participant_names))
            self.button.toggle()
            return

        if self.button.isChecked():
            print("GUI >> pressing record at {}".format(time.time()))
            #if self.bodystorm_listener is None:
            #    self.connector.on_click()
            rval = self.confirm_robot_identity()
            if not rval:
                return

            # put up the recording icon
            self.statusView.update_status("record")

            # must start recording simultaneously
            if self.armband_connector.connected:
                print("starting armband")
                arm_status = self.armband_connector.start_record()
            print("starting audio")
            status = self.bodystorm_listener.start_record(self.participant_names, self.participants_to_devices)

            if not status:
                self.button.toggle()
                print("GUI >> recording aborted -- clients not connected")
                self.statusView.remove_status("recording")
                self.update_progress_bar(0,"")
        else:

            # remove the recording icon
            self.statusView.remove_status("recording")
            self.statusView.update_status("wait")
            QCoreApplication.processEvents()

            print("GUI >> untoggling record at {}".format(time.time()))
            self.update_progress_bar(0,"gathering speech")
            self.show_progress_bar()


            # must end recording simultaneously
            #armband_array1, armband_array2 = self.armband_connector.end_record()
            #array1, array2 = self.bodystorm_listener.end_record()

            if self.armband_connector.connected:
                print("beginning end thread 1")
                _thread.start_new_thread(self.armband_connector.end_record, ("end_thread_armband",))
            #self.armband_connector.end_record("sdf")
            print("beginning end thread 2")
            num_participants = len(self.participant_names)
            _thread.start_new_thread(self.bodystorm_listener.end_record, (1,num_participants,))
            if num_participants > 1:
                _thread.start_new_thread(self.bodystorm_listener.end_record, (2,num_participants,))
            #num_participants = len(self.participant_names)
            #self.bodystorm_listener.end_record(num_participants)

            #print("locking while waiting for end")
            #while self.bodystorm_listener.get_return_vals() is None:
            while (self.armband_connector.get_return_vals() is None and self.armband_connector.connected) or self.bodystorm_listener.get_return_vals() is None:
                pass

            print("obtaining return values")
            armband_array1 = "start: 1553722212.6676118 data:"
            armband_array2 = "start: 1553722212.6676118 data:"
            if self.armband_connector.connected:
                armband_array1, armband_array2 = self.armband_connector.get_return_vals()
            array1, array2 = self.bodystorm_listener.get_return_vals()

            self.armband_connector.clear_messages()
            self.bodystorm_listener.clear_messages()

            try:
                pass
            except:
                print("GUI >> cannot connect to clients at {}".format(time.time()))
                self.statusView.remove_status("waiting")
                self.update_progress_bar(0,"")
                return

            # remove the waiting icon
            self.statusView.remove_status("waiting")

            self.update_progress_bar(10,"interpreting speech")

            if len(array1) == 0 and len(array2) == 0:
                print("no demo to create")
                self.update_progress_bar(100,"finished")
                self.hide_progress_bar()
                return

            # depending on who is the robot, we need to rearrange the order of
            # what we give to the bodystorm class
            if not self.p1_is_robot:
                print("GUI >> p1 is robot")
                self.bodystorm.create_demo(array1, array2, armband_array2)
            else:
                print("GUI >> p2 is robot")
                self.bodystorm.create_demo(array2, array1, armband_array1)

            # update the automata
            self.update_model(self.slider.value(), True)

    def command_line_record(self):

        # do not do anything if the server has not been completely initialized
        if self.bodystorm is None or len(self.participant_names) < 1:
            self.button.toggle()
            return

        demo_list = []
        rval = self.confirm_robot_identity()
        if not rval:
            return

        return_prematurely = False
        avail_speeches = self.bodystorm.Alphabet.get_inputs()
        while True:
            print("Human input (type \'exit\' to end conversation): ", end = '')
            inp = input("")
            if "exit" in inp:
                break
            elif "random" in inp:
                demo_list.clear()

                if len(inp) > 7:
                    size = int(inp[7:].strip())
                else:
                    size = random.randrange(2,8)
                for i in range(size):
                    random_inp = random.choice(self.bodystorm.SIGMA)
                    random_out = random.choice(self.bodystorm.OMEGA)
                    demo_list.append((random_inp,random_out))
                break
            elif "merge" in inp:
                #array1 = [("help_query", 0.5, 0, 0.1,0.3,"hi yourself"),("location_statement", 0.9, 0, 0.3,0.4,"hi yourself"),("welcome", 0.5, 0, 0.4,0.5,"hi yourself"),("greeting", 0.5, 1, 0.5,1,"hi"),("farewell", 0.8, 1, 2.5,3,"goodbye"),("gratitude", 0.5, 1, 4,5,"thank you"), ("location_query", 0.7, 1, 5,6,"oh wait")]
                #array2 = [("welcome", 0.9, 0, 0,0.02,"wecl"),("greeting", 0.5, 0, 0.02,0.07,"hi h hi"),("farewell", 0.5, 0, 0.07,0.1,"bye?"),("greeting", 0.5, 0, 1.5,2,"hi yourself"),("help_query", 0.5, 0, 2.2,2.3,"hi yourself"),("location_statement", 0.9, 0, 2.3,2.4,"hi yourself"),("welcome", 0.5, 0, 2.4,2.5,"hi yourself")]

                array_output = []
                array_input = []
                sample_text = ["hi", "bye", "i want", "books", "car", "pizza"]
                sample_categories = ["greeting", "farewell", "gratitude", "you_are_welcome", "location_query", "location_statement", "help_query", "affirm_deny"]
                seconds = 0
                for i in range(0,16):
                    prev_output = None if len(array_output) == 0 else array_output[-1]

                    # can sample an empty input if the previous output was not empty
                    if prev_output is not None and prev_output[4] == seconds:
                        randreal = random.uniform(0,1)
                        if randreal < 0.25:
                            cat = random.choice(sample_categories)
                            tup = (cat, random.uniform(0,1), 0, seconds, seconds + 1, random.choice(sample_text))
                            array_input.append(tup)
                            seconds += 1
                    else:
                        cat = random.choice(sample_categories)
                        tup = (cat, random.uniform(0,1), 0, seconds, seconds + 1, random.choice(sample_text))
                        array_input.append(tup)
                        seconds += 1

                    # can sample an empty output if the previous input was not empty
                    prev_input = None if len(array_input) == 0 else array_input[-1]
                    if prev_input is not None and prev_input[4] == seconds:
                        randreal = random.uniform(0,1)
                        if randreal < 0.25:
                            cat = random.choice(sample_categories)
                            tup = (cat, random.uniform(0,1), 0, seconds, seconds + 1, random.choice(sample_text))
                            seconds += 1
                            array_output.append(tup)
                    else:
                        cat = random.choice(sample_categories)
                        tup = (cat, random.uniform(0,1), 0, seconds, seconds + 1, random.choice(sample_text))
                        seconds += 1
                        array_output.append(tup)

                array_output = [('location_statement', 0.4173206341986235, 1, 7.13, 9.44, 'of course our soccer balls are each a hundred dollars'), ('location_statement', 0.9701561417169948, 1, 16.34, 20.35, 'yes there in the back corner of the store just behind the house where items'), ('location_statement', 0.391337029766751, 1, 22.62, 24.55, 'odd no it actually is'), ('location_statement', 0.9603573271679249, 1, 25.35, 29.81, 'just down away from sporting goods over to the left in the back corner'), ('price_statement', 0.9993253543277191, 1, 34.5, 35.3, 'twenty dollars'), ('you_are_welcome', 0.18407007106570172, 1, 37.9, 38.79, 'of course anytime')]
                array_input = [('location_query', 0.9943863101239633, 0, 2.0, 6.73, 'hi there can you tell me how much your %%HESITATION soccer balls are'), ('location_query', 0.6835401167074843, 0, 9.67, 15.67, 'one hundred dollars and do you have %%HESITATION phone soccer balls instead of proper ones'), ('location_query', 0.9811932447035808, 0, 19.83, 21.72, 'and is that in sporting goods or'), ('location_statement', 0.5040830645204164, 0, 29.22, 33.08, 'great and how much are %%HESITATION soccer socks'), ('price_statement', 0.9884763341902452, 0, 34.27, 35.37, 'twenty dollars thanks')]

                self.bodystorm.create_demo(array_input, array_output)
                return_prematurely = True
                break
            else:
                if inp not in avail_speeches:
                    close_matches = difflib.get_close_matches(inp, avail_speeches)
                    if len(close_matches) == 0:
                        inp = "greeting"
                    else:
                        inp = close_matches[0]
                        print("  (switched to {})".format(inp))
            #print("Human entered " + str(inp))

            print("Robot output: ", end='')
            out = input("")
            if out not in avail_speeches:
                close_matches = difflib.get_close_matches(out, avail_speeches)
                if len(close_matches) == 0:
                    out = "greeting"
                else:
                    out = close_matches[0]
                    print("  (switched to {})".format(out))
            #print("Robot entered " + str(out))

            demo_list.append((inp, out))

        if not return_prematurely:
            self.update_progress_bar(25, "interpreting speech")
            self.show_progress_bar()
            self.bodystorm.create_demo_from_commandline(demo_list)

        print("UPDATING SOLUTION: {}".format(self.solution))
        self.update_model(self.slider.value(), True)
        print("UPDATED SOLUTION: {}".format(self.solution))

    def update_model(self, n=-1, new_trace=False, expand=True):
        if self.bodystorm is None:
            return

        # TODO: replace this with something less hacky
        new_gestures = {}
        for demo in self.bodystorm.demos:
            demo_array = demo.demo_array
            for item in demo_array:
                output = item[1]
                if output.updated_gesture:
                    output.updated_gesture = False
                    new_gesture = output.gesture
                    new_gestures[output.output] = new_gesture
        for demo in self.bodystorm.demos:
            demo_array = demo.demo_array
            for item in demo_array:
                output = item[1]
                if output.output in new_gestures:
                    output.gesture = new_gestures[output.output]
        ##############################

        if n < 0:
            n = self.slider.value()

        print("GUI >> Attempting to update the model with size {} at ".format(n, time.time()))

        # first check whether we need to update the model in the first place!
        #print("querying with size={}".format(n))
        query = self.solution_db.query(self.bodystorm.demos, n)
        in_progress = self.solution_db.check_if_in_progress(self.bodystorm.demos, n)
        if query is not None or in_progress:
            self.solution = self.solution if query is None else query
            if self.solution is not None:
                self.solution.compute_speech_map(self.bodystorm,self.bodystorm.demos)
            self.update_UI(new_trace,in_progress)
            return

        # if the progress bar is currently hidden, show it and set it to 0
        if not self.progress_bar.isVisible():
            self.update_progress_bar(0,"")
            self.show_progress_bar()

        try:
            # run the adaptation algorithm on a separate thread
            #print("about to set controller")
            thread1 = Controller()
            thread1.n = n
            thread1.bodystorm = self.bodystorm
            thread1.new_trace = new_trace
            thread1.gui = self
            thread1.threadcount = self.threadcount

            # print the updates
            print("GUI >> starting new thread {}".format(self.threadcount))
            print("GUI >> demos entering the sat solver:")
            print(str(self.bodystorm))
            self.threadcount += 1

            # communicate from child to parent
            thread1.update_progress.connect(self.update_progress_bar)
            thread1.update_solution.connect(self.update_solution)
            thread1.update_UI.connect(self.update_UI)
            thread1.remove_thread.connect(self.thread_forgotten)

            #print("about to start")

            if len(self.bodystorm.demos) > 0:
                self.statusView.update_status("updating")

            # remove any other currently-running threads
            if len(self.threads) > 0:
                self.thread_wait = True
                #print("there are {} currently-running threads".format(len(self.threads)))
                thread_to_kill = self.threads[0]
                self.threads.clear()
                self.terminate.emit()
                self.terminate.disconnect()

                #print("GUI >> spinning...")
                while thread_to_kill.thread_wait:
                    time.sleep(0.1)
                #print("GUI >> done spinning")

            #print("now appending thread")
            self.threads.append(thread1)
            #print("now attempting to start thread")
            thread1.connect_to_parent(self.terminate)
            #print("starting thread")
            self.solution_db.set_in_progress(self.bodystorm.demos, n)
            thread1.start()
            #print("started")

            # show a dialog of the new trace, asking users to confirm
            if new_trace:
                #print("POPULATING BODYSTORM HISTORY FROM NEW TRACE")
                self.bodystorm_history.populate_bodystorm_history(self.bodystorm, self.solution)
                if expand:
                    self.bodystorm_history.expand_most_recent_example()

        except:
            print("Error: unable to start thread")
            traceback.print_exc()
            exit()

    def update_solution(self, solution,n):
        self.solution = solution
        self.solution_db.remove_in_progress()
        self.statusView.remove_status("updating")

        if solution is None:
            # clear view
            self.webView.load_blank_html()
        else:
            print("GUI >> adding solution at {}".format(time.time()))
            self.solution_db.add(self.bodystorm.demos, solution,n)
            self.save_traces(autosave=True)

    def thread_forgotten(self):
        self.threads.clear()
        #print(self.threads)

        print("GUI >> forgot thread")

    def update_UI(self, new_trace=False, in_progress=False):
        if self.solution is None:
            return

        #Grapher().make_graph(self.solution,self.bodystorm)
        self.webView.update_graph(self.solution, self.bodystorm)

        self.bodystorm_history.populate_bodystorm_history(self.bodystorm, self.solution)
        self.update_representation(str(self.vis_buttons.get_selected()))

        # progress bar
        if not in_progress:
            self.update_progress_bar(100,"finished")
            self.hide_progress_bar()

    def update_representation(self, text):
        if self.solution is None:
            return

        if text == "Clean":
            self.traceView.hide()
            self.font_selector.setEnabled(True)
            self.webView.load_graph("dagre")
            self.webView.show()
        elif text == "Tree":
            self.webView.hide()
            self.traceView.hide()
            self.traceView.update_traces(self.bodystorm, self.update_model)
            self.traceView.show()

    def simulate(self):
        if self.bodystorm is not None and self.solution is not None and self.robot_connector.connected:
            print("GUI >> pressed simulate button at time {}".format(time.time()))
            self.simulate_button.simulate(self.solution, self.bodystorm)
        elif self.bodystorm is not None and self.solution is not None:
            self.simulate_button.export_design(self.solution, self.bodystorm)

    def open_audio_pref(self):
        audio_dialog = AudioInputDialog(self.participants_to_devices)
        audio_dialog.exec_()

        '''
        Below is a temporary fix to a rare bug that causes the program to quit

        TODO: determine cause of bug, remove try-except statements and fix bug
        '''
        try:
            if audio_dialog.devices_to_return is None:
                return
            self.participants_to_devices = audio_dialog.devices_to_return
            self.participant_names = []
            for name in self.participants_to_devices.keys():
                self.participant_names.append(name)

            # update the connection label
            if len(self.participant_names) == 1:
                self.connector.connect_designer(1)
            elif len(self.participant_names) == 2:
                self.connector.connect_designer(1)
                self.connector.connect_designer(2)
        except:
            print("ERROR: specification of audio input devices failed")
            self.participants_to_devices = {}
            self.participant_names = []

    def save_traces(self, autosave=False):
        if not autosave:
            self.userDialog = SaveFile(self.bodystorm)
            self.userDialog.exec_()
        else:
            SaveFile(self.bodystorm).save(True)

    def load_traces(self):
        self.loadFileDialog = LoadFile()
        bodystorm = self.loadFileDialog.openFileNameDialog()
        if bodystorm is not None:
            self.bodystorm = bodystorm
            self.update_model(self.slider.value())

    def change_font_size(self):
        self.font_size = self.font_selector.value()

        if self.solution is not None and self.bodystorm is not None:
            self.webView.update_graph(self.solution, self.bodystorm)
            self.update_representation(str(self.vis_buttons.get_selected()))

    def change_nonverbal_behavior_display(self):
        self.nonverbal_behaviors = self.checkbox.isChecked()

        if self.solution is not None and self.bodystorm is not None:
            self.webView.update_graph(self.solution, self.bodystorm)
            self.update_representation(str(self.vis_buttons.get_selected()))

    def confirm_robot_identity(self):
        self.robotDialog = ChooseRobotDialog(self)
        self.robotDialog.exec_()
        return self.robotDialog.rval

if __name__ == "__main__":

    # start the GUI
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
