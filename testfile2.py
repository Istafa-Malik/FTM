import os, sys, csv, random
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QMessageBox,QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QImage, QIntValidator, QDoubleValidator, QIcon,QFont
from PyQt5.QtCore import Qt, QTimer, QSize, QDateTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import make_interp_spline
from datetime import datetime
import serial.tools.list_ports
import serial 
import subprocess
import ctypes
from PIL import Image, ImageOps
import cv2
import numpy as np
import sounddevice as sd
base_path = "."
# To run this app in PC environment without building exe, comment the lines below and replace all "/" with "/" 
# base_path = sys._MEIPASS
# To build this code make sure all paths have "/" to change directory.
#==============COMMUNICATION PROTOCOLS==============
#--------------------AUTO PAGE----------------------
ON_PROCESS_PAGE="*3:5#"
RX_MODE="*PRS:"
TX_START="*1:1:1:{}:{}:{}#"        #sent from pc
RX_START="*PRC:SR#"                #expected from machine
TX_COMPLETE="*1:1:0:{}:{}#"        #expected from PC
RX_COMPLETE="*PRC:CP#"             # sent from PC
TX_PAUSE="*1:0:1:{}:{}:{}#"        #send from pc
RX_PAUSE="*PRC:SP#"                #expected from machine
TX_RESET="*1:0 :0:{}:{}:{}#"       #sent from pc
RX_RESET="*PRC:RR#"                #expected from machine
RX_READY="*PRS:RED#"                #expected from machine when ready
#----------------------VALUES----------------------
RX_TEMPERATURE="*TEP:xxx#"
RX_PRESSURE="*1:2:Pressure#"
#--------------------MANUAL PAGE-------------------
TX_MOTOR_FORWARD_START="*2:4:1:1#"
TX_MOTOR_FORWARD_STOP="*2:4:2:1#"
TX_MOTOR_BACKWARD_START="*2:4:1:2#"
TX_MOTOR_BACKWARD_STOP="*2:4:2:2#"
TX_VALVE1_OPEN="*2:5:2#"
TX_VALVE1_CLOSE="*2:5:1#"
TX_VALVE2_OPEN="*2:6:1#"
TX_VALVE2_CLOSE="*2:6:2#"
TX_HEATER_START="*2:7:1#"
TX_HEATER_STOP="*2:7:2#"
#=======================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui_cttm.ui', self)
        # Other code...
        self.button_A.setIcon(QIcon(base_path+"/rsc/rsc3.png"))
        self.button_A.setIconSize(QSize(40, 40))
        font_52 = QFont('SF Pro Display', 52, QFont.Bold)
        font_27 = QFont('SF Pro Display', 27, QFont.Bold)
        font_19 = QFont('SF Pro Display', 19, QFont.Bold)
        font_12 = QFont('SF Pro Display', 12, QFont.Bold)
         # Timer setup for process time
        self.timer_process = QTimer(self)
        self.timer_process.timeout.connect(self.update_process_time)
        self.process_start_time = None  # To hold the time when the process starts

        # Sound generation timer
        self.sound_timer = QTimer(self)  # Initialize sound_timer here
        self.sound_timer.timeout.connect(self.play_sound)  # Connect to sound playing


        # Other initialization code...
        self.feed_graph = self.findChild(QWidget, "feed_graph")  # Get the feed_graph widget
        self.frequency = 1  # Default frequency
        self.amplitude= 1 # Default amplitude
        self.time= 0 # Default time

        # Setup the plot
        self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.feed_graph.setLayout(layout)
  
        # Set up axis labels
        self.ax.set(xlabel='Time (s)', ylabel='Amplitude')
        self.ax.grid()
        self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5))

        # Assuming you already have this QLabel for time display
        # self.label_41 is the QLabel in Qt Designer for displaying time
        self.label_41.setText("0y 0m 0d 00:00:00")  # Initialize with default value
        for widget in self.findChildren(QWidget):
            widget.setFont(font_12)
            widget.setFocusPolicy(Qt.NoFocus)
            
        self.input_1.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        # self.input_1.focusInEvent = self.create_focus_in_handler(self.input_1.focusInEvent)
        # self.input_2.focusInEvent = self.create_focus_in_handler(self.input_2.focusInEvent)
        self.input_2.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_3.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_4.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_5.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_6.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_7.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.label_A.setFont(font_19)
        self.label_3.setFont(font_52)
        self.label_4.setFont(font_19)
        self.label_15.setFont(font_52)
        self.label_16.setFont(font_19)        
        self.label_37.setFont(font_27)
        self.label_41.setFont
        self.label_47.setFont(font_27)
        self.label_46.setFont(font_27)
        self.label_55.setFont
        self.mode = "READY"
        self.screen = 0
        self.int_validator = QIntValidator(self)
        self.process_config = []
        self.time_data = []
        self.pressure_data = []
        self.rx_temperature = 0
        self.rx_pressure = 0
        self.ser = None
        self.heater=False
        self.valve1=False
        self.valve2=False
        #self.disable_osk()
        self.camera = cv2.VideoCapture(0)
        #Sound generation counter
        self.sound_count = 0 # count for sound generation
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_cam)
        # self.timer.timeout.connect(self.display_cam2)
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.rx_data)
        
        self.button_1.clicked.connect(self.handle_verify_login)
        self.button_A.pressed.connect(self.handle_button_A_pressed)
        self.button_A.clicked.connect(self.handle_back_pressed)
        self.button_2.clicked.connect(lambda: self.handle_screen_change(4))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        self.button_4.clicked.connect(self.handle_create_config)
        self.button_5.clicked.connect(lambda: self.handle_screen_change(5))
        self.button_6.clicked.connect(self.populate_configlist)
        self.button_7.clicked.connect(self.start_process)
        self.button_8.clicked.connect(self.pause_process)
        self.button_9.clicked.connect(self.reset_process)
        self.button_10.clicked.connect(self.handle_delete_configuration)
        self.button_11.clicked.connect(self.handle_delete)
        self.button_12.clicked.connect(self.handle_manual)
        self.button_13.pressed.connect(self.motor_left_pressed) # motor left
        self.button_13.released.connect(self.motor_left_released) # motor left
        self.button_14.pressed.connect(self.motor_right_pressed)  # motor right
        self.button_14.released.connect(self.motor_right_released)  # motor right
        self.button_15.clicked.connect(self.handle_heater)  # heater on/off
        # self.button_16.clicked.connect(self.handle_valve_1)  # valve 1  on/off
        self.button_18.clicked.connect(self.complete_process)  # valve 2  on/off  
        self.configlist.itemClicked.connect(self.load_config)
        self.input_4.setValidator(self.int_validator)
        self.input_5.setValidator(self.int_validator)
        self.input_6.setValidator(self.int_validator)
        self.input_7.setValidator(self.int_validator)
        self.showPopup2 = self.comboBox.showPopup 
        self.comboBox.showPopup= self.load_comlist
        self.load_comlist()
        self.comboBox.currentIndexChanged.connect(self.set_serial)
        self.handle_screen_change(1)
        self.disable_osk()
    def disable_osk(self):
       #val=os.environ["QT_IM_MODULE"] #= "none"
        print("hello") 
    # def eventFilter(self, obj, event):
    #     self.enable_osk()
    # return super().eventFilter(obj, event)
    # def enable_osk(self):
    #os.environ["QT_IM_MODULE"] = "qtvirtualkeyboard"
    # def show_keyboard(self):
    #     subprocess.Popen(['osk'])  # For Windows, you can use 'osk'
    # On Linux, you might use `onboard` or other keyboard apps
    # def hide_keyboard(self):
    #     subprocess.Popen(['taskkill', '/IM', 'osk.exe', '/F'])  # For Windows
    # On Linux, you might need to kill the process using `pkill onboard`
    def handle_screen_change(self,value):
        if(value == 1): # Login Screen
            self.screen = 1
            self.comboBox.hide()
            self.comboBox.setDisabled(True)
            self.button_A.hide()
            self.init_screen_1()
        elif(value == 2): # Menu Screen
            self.screen = 2
            self.comboBox.hide()
            self.button_A.show()
            self.init_screen_2()
        elif(value == 3): # Create Config Screen
            self.screen = 3
            self.comboBox.hide()
            self.init_screen_3()
        elif(value == 4): # Load Config Screen
            self.screen = 4
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_4(delete=False)
        elif(value == 5): # Process Screen
            self.screen = 5
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_5()
        elif(value == 6): # Process Screen
            self.screen = 6
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_6()

    def handle_button_A_pressed(self):
        self.button_A.setIconSize(QSize(36, 36))

    def init_screen_1(self):
        self.screen = 1
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_1.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap(base_path+"/rsc/rsc2.png"))
        self.label_6.hide()
  
    def init_screen_2(self):
        self.screen = 2
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap())
        self.label_A.setText("Main Menu")
        self.screen_1.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_2.show()
          
    def init_screen_3(self):
        self.screen = 3
        self.label_A.setText("Create Configuration")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_3.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_23.setStyleSheet("color:#FF0000;")
        self.label_23.setText("")
        self.input_3.clear()
        self.input_4.clear()
        self.input_5.clear()
        self.input_6.clear()
        self.input_7.clear()

    def init_screen_4(self,delete):
        self.screen = 4
        if(delete):
            self.label_A.setText("Delete Configuration")
            self.button_5.hide()
            self.button_12.hide()
            self.button_11.show()
            self.button_11.setEnabled(False)
        else:
            self.label_A.setText("Load Configuration")
            self.button_5.setEnabled(False)
            self.button_11.hide()
            self.button_12.show()
            self.button_5.show()

        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_4.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.configlist.hide()
        self.label_29.setText("")
        self.label_30.setText("")
        self.label_31.setText("")
        self.label_32.setText("")
        self.label_33.setText("")

    def init_screen_5(self):
        self.screen = 5
        
        self.label_A.setText("Auto Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_6.hide()
        self.screen_5.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        # shadow1=QGraphicsDropShadowEffect()
        # shadow1.setBlurRadius(30)
        # shadow1.setOffset(0,5)
        # self.button_7.setGraphicsEffect(shadow1)

    def init_screen_6(self):
        self.screen = 6
        self.label_A.setText("Manual Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.show()
        self.button_13.setStyleSheet('background-color:transparent;')
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))
        self.button_13.setIconSize(QSize(100, 100)) 
        self.button_14.setStyleSheet('background-color:transparent;')
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
        self.button_14.setIconSize(QSize(100, 100)) 
        self.button_15.setStyleSheet("background-color:transparent;")
        self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))
        self.button_15.setIconSize(QSize(100, 100)) 
        self.button_16.setStyleSheet("background-color:transparent;")
        self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
        self.button_16.setIconSize(QSize(100, 100)) 
        self.button_17.setStyleSheet("background-color:transparent;")
        self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
        self.button_17.setIconSize(QSize(100, 100)) 
        self.label_10.setText("Clamp 2 OFF")
        self.label_7.setText("Clamp 1 OFF")
        self.setStyleSheet("background-color:rgb(250,250,250);")
        print("screen 6")
        self.timer.start()
        self.timer2.start()
        self.heater=False
        self.valve1=False
        self.valve2=False
        
    def populate_configlist(self):
        if self.configlist.isVisible():
            self.configlist.hide()
        else:
            self.configlist.show()
            self.configlist.clear()
            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None) 
                    for row in reader:
                        if row: 
                            self.configlist.addItem(row[0])  
            list_height = (self.configlist.count()*42) + 2
            if(list_height>350): list_height = 350
            self.configlist.setFixedHeight(list_height)

    def load_config(self):
        selected_items_list = self.configlist.selectedItems()
        if selected_items_list:
            selected_item = selected_items_list[0].text()
            print(f"Selected item text: {selected_item}")

            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None)
                    for row in reader:
                        if row[0] == selected_item:
                            self.process_config = row
                            break
            print("Process Config:", self.process_config)
            self.label_29.setText(self.process_config[0])
            self.label_30.setText(self.process_config[1])
            self.label_31.setText(self.process_config[2])
            self.label_32.setText(self.process_config[3])
            self.label_33.setText(self.process_config[4])
            self.button_5.setEnabled(True)
            self.button_11.setEnabled(True)
            
    def handle_verify_login(self):
        if(self.input_1.text() == "" and self.input_2.text() == ""):
            self.role = ""
            self.button_3.show()
            self.button_10.show()   
            
            self.handle_screen_change(2)
            
        elif(self.input_1.text() == "operator" and self.input_2.text() == "operator"):
            self.role = "operator"
            self.button_3.hide()
            self.button_10.hide()
            
            self.handle_screen_change(2)
        else:
            self.label_6.show()
            self.label_6.setStyleSheet("color:rgb(255,0,0); background:white;")

    def handle_create_config(self):
        
        data = [
            self.input_3.text(),
            self.input_4.text(),
            self.input_5.text(),
            self.input_6.text(),
            self.input_7.text()
        ]

        if any(not field for field in data):
            self.label_23.setText("Error: All fields must be filled")
            self.label_23.setStyleSheet("color:#FF0000;")
            return
        else:
            file_exists = os.path.exists('ConfigFile.csv')
            
            if file_exists:
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None)
                    for row in reader:
                        if self.input_3.text() == row[0]:  # Check if input_3 text exists in the first column
                            self.label_23.setText("Error: Configuration Name already exists")
                            self.label_23.setStyleSheet("color:#FF0000;")
                            return
                        
            with open('ConfigFile.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(['ConfigName', 'Frequency', 'Time', 'Temperature', 'Amplitude'])  # Replace with appropriate header names
                writer.writerow(data)
                self.label_23.setText("Configuration has been saved successfully")
                self.label_23.setStyleSheet("color:#009900;")

    def handle_delete_configuration(self):
        self.init_screen_4(True)

    def handle_delete(self):
        reply=QMessageBox.question(self, 'Confirm', 'Are you sure you want to delete this?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if os.path.exists('ConfigFile.csv'):
                with open('ConfigFile.csv', 'r') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
                with open('ConfigFile.csv', 'w', newline='') as file:
                    writer = csv.writer(file)
                    for row in rows:
                        if row[0] != self.process_config[0]:
                            print(self.process_config)
                            writer.writerow(row)
                            self.init_screen_2()
        else:
            print("Action canceled")

        print("delete pressed")

    # def start_process(self):
    #     self.timer.start(1)

    #     # Retrieve frequency and amplitude from user input
    #     try:
    #         frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
    #         time = float(self.label_31.text())
    #         amplitude = float(self.label_33.text())  # Assuming label_31 holds amplitude value
    #     except ValueError:
    #         print("Invalid frequency or amplitude value")
    #         return

    #     # Generate and play the sound based on frequency and amplitude
    #     self.generate_sound(frequency, amplitude)
    #     self.timer2.start()

    #      #Start the process timer
    #     self.process_start_time = QDateTime.currentDateTime()  # Record the current date and time
    #     self.timer_process.start(1000)  # Update every second
    #     if self.mode == "READY":
    #         if self.feed_graph.layout() is None:
    #             print("Creating new layout")
    #             self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
    #             self.canvas = FigureCanvas(self.fig)
    #             layout = QVBoxLayout()
    #             layout.addWidget(self.canvas)
    #             self.feed_graph.setLayout(layout)

    #         self.ax.set(xlabel='time (s)', ylabel='amplitude (m)')
    #         self.ax.grid()
    #         self.line, = self.ax.plot([], [], color=(0,0.5,0.5))
    #         self.canvas.draw() 
    #         self.t = 1
    #     #self.mode = "PROCESSING"
    #     cmd=TX_START.format(self.label_30.text().zfill(3),self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
    #     #cmd = "*PS:"+ self.label_30.text().zfill(3) + ":" + self.label_31.text().zfill(3) +  ":" +self.label_32.text().zfill(3) +  ":" +self.label_33.text().zfill(3) + "#"
    #     print(cmd)
    #     self.tx_data(cmd)

    def start_process(self):
        self.timer.start(1)

        # Retrieve frequency, time, and amplitude from user input
        try:
            self.frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
            self.time_duration = float(self.label_31.text())  # Assuming label_31 holds time value
            self.amplitude = float(self.label_33.text())  # Assuming label_33 holds amplitude value
            print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
        except ValueError:
            print("Invalid frequency, time, or amplitude value")
            return
    

# Start the sound generation timer to repeat every 2 seconds
        self.sound_timer.start(2000)  # Start timer for every 2000 ms (2 seconds)
        # Generate and play the sound based on frequency and amplitude
        self.generate_sound(self.frequency, self.amplitude)
        self.timer2.start()

        # Start the process timer
        self.process_start_time = QDateTime.currentDateTime()  # Record the current date and time
        self.timer_process.start(1000)  # Update every second

        if self.mode == "READY":
            if self.feed_graph.layout() is None:
                print("Creating new layout")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)
                self.feed_graph.setLayout(layout)

            # Set the graph axis labels
            self.ax.set(xlabel='Time (s)', ylabel='Amplitude (m)')
            self.ax.grid()

            # Initialize an empty plot line for amplitude
            self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5), label='Amplitude')
            
            # Optionally, you can set a secondary y-axis for frequency
            self.ax_freq = self.ax.twinx()  # Create a secondary y-axis
            self.ax_freq.set_ylabel('Frequency (Hz)')  # Label for frequency
            self.ax_freq.set_ylim(0, self.frequency * 2)  # Adjust limits if needed

            # Set initial time
            self.t = 0

            # Initialize data lists
            self.time_data = []
            self.sine_data = []

            # Draw the initial empty canvas
            self.canvas.draw()
            
            # Start the update timer as usual for updating the plot
        if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.display_plot)
            self.update_timer.start(1000)  # Update the plot every 1 second

        

            self.display_plot()

    def display_plot(self):
         # Fetch and convert values from labels
        try:
            self.frequency = float(self.label_30.text())
            self.time_duration = float(self.label_31.text())
            self.amplitude = float(self.label_33.text())
            print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
        except ValueError:
            print("Error: Please ensure that frequency, time, and amplitude are valid numbers.")
            return

        self.t += 1  # Increment time
        self.time_data.append(self.t)

        # Generate sine wave data based on the current time, frequency, and amplitude
        sine_value = self.amplitude * np.sin(2 * np.pi * self.frequency * self.t)
        self.sine_data.append(sine_value)

        # Check the length of data to determine how much to plot
        if len(self.time_data) > 25:
            t_data = self.time_data[-25:]
            sine_wave_data = self.sine_data[-25:]
        else:
            t_data = self.time_data
            sine_wave_data = self.sine_data

        # Update the plot with new sine wave data
        self.line.set_data(t_data, sine_wave_data)

        # Clear previous annotations before drawing new ones
        self.ax.cla()  # Clear the axis
        self.ax.grid()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude (m)')
        self.ax.set_title('Sine Wave')

        # Redraw the line with updated data
        self.line, = self.ax.plot(t_data, sine_wave_data, color=(0, 0.5, 0.5))

        # Annotate points on the graph
        for x, y in zip(t_data, sine_wave_data):
            self.ax.annotate(f"{y:.2f}", xy=(x, y), textcoords="offset points", xytext=(0, 10), ha='center')

        # Adjust limits and redraw the canvas
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

        
    
    def generate_sound(self, frequency, amplitude, duration=2, sample_rate=44100):
        #"""
        #Generates and plays a sine wave sound based on frequency and amplitude.
        
        #:param frequency: Frequency of the sound in Hz
        #:param amplitude: Amplitude of the sound (0.0 to 1.0)
        #:param duration: Duration of the sound in seconds
        #:param sample_rate: Sample rate (default is 44100 Hz)
        #"""
        # Generate time values
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Generate a sine wave
        audio_signal = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Output the sound through the system's audio output
        sd.play(audio_signal, samplerate=sample_rate)
        sd.wait()
     
    def play_sound(self):
        """Play the sound based on the current frequency and amplitude."""
        audio_signal = self.generate_sound(self.frequency, self.amplitude)
        #sd.play(audio_signal, samplerate=44100)  # Play the generated sound
        sd.wait()  # Wait until the sound has finished playing
    # Increment the sound generation count
        self.sound_count += 1
        #self.sound_count_label.setText(f"Sound Count: {self.sound_count}")  # Update sound count label
        print(f"Sound generated {self.sound_count} times.")  # Optional print statement

    def complete_process(self):
       # """ 
       #Handles the "Complete" button press.
        #Completes the process and finalizes operations.
        #"""
         print("Complete button pressed.")
        # Add logic to complete the process
         self.mode = "COMPLETE"
         self.label_38.setText("PROCESS COMPLETE")
        # Stop timers, finalize data processing, and clean up if needed
         self.stop_process()
        # Add any other cleanup or final state handling here
        # Stop the sound timer
         if hasattr(self, 'sound_timer'):
            self.sound_timer.stop()  # Stop the sound generation

    def pause_process(self):
        self.timer.stop()
        self.mode = "PAUSED"
        cmd = TX_PAUSE.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        cmd = "*PP:000:000:000:000#"
        print(cmd)
        self.tx_data(cmd)
        self.stop_process()
        # Stop the sound timer
        if hasattr(self, 'sound_timer'):
           self.sound_timer.stop()  # Stop the sound generation

    def reset_process(self):
       #"""Resets the process to its initial state."""
        print("Reset button pressed.")
        self.stop_process()
        # Stop the sound timer
        if hasattr(self, 'sound_timer'):
           self.sound_timer.stop()  # Stop the sound generation

    # Clear the graph
        if hasattr(self, 'ax'):
           self.ax.clear()
           self.canvas.draw()
 
        self.stop_process()
        self.time_data = []
        self.sine_data = []
        self.pressure_data = []
        self.feed_cam.setPixmap(QPixmap())
        cmd =TX_RESET.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
        print(cmd)
        self.tx_data(cmd)


    def stop_process(self):
    #"""Stops all timers and clears the plot."""
        for timer in [self.timer, self.timer2, self.timer_process, getattr(self, 'update_timer', None)]:
         if timer and timer.isActive():
            timer.stop()
        print("Timers stopped.")

     # Function to update the timer label
    def update_process_time(self):
        # Calculate elapsed time in seconds
        elapsed_seconds = self.process_start_time.secsTo(QDateTime.currentDateTime())

        # Calculate elapsed days, hours, minutes, and seconds
        days = elapsed_seconds // 86400
        hours = (elapsed_seconds % 86400) // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        # Convert days into years and months (assuming 30 days per month and 365 days per year)
        years = days // 365
        months = (days % 365) // 30
        remaining_days = (days % 365) % 30
        # Print the calculated time values for debugging
        print(f"{years}y {months}m {remaining_days}d {hours:02}:{minutes:02}:{seconds:02}")
        
        # Update QLabel 'label_41' with formatted time
        self.label_41.setText(f"{years}y {months}m {remaining_days}d {hours:02}:{minutes:02}:{seconds:02}")
    
    def display_cam(self):
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(frame.data, 640, 480, 1920, QImage.Format_RGB888)
            if self.screen == 5:
                self.feed_cam.setPixmap(QPixmap.fromImage(q_img))
            elif self.screen == 6:
                self.feed_cam_2.setPixmap(QPixmap.fromImage(q_img))
        else:
            self.feed_cam.setText("Failed to load Camera!")
            self.feed_cam_2.setText("Failed to load Camera!")

    # def display_plot(self):
    # # Fetch and convert values from labels
    #     try:
    #      self.frequency = float(self.label_30.text())
    #      self.time = float(self.label_31.text())
    #      self.amplitude = float(self.label_33.text())
    #       # Debugging: Print the values to ensure they're correctly retrieved
    #      print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time}")

    #     except ValueError:
    #         print("Error: Please ensure that frequency, time, and amplitude are valid numbers.")
    #     return
    #     self.t = self.t + 1
    #     #self.label_36.setText(str(self.rx_pressure))
    #     #self.label_37.setText(str(self.rx_temperature))
    #     self.time_data.append(self.t)
    #     #self.pressure_data.append(self.rx_pressure)
    #     # Generate sine wave data based on the current time, frequency, and amplitude
    #     sine_value = self.amplitude * np.sin(2 * np.pi * self.frequency * self.t)

    # # Append the sine wave value to the data list
    #     self.sine_data.append(sine_value)

    #     if len(self.time_data) > 25:
    #         t_data = self.time_data[-25:]
    #         sine_wave_data=self.sine_data[-25]
    #         #p_data = self.pressure_data[-25:]        
    #         #self.line.set_data(t_data, p_data)
    #     else:

    #         t_data=self.time_data
    #         sine_wave_data=self.sine_data
    #         #update plot with new sine_wave_data
    #         self.line.set_data(t_data,sine_wave_data)
    #         #self.line.set_data(self.time_data, self.rx_pressure_data)
    #     self.ax.relim()
    #     self.ax.autoscale_view()
    #     self.canvas.draw()
        
    def handle_back_pressed(self):
        self.button_A.setIconSize(QSize(40, 40))
        self.label_9.setText("")
        if(self.screen > 1): 
            if (self.screen==6):
                self.screen=4
            elif (self.screen==4):
                self.screen=2
            else:
                self.screen = self.screen - 1
        print(self.screen)
        self.handle_screen_change(self.screen)
        self.heater=False
        self.valve1=False
        self.valve2=False

    def handle_app_quit(self):
        self.close()
     
    def rx_data(self):
        try:
            if self.ser and self.ser.in_waiting > 0:
                my_data = self.read_until_delimiter()
                print("Data received:", my_data)
                ## condition to check formating of data i.e. data[0]=='*'
                #if data is TEMP
                if my_data[1:5]==RX_TEMPERATURE[1:5]:
                    self.rx_temperature = int(my_data[5:len(my_data)-1])
                #if data is PRESSURE
                elif my_data[1:5]==RX_PRESSURE[1:5]:
                    self.rx_pressure=(int(my_data[5:len(my_data)-1]))
                    pressure_data = self.rx_pressure / 133.322  # Convert Pascals to mmHg
                #if data is MODE
                elif my_data[0:5]==RX_MODE:
                    if my_data==RX_READY:
                        self.mode="READY"
                    elif my_data==RX_START:
                        self.mode="PROCESSING"
                    elif my_data==RX_PAUSE:
                        self.mode="PAUSED"
                    elif my_data==RX_RESET:
                        self.mode="HOMING"
                    elif my_data==RX_COMPLETE:
                        self.mode="COMPLETE PROCESS"
                self.label_38.setText(self.mode)
                self.label_37.setText(str(self.rx_temperature))
                self.label_47.setText(str(self.rx_temperature))
                # self.label_55.setText(str(self.rx_pressure))
                self.rx_pressure = 15
                self.label_55.setText(str(self.rx_pressure))
                self.label_46.setText(str(self.rx_pressure))

                # Check if the received data is the RX_COMPLETE command

            self.handle_screen5()
        except serial.SerialException as e:
            print(f"SerialException: {e}")    
        # save function here

    def tx_data(self,data):
        try:
            self.ser.write(data.encode())
        except Exception as err:
             self.label_9.setText("ERROR: NO SERIAL PORT")
               
    def handle_screen5(self):
        if self.mode == "READY":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            self.button_A.setEnabled(True)
        elif self.mode == "PROCESSING":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            self.button_A.setEnabled(True)
            self.display_plot()
        elif self.mode == "PAUSED":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            self.button_A.setEnabled(True)
        # elif self.mode == "HOMING":
        #     self.button_7.setEnabled(False)
        #     self.button_8.setEnabled(False)
        #     self.button_9.setEnabled(False)
        #     self.button_A.setEnabled(False)

    def load_comlist(self):
        self.comboBox.clear()
        com_ports_list = []
        com_ports = serial.tools.list_ports.comports()
        for port in com_ports:
            self.comboBox.addItem(f"{port.device}")
        self.showPopup2()

    def read_until_delimiter(self):
        data = bytearray()
        delimiter=b'#'
        while True:
            if self.ser.in_waiting > 0:  # Check if there's data waiting in the buffer
                byte = self.ser.read(1)  # Read one byte at a time
                data.extend(byte)
                if byte == delimiter:
                    break
        return data.decode('utf-8')
    
    def set_serial(self):
        if self.ser != None:
            self.ser.close() 
        if self.comboBox.currentIndex() > -1:
            comPort= self.comboBox.currentText()
            self.ser = serial.Serial(comPort, baudrate=115200, timeout=1)
            
    def handle_manual(self):
        print("on screen 6")
        self.init_screen_6()

    def motor_left_pressed(self):
        print("motor pressed")
        self.button_13.setStyleSheet('background-color:transparent;')
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left_pressed.png"))
        self.tx_data(TX_MOTOR_BACKWARD_START)

    def motor_left_released(self):
        print("motor released")
        self.button_13.setStyleSheet("background-color:transparent;")
        self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))

        self.tx_data(TX_MOTOR_BACKWARD_STOP)

    def motor_right_pressed(self):
        print("motor pressed")
        self.button_14.setStyleSheet("background-color:transparent;")
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right_pressed.png"))

        self.tx_data(TX_MOTOR_FORWARD_START)

    def motor_right_released(self):
        print("motor released")
        self.button_14.setStyleSheet("background-color:transparent;")
        self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
        self.tx_data(TX_MOTOR_FORWARD_STOP)

    def handle_heater(self):
        self.heater= not self.heater
        if(self.heater): 
            #heater on 
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater_pressed.png"))

            self.tx_data(TX_HEATER_START)
        else: 
            #heater off
            self.tx_data(TX_HEATER_STOP)
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))

        print("heater")

    def handle_valve_1(self):
        self.valve1 = not self.valve1
        if (self.valve1):
            #valve on
            print("value 1 ON") 
            self.label_7.setText("Clamp 1 ON")
            self.button_16.setStyleSheet("background-color:transparent;")
            self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))
            
            self.tx_data(TX_VALVE1_OPEN)
        else:
            # valve off
            print("value 1 OFF")
            self.label_7.setText("Clamp 1 OFF")
            self.button_16.setStyleSheet("background-color:transparent;")
            self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
            self.tx_data(TX_VALVE1_CLOSE)

    def handle_valve_2(self):
        print("hello from handle_valve_2")
        self.valve2 = not self.valve2
        if (self.valve2):
            #valve on
            print("value 2 ON")
            self.label_10.setText("Clamp 2 ON")
            self.button_17.setStyleSheet("background-color:transparent;")
            self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))

            self.tx_data(TX_VALVE1_OPEN)
        else:
            # valve off
            print("value 2 OFF")
            self.label_10.setText("Clamp 2 OFF")
            self.button_17.setStyleSheet("background-color:transparent;")
            self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))

            self.tx_data(TX_VALVE2_CLOSE)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()