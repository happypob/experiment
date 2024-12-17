import tkinter as tk
from tkinter import scrolledtext
import sys
import threading
import time

class Redirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

    def flush(self):
        pass

def long_running_task(text_widget):
    for i in range(50):
        print(f"doing task: {i+1}...")
        time.sleep(0.1)
    print("task finished")

def start_task(text_widget):
    task_thread = threading.Thread(target=lambda: long_running_task(text_widget))
    task_thread.daemon = True
    task_thread.start()