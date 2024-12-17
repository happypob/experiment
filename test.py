import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np
from max30102 import MAX30102
import hrcalc
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


class HeartRateMonitor(object):
    """
    A class that encapsulates the MAX30102 device into a thread.
    """

    LOOP_TIME = 0.01

    def __init__(self, print_raw=False, print_result=False):
        self.bpm = 0
        self.spo2 = 0
        if print_raw is True:
            print('IR, Red')
        self.print_raw = print_raw
        self.print_result = print_result

    def run_sensor(self):
        sensor = MAX30102()
        ir_data = []
        red_data = []
        bpms = []

        # data for show
        self.spos = []
        self.bpms = []

        while not self._thread.stopped:
            num_bytes = sensor.get_data_present()
            if num_bytes > 0:
                while num_bytes > 0:
                    red, ir = sensor.read_fifo()
                    num_bytes -= 1
                    ir_data.append(ir)
                    red_data.append(red)
                    if self.print_raw:
                        print("{0}, {1}".format(ir, red))

                while len(ir_data) > 100:
                    ir_data.pop(0)
                    red_data.pop(0)

                if len(ir_data) == 100:
                    bpm, valid_bpm, spo2, valid_spo2 = hrcalc.calc_hr_and_spo2(ir_data, red_data)
                    if valid_bpm:
                        bpms.append(bpm)
                        while len(bpms) > 4:
                            bpms.pop(0)
                        self.bpm = np.mean(bpms)
                        if (np.mean(ir_data) < 50000 and np.mean(red_data) < 50000):
                            self.bpm = 0
                            if self.print_result:
                                print("Finger not detected")
                        if self.print_result:
                            print("BPM: {0}, SpO2: {1}".format(self.bpm, spo2))
                        
                        if spo2 > 0:
                            self.bpms.append(self.bpm)
                            self.spos.append(spo2)

            time.sleep(self.LOOP_TIME)

        sensor.shutdown()

    def start_sensor(self):
        self._thread = threading.Thread(target=self.run_sensor)
        self._thread.stopped = False
        self._thread.start()

    def stop_sensor(self, timeout=2.0):
        self._thread.stopped = True
        self.bpm = 0
        self._thread.join(timeout)

    def show(self):
        x = np.arange(len(self.spos))
        y = np.array(self.spos)
    
        yhat = savgol_filter(y, 51, 3)
    
        plt.plot(x, yhat)
        plt.show()


class Application(tk.Tk):
    def __init__(self, heart_rate_monitor):
        super().__init__()
        self.title("Heart Rate and SpO2 Monitor")
        self.geometry("300x200")

        # Heart Rate and SpO2 labels
        self.bpm_label = ttk.Label(self, text="BPM: --", font=("Arial", 16))
        self.bpm_label.pack(pady=20)

        self.spo2_label = ttk.Label(self, text="SpO2: --%", font=("Arial", 16))
        self.spo2_label.pack(pady=20)

        # Start and Stop buttons
        self.start_button = ttk.Button(self, text="Start", command=self.start_monitor)
        self.start_button.pack(side="left", padx=10, pady=10)

        self.stop_button = ttk.Button(self, text="Stop", command=self.stop_monitor)
        self.stop_button.pack(side="right", padx=10, pady=10)

        # Heart rate monitor instance
        self.heart_rate_monitor = heart_rate_monitor
        self.update_data()

    def start_monitor(self):
        # Start the sensor in a separate thread
        self.heart_rate_monitor.start_sensor()

    def stop_monitor(self):
        # Stop the sensor
        self.heart_rate_monitor.stop_sensor()

    def update_data(self):
        # Update the GUI with the current BPM and SpO2 values
        bpm = self.heart_rate_monitor.bpm
        spo2 = self.heart_rate_monitor.spo2

        if bpm > 0:
            self.bpm_label.config(text=f"BPM: {bpm:.2f}")
        else:
            self.bpm_label.config(text="BPM: --")

        if spo2 > 0:
            self.spo2_label.config(text=f"SpO2: {spo2:.2f}%")
        else:
            self.spo2_label.config(text="SpO2: --%")

        # Update the labels every 500 ms
        self.after(500, self.update_data)


if __name__ == "__main__":
    # Create the heart rate monitor object
    hrm = HeartRateMonitor(print_raw=False, print_result=True)

    # Create the Tkinter application and pass the hrm object
    app = Application(hrm)

    # Start the Tkinter event loop
    app.mainloop()