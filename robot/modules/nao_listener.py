import time
import numpy as np
import sys
import os.path
import threading
import Queue as queue
import soundfile as sf
import sounddevice as sd
#from shutil import copyfile
import os
import pdb


class SpeechRecorder:

    def __init__(self, soundfile):

        self.soundfile = soundfile
        self.is_recording = False
        self.timeout = False
        self.rec_lock = threading.Lock()
        self.energy_window = []
        self.exit_flag = False
        self.done_recording = False
        self.duration_timer = None
        self.timer = None

    def reset(self):
        self.is_recording = False
        self.timeout = False
        self.energy_window = []
        self.exit_flag = False
        self.done_recording = False
        self.duration_timer = None
        self.timer = None

    def start_recording(self, base_silence):
        """
        return only once audio has begun recording
        """
        self.reset()
        if self.timeout is False:
            print('Listening for speech now:')
            #this_thread = threading.Thread(target=self.record_speech, args=(
            #                            self.soundfile, base_silence))
            #this_thread.start()
            self.record_speech(self.soundfile, base_silence)

    def get_audio(self):
        """
        block until audio is done recording. return soundfile name immediately
        after
        """
        while self.done_recording is False:
            time.sleep(0.01)
        print("done recording, waiting for 0.5 seconds")
        time.sleep(0.5)
        while not os.path.isfile(self.soundfile):
            time.sleep(0.01)
        print("obtained file")
        return self.soundfile

    def record_speech(self, soundfile, base_silence):
        """
        record audio until speech has been detected,
        then that speech has completed
        """
        import sys

        self.rec_lock.acquire()
        print("record_speech acquired rec lock")
        thread = threading.Thread(target=self.record_audio, args=(soundfile,))
        thread.start()
        self.rec_lock.release()
        print("record_speech released rec lock")

        self.mic_energy_terminator(base_silence)

    def record_audio(self, soundfile):
        """
        record audio until self.terminate is called
        """
        import sounddevice as sd
        import soundfile as sf

        class Timer:

            def _timer(self, duration):
                time.sleep(duration)
                self._duration_passed = True

            def __init__(self, duration):
                self._duration_passed = False
                timer_thread = threading.Thread(target=self._timer,
                    args=(duration,))
                timer_thread.start()

            @property
            def duration_passed(self):
                return self._duration_passed


        self.rec_lock.acquire()
        print("record audio acquired rec lock")

        recording_queue = queue.Queue()
        self.energy_window = []
        self.is_recording = True
        total_data_len = 0

        def callback(indata, frames, time, status):
            #pdb.set_trace()
            import time
            #print("in the callback")
            waveform = indata.copy()
            zlist = zip(*waveform)
            recording_queue.put(waveform)
            for frame in zlist:
                self.energy_window.append(frame[0])
                while self.timer is None:
                    time.sleep(0.01)
                if self.timer.duration_passed is True:
                    self.energy_window.pop(0)

        with sf.SoundFile(self.soundfile, mode='x', samplerate=44100,
                        channels=2) as file:
            print(self.soundfile)
            with sd.InputStream(device=0,channels=2, callback=callback):
                self.timer = Timer(1)
                self.rec_lock.release()
                print("record audio released rec lock")
                while self.exit_flag is not True:
                    print("writing audio data")
                    data = recording_queue.get()
                    #print("obtained data from queue")
                    total_data_len += len(data)
                    #print("about to write")
                    file.write(data)
                    #print("written")
                while not recording_queue.empty():
                    print("writing remaining audio data")
                    file.write(recording_queue.get())
                print("about to flush")
                file.flush()
                #os.fsync(file.fileno())

        #copyfile(soundfile, "another.wav")
        print("TOTAL DATA LEN: {} at 44100 sr".format(total_data_len))

        self.exit_flag = False
        self.done_recording = True

    def mic_energy_terminator(self, base_silence):
        """
        mic_energy_terminator() listens to the audio input on self.audio_input
        and terminates recording on that stream when, after noise is detected,
        silence is detected. Noise level is evaluated on the average of a one
        second sliding window.
        """

        silence_multiplier = 1.5

        while self.timeout is False and self.is_recording is False:
            time.sleep(0.1)
        energy = self.get_energy()
        while self.timeout is False and energy < (base_silence*silence_multiplier):
            energy = self.get_energy()
            print('no speech yet detected - energy = ' + str(energy))
            time.sleep(0.01)
        while self.timeout is False and energy >= (base_silence*silence_multiplier):
            energy = self.get_energy()
            print('speech has been detected - energy = ' + str(energy))
            time.sleep(0.01)
        print("TERMINATING RECORDING")
        self.terminate_recording()

    def get_energy(self):
        """
        Returns the energy being recived by the mic, as recorded by
        record_audio. Will block until self.energy_window is written to, or
        this SpeechRecorded object is timed out, in which case it will return
        None.
        """
        while self.timeout is False:
            try:
                mean = np.mean(np.abs(self.energy_window))
                return mean
            except:
                continue


    def terminate_recording(self):
        """
        Can be called to end the recording process. Doing so in this
        way will not terminate any mic_energy_terminator() threads created by
        record_speech()
        """
        self.exit_flag = True

    def cancel(self):
        """
        Can be called to terminate all recording processes and all
        mic_energy_terminator() threads created by this module.
        """
        self.timeout = True
        self.exit_flag = True
