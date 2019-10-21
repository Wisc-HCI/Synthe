from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib import pyplot as plt
import numpy as np
import myo
import time
import datetime
import sys
import pickle

class Listener(myo.DeviceListener):

    def __init__(self):
        self.acceleration = []
        self.gyroscope = []
        self.collecting = False

    def on_paired(self, event):
        print("pairing")
        #event.device.vibrate(myo.VibrationType.short)
    def on_unpaired(self, event):
        print("unpairing")
        return False    # Stop the hub

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

class Trainer(QThread):

    some_data_passer = pyqtSignal(object,object)
    all_data_passer = pyqtSignal(object)

    def connect_armband(self):
        myo.init('myo_armband/sdk/myo.framework/myo')
        self.hub = myo.Hub()
        self.listener = Listener()

    def run(self):
        self.listener.clear_accel_gyro()

        start_time = time.time()
        temp_time = time.time()
        prefix_len = 0
        print("about to start listening")
        while self.hub.run(self.listener.on_event, 500):
            curr_time = time.time()
            if curr_time - start_time > 5:
                break
            if curr_time - temp_time > 0.5:
                new_data,prefix_len = self.package_some_data(prefix_len)
                temp_time = time.time()
                self.some_data_passer.emit(new_data,5)
        all_data = self.package_all_data()
        self.all_data_passer.emit(all_data)

    def package_some_data(self,prefix_len):
        accel_ts_data, gyro_ts_data = self.listener.get_acc_gyro_data()
        next_prefix_len = len(accel_ts_data)

        accel_data = []
        gyro_data = []
        ts_data = []
        for i in range(prefix_len,len(accel_ts_data)):
            d = accel_ts_data[i]
            accel_data.append(d[0])
            ts_data.append(d[1]/1000000.0)
        for i in range(prefix_len,len(gyro_ts_data)):
            d = gyro_ts_data[i]
            gyro_data.append(d[0])

        if prefix_len == 0:
            within_interval_index = -1
            for d in range(0,len(ts_data)):
                if ts_data[-1] - ts_data[d] <= 0.5:
                    within_interval_index = d
                    break

            ts_data = ts_data[within_interval_index:]
            accel_data = accel_data[within_interval_index:]
            gyro_data = gyro_data[within_interval_index:]

        data = self.package_data_helper(accel_data,gyro_data,ts_data)
        return data,next_prefix_len

    def package_all_data(self):
        accel_ts_data, gyro_ts_data = self.listener.get_acc_gyro_data()

        accel_data = []
        gyro_data = []
        ts_data = []
        for d in accel_ts_data:
            accel_data.append(d[0])
            ts_data.append(d[1]/1000000.0)
        for d in gyro_ts_data:
            gyro_data.append(d[0])

        within_interval_index = -1
        for d in range(0,len(ts_data)):
            if ts_data[-1] - ts_data[d] <= 5:
                within_interval_index = d
                break

        ts_data = ts_data[within_interval_index:]
        accel_data = accel_data[within_interval_index:]
        gyro_data = gyro_data[within_interval_index:]

        return self.package_data_helper(accel_data,gyro_data,ts_data)

    def package_data_helper(self,accel_data,gyro_data,ts_data):
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

        return [x,y,z,gx,gy,gz,tim]
