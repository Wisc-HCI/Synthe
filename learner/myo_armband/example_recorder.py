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
    print("Hello, {}!".format(event.device_name))
    #event.device.vibrate(myo.VibrationType.short)
  def on_unpaired(self, event):
    return False  # Stop the hub

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

class Plot(object):

  def __init__(self, listener):
    self.listener = listener
    self.fig = plt.figure()
    self.axes = [self.fig.add_subplot('81' + str(i)) for i in range(1, 4)]
    [(ax.set_ylim([-100, 100])) for ax in self.axes]
    self.graphs = [ax.plot(np.arange(512), np.zeros(512))[0] for ax in self.axes]
    plt.ion()

  def update_plot(self):
    emg_data = self.listener.get_acc_data()

  def main(self):
    while True:
      self.update_plot()
      plt.pause(1.0 / 30)

if __name__ == '__main__':
  typ = sys.argv[1]
  try:
    with open("data_train.pkl", "rb") as fp:
      all_data = pickle.load(fp)
  except:
    print("no such data_train.pkl file")
    all_data = []
  myo.init('sdk/myo.framework/myo')
  hub = myo.Hub()
  listener = Listener()
  for i in range(1):
    print("Ready?")
    time.sleep(1)
    print("Set.")
    time.sleep(1)
    print("GO!")

    listener.clear_accel_gyro()

    start_time = time.time()
    while hub.run(listener.on_event, 500):
      if time.time() - start_time > 5:
        break
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

    print(ts_data[0])
    print(ts_data[-1])

    within_interval_index = -1
    for d in range(0,len(ts_data)):
      if ts_data[-1] - ts_data[d] <= 5:
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

    data = [x,y,z,gx,gy,gz,tim,typ]
    all_data.append(data)

    print("done!")
    time.sleep(0.5)

  with open("data_train.pkl", "wb") as fp:
    pickle.dump(all_data, fp)


