import os, sys, csv, random
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QMessageBox, QPushButton, QLineEdit
from PyQt5.QtGui import QPixmap, QImage, QIntValidator, QDoubleValidator, QIcon, QFont
from PyQt5.QtCore import Qt, QTimer, QSize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import serial.tools.list_ports
import serial 
import time
from main3 import VirtualKeyboard
from PIL import Image, ImageOps
import cv2
import json
import numpy as np
base_path = "."


# To run this app in PC environment without building exe, comment the lines below  
#base_path = sys._MEIPASS
# To build this code make sure all paths have "/" to change directory.



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{base_path}/ui_cttm.ui', self)
        
        
        
        self.keyboard = None
        # self.keyboard_enabled = False
        
        self.load_settings()
        
        self.init_screen_1()
        
        self.remaining_time = None
        self.button_A.setIcon(QIcon(base_path+"/rsc/rsc3.png"))
        self.button_A.setIconSize(QSize(40, 40))
        font_52 = QFont('SF Pro Display', 52, QFont.Bold)
        font_27 = QFont('SF Pro Display', 27, QFont.Bold)
        font_19 = QFont('SF Pro Display', 19, QFont.Bold)
        font_12 = QFont('SF Pro Display', 12, QFont.Bold)
        

        self.mode = "READY"
        self.screen = 0
        self.int_validator = QIntValidator(self)
        self.process_config = []
        # self.time_data = []
        # self.force_data = []
        self.rx_temperature = 0
        # self.rx_force = 0
        # self.time_data = []
        # self.voltage_data = []
        # self.current_data = []
        self.rx_current = 1
        self.rx_voltage = 1
        # self.ser = None
        #self.ser = serial.Serial(port='COM5', baudrate=9600, timeout = 1000)
        self.heater=False
        self.motor_forward = False
        self.motor_reverse = False
        # self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        # self.timer.timeout.connect(self.display_cam)
        self.timer2 = QTimer()
        
        self.last_command = None  # Or an empty string

        self.ser = None
        self.ser_2 = None
        # Other initializations
        self.remaining_time = None
        
        # Initialize empty data lists for plotting
        self.time_data = []
        self.voltage_data = []
        self.current_data = []

        # Initialize the time tracker `self.t`
        self.t = 0

    
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
        self.button_13.pressed.connect(self.motor_forward_pressed) # Actuate Forward
        # self.button_13.released.connect(self.motor_forward_released) # Actuate Forward
        self.button_14.clicked.connect(self.motor_reverse_pressed)  # Actuate Reverse
        # self.button_14.released.connect(self.motor_reverse_released)  # Actuate Reverse
        self.button_15.clicked.connect(self.handle_heater)  # heater on/off
        self.button_16.clicked.connect(lambda: self.handle_screen_change(7))
        self.button_17.clicked.connect(self.settings)
        #self.button_16.pressed.connect(self.valve_1_pressed)  # valve 1
        #self.button_16.released.connect(self.valve_1_released)  # valve 1
        #self.button_17.pressed.connect(self.valve_2_pressed)  # valve 1
        #self.button_17.released.connect(self.valve_2_released)  # valve 1
        self.configlist.itemClicked.connect(self.load_config)
        #self.input_4.setValidator(self.int_validator)
        #self.input_5.setValidator(self.int_validator)
        self.input_6.setValidator(self.int_validator)
        self.input_7.setValidator(self.int_validator)

        # self.showPopup2 = self.comboBox.showPopup 
        # self.comboBox.showPopup= self.load_comlist

        self.ser = None
        self.ser_2 = None
        self.initialize_ports()

    def initialize_ports(self):
        # Initialize serial ports based on previously selected values or defaults
        self.load_comlist()
        self.load_comlist_2()

        # Connect signals for comboBox_2
        self.comboBox.currentIndexChanged.connect(self.set_serial)
        self.comboBox_2.currentIndexChanged.connect(self.handle_comboBox_2_change)
        
        
        self.handle_screen_change(1)


      # virtual keboard
    
    def show_virtual_keyboard(self, input_field, event=None):
        # Check if the keyboard exists and is visible before proceeding
        if self.keyboard is None or not self.keyboard.isVisible():
            # If no keyboard is open, create a new one
            self.keyboard = VirtualKeyboard(input_field, self)
            self.keyboard.finished.connect(self.on_keyboard_closed)  # Reset the flag when the keyboard closes
            self.keyboard.show()
        else:
            # If a keyboard is already open, change the focused input field
            self.keyboard.input_field = input_field

    def handle_focus_event(self, event):
        # Ensure that the keyboard opens only for the clicked input field
        self.show_virtual_keyboard(self.sender(), event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

    def on_keyboard_closed(self):
        # Safely reset the keyboard reference when it's closed
        self.keyboard = None
    
    

    def handle_screen_change(self, value):
        # Close the virtual keyboard if it is open when changing screens
        if self.keyboard is not None and self.keyboard.isVisible():
            self.keyboard.close_keyboard()

        for widget in self.findChildren(QtWidgets.QPushButton):
            widget.setFocusPolicy(Qt.NoFocus)

        if value == 1:  # Login Screen
            self.screen = 1
            self.comboBox.hide()
            # self.comboBox.setDisabled(True)
            self.comboBox_2.hide()
            # self.comboBox_2.setDisabled(True)
            self.button_A.hide()
            self.init_screen_1()

        elif value == 2:  # Menu Screen
            self.screen = 2
            self.comboBox.hide()
            self.comboBox_2.hide()
            self.button_A.show()
            self.init_screen_2()

        elif value == 3:  # Create Config Screen
            self.screen = 3
            self.comboBox.hide()
            self.comboBox_2.hide()
            self.init_screen_3()

        elif value == 4:  # Load Config Screen
            self.screen = 4
            self.comboBox.hide()
            self.comboBox_2.hide()
            self.init_screen_4(delete=False)

        elif value == 5:  # Process Screen
            self.screen = 5
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.comboBox_2.show()
            self.comboBox_2.setDisabled(False)
            self.init_screen_5()

        elif value == 6:  # Manual Screen
            self.screen = 6
            self.comboBox.hide()  # Hide supply COM selection
            self.comboBox_2.show()
            self.comboBox_2.setDisabled(False)
            self.init_screen_6()

        elif value == 7:  # Settings Screen
            self.screen = 7
            self.comboBox_2.show()
            self.comboBox.setDisabled(False)
            self.init_screen_7()

    def close_keyboard(self):
        if self.keyboard is not None:
            self.keyboard.close()  # Close the keyboard if open
            self.keyboard = None


    def handle_button_A_pressed(self):
        self.button_A.setIconSize(QSize(36, 36))

    def init_screen_1(self):
        self.screen = 1
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_7.hide()
        self.screen_1.show()
        self.setStyleSheet("background-color:white;")
        self.label_A.setPixmap(QPixmap(base_path+"/rsc/rsc2.png"))
        self.label_6.setStyleSheet("color:white;")
        self.label_10.hide()
        self.label_11.hide()
        self.label_12.hide()
        self.comboBox.hide()

        # Connect input_1 and input_2 to trigger virtual keyboard when clicked
        self.input_1.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_1, event)
        self.input_2.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_2, event)

    def handle_focus_event(self, event):
        self.show_virtual_keyboard(event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

  
    def init_screen_2(self):
        if (self.mode == "operator"):
            self.screen = 2
            self.setStyleSheet("background-color:white;")
            self.label_A.setPixmap(QPixmap())
            self.label_A.setText("Main Menu")
            self.button_3.hide()
            self.button_10.hide()
            self.screen_1.hide()
            self.screen_3.hide()
            self.screen_4.hide()
            self.screen_5.hide()
            self.screen_6.hide()
            self.screen_7.hide()
            self.screen_2.show()
            self.label_10.hide()
            self.label_11.hide()
        elif (self.mode == "admin"):  
            self.screen = 2
            self.setStyleSheet("background-color:white;")
            self.label_A.setPixmap(QPixmap())
            self.label_A.setText("Main Menu")
            self.button_3.show()
            self.button_10.show()
            self.screen_1.hide()
            self.screen_3.hide()
            self.screen_4.hide()
            self.screen_5.hide()
            self.screen_6.hide()
            self.screen_7.hide()
            self.screen_2.show()
            self.label_10.hide()
            self.label_11.hide()
          
    def init_screen_3(self):
        self.screen = 3
        self.label_A.setText("Create Configuration")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_7.hide()
        self.screen_3.show()
        self.setStyleSheet("background-color:#E2E2E2;")
        self.label_23.setStyleSheet("color:#FF0000;")
        self.label_23.setText("")
        #self.input_3.clear()
        #self.input_4.clear()
        #self.input_5.clear()
        self.input_6.clear()
        self.input_7.clear()
        self.label_10.hide()
        self.label_11.hide()
        
        self.input_3.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_3, event)
        self.input_6.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_6, event)
        self.input_7.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_7, event)
        self.input_8.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_8, event)

    def handle_focus_event(self, event):
        self.show_virtual_keyboard(event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event
        
        

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
        self.screen_7.hide()
        self.screen_4.show()
        self.setStyleSheet("background-color:#E2E2E2;")
        self.configlist.hide()
        self.label_29.setText("")
        #self.label_30.setText("")
        #self.label_31.setText("")
        self.label_32.setText("")
        self.label_33.setText("")
        self.label_42.setText("")
        self.label_10.hide()
        self.label_11.hide()
        
        
    def init_screen_5(self):
        self.screen = 5
        self.label_A.setText("Auto Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_6.hide()
        self.screen_7.hide()
        self.screen_5.show()
        self.setStyleSheet("background-color:#E2E2E2;")
        self.input_11.setText(self.label_32.text())
        self.input_9.setText(self.label_33.text())
        self.input_10.setText(self.label_42.text())
        self.label_10.show()
        self.label_11.show()
        # self.load_comlist()
        # self.comboBox.currentIndexChanged.connect(self.set_serial)
        self.timer2.setInterval(1000)  # Set interval to 1 second for rx_data
        self.timer2.timeout.connect(self.rx_data)
        self.timer2.start()


    def init_screen_6(self):
        self.screen = 6
        self.label_A.setText("Manual Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_7.hide()
        self.screen_6.show()
        self.comboBox_2.show()
        self.comboBox_2.setDisabled(False)
        self.label_10.hide()
        self.label_11.hide()
        self.button_13.setStyleSheet("background-color:transparent;")
        self.button_13.setIcon(QIcon(base_path+"/rsc/Forward.png"))
        self.button_13.setIconSize(QSize(100, 100)) 
        self.button_14.setStyleSheet("background-color:transparent;")
        self.button_14.setIcon(QIcon(base_path+"/rsc/reverse.png"))
        self.button_14.setIconSize(QSize(100, 100)) 
        self.button_15.setStyleSheet("background-color:transparent;")
        self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))
        self.button_15.setIconSize(QSize(100, 100)) 
        # self.load_comlist_2()
        
        self.setStyleSheet("background-color:#E2E2E2;")
        print("Screen 6 - Manual Operation")

        
    def init_screen_7(self):
        self.screen = 7
        self.label_A.setText("Settings")
        self.screen_1.hide()
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_4.hide()
        self.screen_5.hide()
        self.screen_6.hide()
        self.screen_7.show()
        self.label_10.hide()
        self.label_11.hide()
        self.comboBox.hide()
        self.setStyleSheet("background-color:#E2E2E2;")
        print("screen 7")
        
        self.input_12.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_12, event)
        self.input_14.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_14, event)
        self.input_13.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_13, event)
        
        

    def handle_focus_event(self, event):
        self.show_virtual_keyboard(event)
        QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event



    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm Exit', 
                                    "Are you sure you want to exit?", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Unconditionally send the command to turn off the power supply
                self.tx_data("OUTP:GEN OFF *IDN\n")
                print("Power supply turned off before closing GUI")

                # Send the command to the MCU to stop the process
                self.tx_data("*1:0:0#", port='mcu')  # Send stop command to MCU
                print("Stop protocol *1:0:0# sent to MCU")
                
                # Check if the virtual keyboard is open and close it
                if self.keyboard is not None and self.keyboard.isVisible():
                    self.keyboard.close()
                    print("Virtual keyboard closed")

            except Exception as e:
                print(f"Error turning off power supply or sending stop command to MCU: {e}")

            event.accept()  # Proceed with closing the window
        else:
            event.ignore()  # Ignore the close event and keep the window open




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
            #self.label_30.setText(self.process_config[1])
            #self.label_31.setText(self.process_config[2])
            self.label_32.setText(self.process_config[1])
            self.label_33.setText(self.process_config[2])
            self.label_42.setText(self.process_config[3])
            self.button_5.setEnabled(True)
            self.button_11.setEnabled(True)
            
    def handle_verify_login(self):
        if(self.input_1.text() == "admin" and self.input_2.text() == "admin"):
            self.mode = "admin"
            self.handle_screen_change(2)
            
        elif(self.input_1.text() == "operator" and self.input_2.text() == "123"):
            self.mode = "operator"
            self.handle_screen_change(2)
        else:
            self.label_6.setStyleSheet("color:rgb(255,0,0);")

    def handle_create_config(self):
        # Retrieve text from inputs
        input_7_value = self.input_7.text()
        input_8_value = self.input_8.text()

        # Check if the input values are numeric and within the specified limits
        try:
            input_7_number = float(input_7_value)
            input_8_number = float(input_8_value)

            # Check if the value of input_7 is greater than 32
            if input_7_number > 32:
                self.label_23.setText("Error: Value of Voltage cannot exceed 32")
                self.label_23.setStyleSheet("color:#FF0000;")
                return
            # Check if the value of input_8 is greater than 10
            elif input_8_number > 10:
                self.label_23.setText("Error: Value of Current cannot exceed 10")
                self.label_23.setStyleSheet("color:#FF0000;")
                return

            # If both conditions are met, proceed with configuration creation
            data = [
                self.input_3.text(),
                self.input_6.text(),
                input_7_value,
                input_8_value
            ]

            # Further code to handle the creation of the configuration
            self.label_23.setText("Configuration created successfully.")
            self.label_23.setStyleSheet("color:#009900;")
        
        except ValueError:
        # Handle the case where the input values are not numeric
         self.label_23.setText("Error: Invalid input. Please enter numeric values.")
        self.label_23.setStyleSheet("color:#FF0000;")

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
                    writer.writerow(['ConfigName', 'Linear Speed', 'Distance', 'Temperature', 'Voltage', 'Current'])  # Replace with appropriate header names
                writer.writerow(data)
                self.label_23.setText("Configuration has been saved successfully")
                self.label_23.setStyleSheet("color:#009900;")

    def handle_delete_configuration(self):
        self.init_screen_4(True)

    def handle_delete(self):
        reply=QMessageBox.question(self, 'Confirm', 'Are you sure you want to delete this?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
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
        
    #     if self.mode == "READY":
    #         if self.feed_graph.layout() is None:
    #             print("Creating new layout")
    #             self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
    #             self.canvas = FigureCanvas(self.fig)
    #             layout = QVBoxLayout()
    #             layout.addWidget(self.canvas)
    #             self.feed_graph.setLayout(layout)

    #         self.ax.set(xlabel='time (s)', ylabel='force (g)')
    #         self.ax.grid()
    #         self.line, = self.ax.plot([], [], color=(0,0.5,0.5))
    #         self.canvas.draw() 
    #         self.t = 1


        # # Initialize GUI components
        # self.setWindowTitle("Process with Delay")
        # self.resize(400, 300)

        # Setup button
        # self.button_7 = QPushButton("Start", self)
        # self.button_7.clicked.connect(self.on_button_7_pressed)

        # Feed graph widget
        # self.feed_graph = QWidget(self)

        # # Set up layout
        # layout = QVBoxLayout(self)
        # layout.addWidget(self.button_7)
        # layout.addWidget(self.feed_graph)
        # self.setLayout(layout)

        # # Set mode
        # self.mode = "READY"

        # # Initialize timer
        # self.timer = QTimer(self)
        # self.timer.setSingleShot(True)  # Make the timer single-shot so it fires only once
        # self.timer.timeout.connect(self.start_process)  # Connect the timer's timeout signal to the start_process method

    # def on_button_7_pressed(self):
    #     # Start the timer with a 10-second delay
    #     print(" Starting 10-second delay...")
        # self.timer.start(10000)  # 10 seconds = 10000 milliseconds

    # def start_process(self):
    #     try:
    #         # Update label_20 to show "Start"
    #         self.label_20.setText("Start")
    #         self.label_20.setStyleSheet("color:#00FF00;")  # Optional: Set color to green
            
    #         # Retrieve the threshold values from inputs
    #         try:
    #             voltage_threshold = float(self.input_9.text())
    #             current_threshold = float(self.input_10.text())
    #         except ValueError:
    #             self.label_23.setText("Error: Invalid threshold values")
    #             self.label_23.setStyleSheet("color:#FF0000;")
    #             return

    #         # Retrieve the time limit from input_11
    #         try:
    #             self.time_limit = int(self.input_11.text())  # Time in seconds
    #         except ValueError:
    #             self.label_23.setText("Error: Invalid time limit")
    #             self.label_23.setStyleSheet("color:#FF0000;")
    #             return

    #         # Check if voltage * current exceeds 160
    #         if voltage_threshold * current_threshold > 160:
    #             # Switch to channel 2 if the product exceeds 160
    #             command_CHN_SEL = "INST OUT2 *IDN\n"
    #             print(f"Switching to channel 2: {command_CHN_SEL}")
    #             self.tx_data(command_CHN_SEL)

    #             # Set current to current_threshold / 2
    #             current_threshold /= 2
    #             print(f"Adjusted current threshold: {current_threshold}")

    #         # Transmit the voltage and current setting commands
    #         set_voltage_cmd = f"VOLT {voltage_threshold} *IDN\n"
    #         set_current_cmd = f"CURR {current_threshold} *IDN\n"
    #         self.tx_data(set_voltage_cmd)
    #         self.tx_data(set_current_cmd)

    #         # Open the power supply channel
    #         self.tx_data("OUTP:GEN ON\n")

    #         # Send protocol to the MCU to indicate the process has started
    #         self.tx_data("*1:1:1#", port='mcu')  # Send start command to the MCU
    #         print("Start protocol *1:1:1# sent to MCU")

    #         # Initialize the plot if not done already
    #         if self.feed_graph.layout() is None:
    #             print("Creating new layout for the plot")
    #             self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
    #             self.canvas = FigureCanvas(self.fig)
    #             layout = QVBoxLayout()
    #             layout.addWidget(self.canvas)
    #             self.feed_graph.setLayout(layout)

    #             # Initialize empty data lists for plotting
    #             self.time_data = []
    #             self.voltage_data = []  # Store voltage data
    #             self.current_data = []  # Store current data

    #             # Initialize the time tracker `self.t`
    #             self.t = 0  # Initialize `self.t` to keep track of time

    #             # Set labels and grid for the plot
    #             self.ax.set(xlabel='Time (s)', ylabel='Voltage (V) / Current (A)')
    #             self.ax.grid()

    #             # Initialize the two lines for voltage and current
    #             self.voltage_line, = self.ax.plot([], [], label='Voltage (V)', color='blue')
    #             self.current_line, = self.ax.plot([], [], label='Current (A)', color='red')

    #             # Add a legend to differentiate the lines
    #             self.ax.legend()

    #             # Draw the canvas to update the plot
    #             self.canvas.draw()

    #         # Start or resume the process timer
    #         if self.remaining_time is None:  # First start or after reset
    #             self.process_timer = QTimer()
    #             self.process_timer.timeout.connect(self.on_process_complete)  # Modified to send completion protocol when time runs out
    #             self.process_timer.setSingleShot(True)  # Ensure it only runs once
    #             self.process_timer.start(self.time_limit * 1000)  # Convert to milliseconds
    #         else:  # Resuming after pause
    #             self.process_timer = QTimer()
    #             self.process_timer.timeout.connect(self.on_process_complete)
    #             self.process_timer.setSingleShot(True)
    #             self.process_timer.start(self.remaining_time)  # Start with the remaining time
    #             print(f"Resuming process with {self.remaining_time / 1000} seconds left.")
    #             self.remaining_time = None  # Reset after resuming

    #         # Start the update timer as usual for updating the plot
    #         if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
    #             self.update_timer = QTimer()
    #             self.update_timer.timeout.connect(self.display_plot)
    #             self.update_timer.start(1000)  # Update the plot every 1 second

    #     except Exception as e:
    #         self.label_23.setText(f"Error: {e}")
    #         self.label_23.setStyleSheet("color:#FF0000;")
    #         print(f"Exception in start_process: {e}")

    # # New method to handle process completion
    # def on_process_complete(self):
    #     try:
    #         # Send protocol to the MCU to indicate the process is complete
    #         self.tx_data("*1:1:0#", port='mcu')  # Send completion command to the MCU
    #         print("Completion protocol *1:1:0# sent to MCU")
            
    #         # Turn off the power supply channel
    #         command_GEN_OFF = "OUTP:GEN OFF *IDN\n"
    #         self.tx_data(command_GEN_OFF)
    #         print("Power supply turned off: OUTP:GEN OFF *IDN")

    #         self.label_20.setText("Complete")
    #         self.label_20.setStyleSheet("color:#0000FF;")  # Optional: Set color to blue

    #         # Call the reset_process or any other function to stop/reset the process
    #         self.reset_process()
    #     except Exception as e:
    #         print(f"Error in on_process_complete: {e}")

    def start_process(self):
        # Check if the MCU port is selected
        if not self.comboBox_2.currentText():
            self.label_9.setText("Error: Please select a COM port for MCU.")
            self.label_9.setStyleSheet("color:#FF0000;")
            return  # Exit the function if no port is selected
        
        # Check if the Supply port is selected (if needed)
        if not self.comboBox.currentText():
            self.label_12.setText("Error: Please select a COM port for Supply.")
            self.label_12.setStyleSheet("color:#FF0000;")
            return  # Exit the function if no port is selected
        try:
            # Send start protocol to the MCU
            start_protocol = "*1:1:1#"
            print(f"Sending start protocol to MCU: {start_protocol}")
            self.tx_data(start_protocol, port='mcu')  # Send start command to the MCU

            # Initialize a variable to track feedback status
            feedback_received = False
            feedback_timeout = 300  # Timeout period in seconds
            check_interval = 5  # Interval to check for feedback

            # Check for feedback from the MCU for up to 300 seconds
            for elapsed_time in range(0, feedback_timeout, check_interval):
                # Sleep for the check interval
                time.sleep(check_interval)

                # Check for feedback from the MCU
                mcu_feedback = self.rx_data()  # Receive feedback
                print(f"Checking feedback from MCU: {mcu_feedback}")

                if mcu_feedback == "*PRS:STR#":  # Expected feedback for start
                    feedback_received = True
                    break  # Exit loop if feedback is received

            if not feedback_received:
                # If feedback is not received after 300 seconds, display error
                self.label_9.setText("Error: No response from MCU within 300 seconds.")
                self.label_9.setStyleSheet("color:#FF0000;")
                print("No feedback received from MCU within the timeout period.")
                return  # Exit the method early

            # Continue with the process if feedback is received
            self.label_20.setText("Start")
            self.label_20.setStyleSheet("color:#00FF00;")  # Optional: Set color to green

            # Retrieve the threshold values from inputs
            try:
                voltage_threshold = float(self.input_9.text())
                current_threshold = float(self.input_10.text())
            except ValueError:
                self.label_23.setText("Error: Invalid threshold values")
                self.label_23.setStyleSheet("color:#FF0000;")
                return

            # Retrieve the time limit from input_11
            try:
                self.time_limit = int(self.input_11.text())  # Time in seconds
            except ValueError:
                self.label_23.setText("Error: Invalid time limit")
                self.label_23.setStyleSheet("color:#FF0000;")
                return

            # Check if voltage * current exceeds 160
            if voltage_threshold * current_threshold > 160:
                # Switch to Channel 2 and set values
                command_CHN_SEL = "INST OUT2 *IDN\n"
                print(f"Switching to Channel 2: {command_CHN_SEL}")
                self.tx_data(command_CHN_SEL)

                # Set voltage and current for Channel 2 (with adjusted current)
                current_threshold_channel2 = current_threshold / 2
                set_voltage_cmd = f"VOLT {voltage_threshold} *IDN\n"
                set_current_cmd = f"CURR {current_threshold_channel2} *IDN\n"
                self.tx_data(set_voltage_cmd)
                self.tx_data(set_current_cmd)
                print(f"Voltage set to {voltage_threshold} and current set to {current_threshold_channel2} on Channel 2")

                # Open Channel 2
                self.tx_data("OUTP:SEL ON *IDN\n")
                print("Channel 2 turned on")

                # Switch back to Channel 1 and set values
                command_CHN_SEL = "INST OUT1 *IDN\n"
                print(f"Switching to Channel 1: {command_CHN_SEL}")
                self.tx_data(command_CHN_SEL)
                current_threshold_channel1 = current_threshold / 2
                set_voltage_cmd = f"VOLT {voltage_threshold} *IDN\n"
                set_current_cmd = f"CURR {current_threshold_channel1} *IDN\n"
                self.tx_data(set_voltage_cmd)
                self.tx_data(set_current_cmd)
                print(f"Voltage set to {voltage_threshold} and current set to {current_threshold_channel1} on Channel 1")

                # Open Channel 1
                self.tx_data("OUTP:SEL ON *IDN\n")
                print("Channel 1 turned on")
                self.tx_data("OUTP:GEN ON *IDN\n")

            else:
                # Normal case: Set voltage and current for Channel 1
                command_CHN_SEL = "INST OUT1 *IDN\n"
                print(f"Switching to Channel 1: {command_CHN_SEL}")
                self.tx_data(command_CHN_SEL)
                set_voltage_cmd = f"VOLT {voltage_threshold} *IDN\n"
                set_current_cmd = f"CURR {current_threshold} *IDN\n"
                self.tx_data(set_voltage_cmd)
                self.tx_data(set_current_cmd)
                print(f"Voltage set to {voltage_threshold} and current set to {current_threshold} on Channel 1")

                # Open Channel 1
                self.tx_data("OUTP:SEL ON *IDN\n")
                print("Channel 1 turned on")
                self.tx_data("OUTP:GEN ON *IDN\n")

            # Initialize the plot if not done already
            if self.feed_graph.layout() is None:
                print("Creating new layout for the plot")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)
                self.feed_graph.setLayout(layout)

                # Initialize empty data lists for plotting
                self.time_data = []
                self.voltage_data = []  # Store voltage data
                self.current_data = []  # Store current data

                # Initialize the time tracker `self.t`
                self.t = 0  # Initialize `self.t` to keep track of time

                # Set labels and grid for the plot
                self.ax.set(xlabel='Time (s)', ylabel='Voltage (V) / Current (A)')
                self.ax.grid()

                # Initialize the two lines for voltage and current
                self.voltage_line, = self.ax.plot([], [], label='Voltage (V)', color='blue')
                self.current_line, = self.ax.plot([], [], label='Current (A)', color='red')

                # Add a legend to differentiate the lines
                self.ax.legend()

                # Draw the canvas to update the plot
                self.canvas.draw()

            # Start or resume the process timer
            if self.remaining_time is None:  # First start or after reset
                self.process_timer = QTimer()
                self.process_timer.timeout.connect(self.on_process_complete)  # Modified to send completion protocol when time runs out
                self.process_timer.setSingleShot(True)  # Ensure it only runs once
                self.process_timer.start(self.time_limit * 1000)  # Convert to milliseconds
            else:  # Resuming after pause
                self.process_timer = QTimer()
                self.process_timer.timeout.connect(self.on_process_complete)
                self.process_timer.setSingleShot(True)
                self.process_timer.start(self.remaining_time)  # Start with the remaining time
                print(f"Resuming process with {self.remaining_time / 1000} seconds left.")
                self.remaining_time = None  # Reset after resuming

            # Start the update timer as usual for updating the plot
            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.display_plot)
                self.update_timer.start(1000)  # Update the plot every 1 second

        except Exception as e:
            self.label_23.setText(f"Error: {e}")
            self.label_23.setStyleSheet("color:#FF0000;")
            print(f"Exception in start_process: {e}")


    def on_process_complete(self):
        try:
            # Send protocol to the MCU to indicate the process is complete
            self.tx_data("*1:1:0#", port='mcu')  # Send completion command to the MCU
            print("Completion protocol *1:1:0# sent to MCU")

            # Turn off the power supply channel
            command_GEN_OFF = "OUTP:GEN OFF *IDN\n"
            self.tx_data(command_GEN_OFF)
            self.tx_data("*RST *IDN\n")
            print("Power supply turned off: OUTP:GEN OFF *IDN")

            # Update label to show "Complete"
            self.label_20.setText("Complete")
            self.label_20.setStyleSheet("color:#0000FF;")  # Optional: Set color to blue

            # Stop the update timer to stop plotting
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
                print("Update timer stopped.")

            # Clear the graph data and reset the plot
            if hasattr(self, 'ax'):
                self.time_data = []
                self.voltage_data = []
                self.current_data = []

                # Clear the plot lines
                self.ax.cla()  # Clear the axes
                self.ax.set(xlabel='Time (s)', ylabel='Voltage (V) / Current (A)')
                self.ax.grid()
                self.voltage_line, = self.ax.plot([], [], label='Voltage (V)', color='blue')
                self.current_line, = self.ax.plot([], [], label='Current (A)', color='red')
                self.ax.legend()

                # Redraw the canvas to update the cleared plot
                self.canvas.draw()
                print("Graph reset.")

        except Exception as e:
            print(f"Error in on_process_complete: {e}")




        
    def get_voltage_from_power_supply(self):
        try:
            # Send command to the power supply to check the voltage
            self.tx_data("VOLT? *IDN\n")
            
            # Read the response from the power supply
            voltage_data = self.read_until_delimiter(self.ser)  # Pass self.ser here
            
            # Check if the response is None or empty
            if voltage_data is None or voltage_data.strip() == "":
                print("No data received from the power supply.")
                return 0.0  # Return default value if no data is received
            
            # Strip and convert the response to a float
            voltage_value = float(voltage_data.strip())

            print(f"Voltage data received: {voltage_value}")
            return voltage_value
        
        
        except ValueError as ve:
            print(f"ValueError: {ve} - Cannot convert voltage data to float.")
            return 0.0  # Return default value if conversion fails
        except Exception as e:
            print(f"Error: {e}")
            return 0.0  # Return default value in case of other errors

    def get_current_from_power_supply(self):
        try:
            # Send command to the power supply to check the current
            self.tx_data("MEAS:CURR? *IDN\n")
            
            # Read the response from the power supply
            current_data = self.read_until_delimiter(self.ser)  # Pass self.ser here
            
            # Check if the response is None or empty
            if current_data is None or current_data.strip() == "":
                print("No data received from the power supply.")
                return 0.0  # Return default value if no data is received
            
            # Convert the response to a float
            current_value = float(current_data.strip())
            
            print(f"Current data received: {current_value}")
            return current_value

        except ValueError as ve:
            print(f"ValueError: {ve} - Cannot convert current data to float.")
            return 0.0  # Return default value if conversion fails
        except Exception as e:
            print(f"Error: {e}")
            return 0.0  # Return default value in case of other errors


        
    # def tx_data(self, data):
    #     # Simulate data transmission
    #     print(f"Transmitting data: {data}")



        # Comment out the serial port closing to keep the port open for subsequent communication
        # finally:
        #     if self.ser.is_open:
        #         self.ser.close()
        #         print(f"Closed serial port: {self.ser.port}")

        

    # def complete_process(self):
    # # Send the COMPLETE CMD
    #     cmd = "*1:0:0#"
    #     print(cmd)
    #     self.tx_data(cmd)

    #     # Turn off the power supply channel
    #     self.tx_data("OUTP:GEN OFF *IDN\n")  # Sending GEN_OFF command


    def pause_process(self):
        # Stop both timers if they are active
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
            print("Update timer stopped.")

        if hasattr(self, 'process_timer') and self.process_timer.isActive():
            # Calculate the remaining time (in milliseconds)
            self.remaining_time = self.process_timer.remainingTime()
            self.process_timer.stop()
            print(f"Process paused with {self.remaining_time / 1000} seconds remaining.")
            
            # Send the pause protocol
            pause_cmd = "*1:0:0#"  # Protocol indicating process is paused
            print(f"Sending pause protocol to MCU: {pause_cmd}")
            self.tx_data(pause_cmd, port='mcu')  # Specify MCU port for sending the command

            # Add logic to receive and validate the MCU feedback (assuming rx_data handles MCU port internally)
            mcu_feedback = self.rx_data()  # Call rx_data without port argument
            if mcu_feedback == "*PRS:STP#":
                print("Pause feedback received from MCU: *PRS:STP#")
            else:
                print(f"Unexpected feedback from MCU: {mcu_feedback}")
                
                
                self.label_20.setText("Pause")
                self.label_20.setStyleSheet("color:#FFA500;")  # Optional: Set color to orange




        # # Close the serial port if it's open
        # if hasattr(self, 'ser') and self.ser.is_open:
        #     self.ser.close()
        #     print(f"Serial port {self.ser.port} closed.")

        # # Clear the plot
        # if hasattr(self, 'ax') and hasattr(self, 'canvas'):
        #     self.ax.clear()
        #     self.ax.set_xlabel('Time (s)')
        #     self.ax.set_ylabel('Values')
        #     self.ax.grid()
        #     self.ax.legend()
        #     self.canvas.draw()

        # Reset data lists
        # self.time_data = []
        # self.voltage_data = []
        # self.current_data = []

        # Send the stop command and complete protocol
        # cmd = "*1:0:0#"  # Complete protocol to indicate manual stop
        # print(f"Sending stop protocol: {cmd}")
        # self.tx_data(cmd)
        # print("Sending stopped")
        # # Turn off the power supply channel
        # self.tx_data("OUTP:GEN OFF *IDN\n")  # Sending GEN_OFF command

    def reset_process(self):
        # Stop timers if they are active
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
            print("Update timer stopped.")

        if hasattr(self, 'process_timer') and self.process_timer.isActive():
            self.process_timer.stop()
            print("Process timer stopped.")
            
        self.tx_data("OUTP:GEN OFF *IDN\n")
        self.tx_data("*RST *IDN\n")

        # Close the serial port if open
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print(f"Serial port {self.ser.port} closed.")

        # Reset the data and stop the process
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.remaining_time = None  # Reset the remaining time

        # Send the stop protocol to the MCU
        cmd = "*1:0:0#"  # Complete stop protocol
        print(f"Sending stop protocol to MCU: {cmd}")
        self.tx_data(cmd, port='mcu')  # Specify MCU port for sending the command

        # Receive and validate MCU feedback
        mcu_feedback = self.rx_data()  # Call rx_data without port argument
        if mcu_feedback == "*PRS:STP#":
            print("Reset feedback received from MCU: *PRS:STP#")
            print("Process reset successfully.")
        else:
            print(f"Unexpected feedback from MCU: {mcu_feedback}")
            
            
        # Update label_20 to show "Reset"
        self.label_20.setText("Reset")
        self.label_20.setStyleSheet("color:#FF0000;")  # Optional: Set color to red

        print("Process stopped.")




    # def display_cam(self):
    #     ret, frame = self.camera.read()
    #     if ret:
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         q_img = QImage(frame.data, 640, 480, 1920, QImage.Format_RGB888)
    #         self.feed_cam.setPixmap(QPixmap.fromImage(q_img))
    #     else:
    #         self.feed_cam.setText("Failed to load Camera!")

    # def display_plot(self):
    #     self.t = self.t + 1
    #     self.label_36.setText(str(self.rx_force))
    #     self.label_37.setText(str(self.rx_temperature))
    #     self.time_data.append(self.t)
    #     self.force_data.append(self.rx_force)
        
    #     if len(self.time_data) > 25:
    #         t_data = self.time_data[-25:]
    #         f_data = self.force_data[-25:]        
    #         self.line.set_data(t_data, f_data)

    #     else:
    #         self.line.set_data(self.time_data, self.force_data)
        
    #     self.ax.relim()
    #     self.ax.autoscale_view()
    #     self.canvas.draw()

    # def display_plot(self):
    #     self.t += 1
    #     voltage_actual = self.get_voltage_from_power_supply()
    #     current_actual = self.get_current_from_power_supply()

    #     self.label_16.setText(f"Voltage: {voltage_actual} V")
    #     self.label_17.setText(f"Current: {current_actual} A")


    #     try:
    #         voltage_threshold = float(self.input_9.text()) if self.input_9.text() else float('inf')
    #         current_threshold = float(self.input_10.text()) if self.input_10.text() else float('inf')
    #     except ValueError:
    #         self.label_23.setText("Error: Invalid threshold values")
    #         self.label_23.setStyleSheet("color:#FF0000;")
    #         return

    #     if voltage_actual > voltage_threshold:
    #         voltage_actual = voltage_threshold
    #         self.label_16.setText(f"Voltage (Exceeded): {voltage_actual} V")

    #     if current_actual > current_threshold:
    #         current_actual = current_threshold
    #         self.label_17.setText(f"Current (Exceeded): {current_actual} A")
            
    #     # print(f"Voltage data received: {voltage_actual}\nCurrent data received: {current_actual}")

    #     self.time_data.append(self.t)
    #     self.voltage_data.append(voltage_actual)
    #     self.current_data.append(current_actual)

    #     t_data = self.time_data[0:]
    #     v_data = self.voltage_data[0:]
    #     c_data = self.current_data[0:]
        
    #     print(f"Voltage data received: {v_data}\nCurrent data received: {c_data}")

    #     self.voltage_line.set_data(t_data, v_data)
    #     self.current_line.set_data(t_data, c_data)

    #     if len(t_data) > 0:
    #         self.ax.set_xlim(min(t_data), max(t_data))
    #     if len(v_data) > 0 and len(c_data) > 0:
    #         self.ax.set_ylim(min(min(v_data), min(c_data)), max(max(v_data), max(c_data)))

    #     self.canvas.draw()


    def display_plot(self):
        self.t += 1
        voltage_actual = self.get_voltage_from_power_supply()
        current_actual = self.get_current_from_power_supply()
        
         # Update the labels with the real-time values
        self.label_25.setText(f" {voltage_actual} V")  # Update label_25
        self.label_26.setText(f" {current_actual} A")   # Update label_26

        # self.label_16.setText(f"Voltage: {voltage_actual} V")
        # self.label_17.setText(f"Current: {current_actual} A")

        try:
            voltage_threshold = float(self.input_9.text()) if self.input_9.text() else float('inf')
            current_threshold = float(self.input_10.text()) if self.input_10.text() else float('inf')
        except ValueError:
            self.label_23.setText("Error: Invalid threshold values")
            self.label_23.setStyleSheet("color:#FF0000;")
            return

        if voltage_actual > voltage_threshold:
            voltage_actual = voltage_threshold
            self.label_16.setText(f"Voltage (Exceeded): {voltage_actual} V")

        if current_actual > current_threshold:
            current_actual = current_threshold
            self.label_17.setText(f"Current (Exceeded): {current_actual} A")

        self.time_data.append(self.t)
        self.voltage_data.append(voltage_actual)
        self.current_data.append(current_actual)

        t_data = self.time_data
        v_data = self.voltage_data
        c_data = self.current_data

        self.voltage_line.set_data(t_data, v_data)
        self.current_line.set_data(t_data, c_data)

        if len(t_data) > 0:
            self.ax.set_xlim(min(t_data), max(t_data))
        if len(v_data) > 0 and len(c_data) > 0:
            self.ax.set_ylim(min(min(v_data), min(c_data)) - 1, max(max(v_data), max(c_data)) + 1)

        self.canvas.draw()




 
 # for handling Back pressed
        
    def handle_back_pressed(self):
        self.button_A.setIconSize(QSize(40, 40))
        self.label_9.setText("")

        # Check if the current screen is 5, and if so, call reset_process
        if self.screen == 5:
            self.reset_process()  # Call reset_process when navigating away from screen 5

        # Check if the current screen is 5, 6, or 7, and if so, close the serial ports before changing screens
        if self.screen in [5, 6, 7]:
            self.close_serial_ports()  # Close serial ports when navigating away from screens 5, 6, or 7
            self.comboBox.setCurrentIndex(0)  # Clear the comboBox
            self.comboBox_2.setCurrentIndex(0)  # Clear the comboBox_2

        # Determine the new screen based on current screen value
        if self.screen > 1: 
            if self.screen == 6:
                self.screen = 4
            elif self.screen == 4:
                self.screen = 2
            elif self.screen == 7:
                self.screen = 2
            else:
                self.screen -= 1

        print(self.screen)
        self.handle_screen_change(self.screen)


    def handle_app_quit(self):
        self.close()


        
    def close_serial_ports(self):
        # Close the serial ports if they are open
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Power Supply serial port closed.")
        
        if self.ser_2 and self.ser_2.is_open:
            self.ser_2.close()
            print("MCU serial port closed.")

        # Clear the labels to indicate ports are closed
        self.label_12.setText("")
        self.label_9.setText("")

        # Reset serial port objects to None
        self.ser = None
        self.ser_2 = None

     
    # def rx_data(self):
    #     try:
    #         print("Im in rx_data")
    #         self.ser = serial.Serial(port='COM3', baudrate=9600, timeout=10)
    #         self.ser.open()
    #         if self.ser and self.ser.in_waiting > 0:
    #             my_data = self.read_until_delimiter()
    #             ## condition to check formating of data i.e. data[0]=='*'
    #             # Print the received data for debugging
    #             print(f"Data received: {my_data}")
    #             # if data is TEMP
    #             if my_data[1:3]=='T:':
    #                 self.rx_temperature = int(my_data[3:len(my_data)-1])
    #             #if data is FORCE
    #             elif my_data[1:3]=='F:':
    #                 self.rx_force=(int(my_data[3:len(my_data)-1]))
    #                 # print(self.rx_force)
    #             #if data is MODE
    #             elif my_data[1:3]=='M:':
    #                 print("Data received:", my_data)
    #                 if my_data[3:5]=='RD':
    #                     self.mode="READY"
    #                 elif my_data[3:5]=='ST':
    #                     self.mode="PROCESSING"
    #                 elif my_data[3:5]=='PS':
    #                     self.mode="PAUSED"
    #                 elif my_data[3:5]=='HM':
    #                     self.mode="HOMING"
    #             self.label_38.setText("Status:  " + self.mode)
    #         self.handle_screen5()
    #     except serial.SerialException as e:
    #         print(f"SerialException: {e}")  
  
  
 


    def settings(self):
        try:
            # Retrieve current values from input fields
            current_temperature = self.input_14.text()
            current_distance = self.input_12.text()
            current_speed = self.input_13.text()

            # Define protocols
            protocol_temperature = f"*3:1:{current_temperature}#"
            protocol_distance = f"*3:2:{current_distance}#"
            protocol_speed = f"*3:3:{current_speed}#"
            protocol_save = "*3:4:1#"

            # Function to send data and print feedback
            def send_and_log(protocol):
                print(f"Sending protocol to MCU: {protocol}")
                self.tx_data(protocol, port='mcu')
                time.sleep(1)
                mcu_feedback = self.rx_data()
                # time.sleep(1)
                print(f"Received feedback from MCU: {mcu_feedback}")
                return mcu_feedback

            # Send temperature, distance, and speed protocols and log feedback
            send_and_log(protocol_temperature)
            send_and_log(protocol_distance)
            send_and_log(protocol_speed)

            # Send the save protocol and check the feedback
            feedback = send_and_log(protocol_save)

            # Check if the expected feedback is received
            if feedback == "*SET:SAV#":
                # Prepare data for JSON
                settings_data = {
                    "temperature": current_temperature,
                    "distance": current_distance,
                    "speed": current_speed
                }
                print("Data to save:", settings_data)  # Debug print

                # Save the values to a JSON file
                try:
                    with open("settings.json", "w") as settings_file:
                        json.dump(settings_data, settings_file)
                        print("Settings saved successfully.")  # Debug print

                    # Update label_38 to indicate success
                    self.label_38.setText("Saved")
                    self.label_38.setStyleSheet("color:#009900;")
                except Exception as e:
                    print(f"Error saving settings: {e}")  # Debug print

            else:
                # If feedback is not as expected, show an error message
                self.label_23.setText("Error: Failed to save settings.")
                self.label_23.setStyleSheet("color:#FF0000;")

            # Regardless of feedback for the save command, update label_23
            self.label_23.setText("Settings have been processed.")
            self.label_23.setStyleSheet("color:#009900;")

        except Exception as e:
            print(f"Error occurred during settings update: {e}")
            self.label_23.setText("Error: An unexpected error occurred.")
            self.label_23.setStyleSheet("color:#FF0000;")

    # Function to load the settings from the JSON file at startup
    def load_settings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as settings_file:
                    settings_data = json.load(settings_file)
                    self.input_14.setText(settings_data.get("temperature", ""))
                    self.input_12.setText(settings_data.get("distance", ""))
                    self.input_13.setText(settings_data.get("speed", ""))
                    print("Settings loaded successfully:", settings_data)  # Debug print
            except Exception as e:
                print(f"Error loading settings: {e}")  # Debug print



        
    def tx_data(self, data, port='supply'):
        try:
            # Determine the correct serial object based on the port parameter
            ser = self.ser if port == 'supply' else self.ser_2
            
            if ser and ser.is_open:
                print(f"Transmitting data on {ser.port}: {data}")
                
                # Write data to the selected serial port
                ser.write(data.encode())
            else:
                print(f"Serial port for {port} not open.")
        
        except serial.SerialException as e:
            print(f"Serial communication error on {port}: {e}")
        
        except Exception as e:
            print(f"Unexpected error on {port}: {e}")

            
            
    def rx_data(self):
        feedback = None  # Initialize feedback variable
        try:
            # Check for data from the power supply
            if self.ser and self.ser.is_open:
                if self.ser.in_waiting > 0:
                    my_data = self.read_until_delimiter(self.ser)
                    print(f"Data received from supply: {my_data}")
                    self.process_received_data(my_data, port='supply')

            # Check for data from the MCU
            if self.ser_2 and self.ser_2.is_open:
                if self.ser_2.in_waiting > 0:
                    my_data = self.read_until_delimiter(self.ser_2)
                    print(f"Data received from MCU: {my_data}")
                    self.process_received_data(my_data, port='mcu')
                    feedback = my_data  # Store feedback from MCU

        except serial.SerialException as e:
            print(f"SerialException: {e}")
        except Exception as e:
            print(f"Error during data reception: {e}")

        return feedback  # Return the received feedback




    def process_received_data(self, data, port):
        if port == 'supply':
            if "VOLT?" in data:
                voltage_value = float(data.split()[-1])  # Extract voltage
                print(f"Voltage data received: {voltage_value}")
                self.voltage_data.append(voltage_value)  # Store voltage value

            elif "MEAS:CURR?" in data:
                current_value = float(data.split()[-1])  # Extract current
                print(f"Current data received: {current_value}")
                self.current_data.append(current_value)  # Store current value

        elif port == 'mcu':
            # Check for MCU-specific protocols
            if "*PRS:STR#" in data:
                print("MCU acknowledged process start with *PRS:STR#")
            elif "*PRS:CMP#" in data:
                print("MCU acknowledged process complete with *PRS:CMP#")
            elif "*PRS:STP#" in data:
                print("MCU acknowledged process pause with *PRS:STP#")
            
            # Check for motor feedback for manual motor commands
            elif "*MAN:MOT#" in data:
                print("MCU acknowledged motor command with *MAN:MOT#")

            # Check for real-time temperature data (*1:2:temperature_value#)
            elif data.startswith("*1:2:"):
                try:
                    # Extract the temperature value
                    temperature_value = data.split(":")[2].replace("#", "")  # Get the temperature value
                    self.label_37.setText(f" {temperature_value} °C")
                    self.label_47.setText(f" {temperature_value} °C")
                    print(f" {temperature_value} °C")  # Print for confirmation
                except IndexError:
                    print("Error: Invalid temperature data format received.")



    
        # save function here

    # def tx_data(self,data):
    #     try:
    #         print("tx_data")
    #         self.ser.write(data.encode())
    #     except Exception as err:
    #         self.label_9.setText("ERROR: NO SERIAL PORT")
               
    def handle_screen5(self):
        if self.mode == "Complete":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(False)
            self.button_9.setEnabled(False)
            #self.button_A.setEnabled(True)
        elif self.mode == "Start":
            self.button_7.setEnabled(False)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
           # self.button_A.setEnabled(False)
            self.display_plot()
        elif self.mode == "Stop":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(False)
            self.button_9.setEnabled(True)
           # self.button_A.setEnabled(False)
        # elif self.mode == "HOMING":
        #     self.button_7.setEnabled(False)
        #     self.button_8.setEnabled(False)
        #     self.button_9.setEnabled(False)
        #     self.button_A.setEnabled(False)

    # Prevent auto-selection of COM1 when clicking comboBox drop-down
    
    def load_comlist(self):
        # Clear previous items
        self.comboBox.clear()
        self.comboBox.addItem("")  # Add empty item for default selection

        # Get available COM ports
        com_ports = serial.tools.list_ports.comports()

        # Add available COM ports to comboBox
        for port in com_ports:
            self.comboBox.addItem(f"{port.device}")

    def load_comlist_2(self):
        # Clear previous items
        self.comboBox_2.clear()
        self.comboBox_2.addItem("")  # Add empty item for default selection

        # Get available COM ports
        com_ports = serial.tools.list_ports.comports()

        # Add available COM ports to comboBox_2
        for port in com_ports:
            self.comboBox_2.addItem(f"{port.device}")

        

    def read_until_delimiter(self, ser):
        
        # Set delimiter based on the serial port (power supply = '\n', MCU = '#')
        delimiter = b'\n' if ser == self.ser else b'#'
        
        # Collect incoming data
        data = bytearray()
        
        while True:
            if ser.in_waiting > 0:
                byte = ser.read(1)  # Read one byte at a time
                data.extend(byte)
                if byte == delimiter:
                    break  # Exit loop when delimiter is encountered
                    
        # Decode and return the complete data as a string
        return data.decode('utf-8')


    def set_serial(self):
        try:
            # Get the selected port from comboBox (power supply)
            comPort = self.comboBox.currentText()

            # If an empty port is selected, close the serial connection if it's open
            if comPort == "":
                if self.ser and self.ser.is_open:
                    self.ser.close()  # Close the port if it's already open
                    print("Power Supply serial port closed.")
                    self.label_12.setText("")

                return  # Exit the method if no port is selected

            # If a port is selected and not already opened, open the serial connection
            if self.ser is None or not self.ser.is_open or self.ser.port != comPort:
                if self.ser and self.ser.is_open:
                    self.ser.close()  # Close the port if it's already open

                self.ser = serial.Serial(port=comPort, baudrate=9600, timeout=10000)
                print(f"Power Supply serial port opened: {self.ser.port}")
                self.label_12.setText("")
                self.tx_data("*IDN?\n")
                print("Identified")
            else:
                self.label_12.setText("No port selected or already open for power supply")

            # Check for errors between the selected ports (power supply and MCU)
            self.check_ports_and_error()

        except Exception as e:
            # Handle any errors during serial port opening
            self.label_12.setText(f"Error: {e}")

    def handle_comboBox_2_change(self):
        try:
            # Get the selected port from comboBox_2 (MCU)
            comPort2 = self.comboBox_2.currentText()

            # If an empty port is selected, close the serial connection if it's open
            if comPort2 == "":
                if self.ser_2 and self.ser_2.is_open:
                    self.ser_2.close()  # Close the port if it's already open
                    print("MCU serial port closed.")
                    self.label_9.setText("")

                return  # Exit the method if no port is selected

            # If a port is selected and not already opened, open the serial connection
            if self.ser_2 is None or not self.ser_2.is_open or self.ser_2.port != comPort2:
                if self.ser_2 and self.ser_2.is_open:
                    self.ser_2.close()  # Close the port if it's already open

                self.ser_2 = serial.Serial(port=comPort2, baudrate=9600, timeout=10000)
                print(f"MCU serial port opened: {self.ser_2.port}")
                self.label_9.setText("")
            else:
                self.label_9.setText("No port selected or already open for MCU")

            # Check for errors between the selected ports (power supply and MCU)
            self.check_ports_and_error()

        except Exception as e:
            # Handle any errors during serial port opening
            self.label_9.setText(f"Error: {e}")



    def check_ports_and_error(self):
        # Check if the power supply or MCU port is empty
        if self.comboBox.currentText() == "" or self.comboBox_2.currentText() == "":
            # Clear error messages if either port is empty
            self.label_12.setText("")
            self.label_9.setText("")
            return  # Exit the method as there's no conflict

        # Ensure the selected ports for power supply and MCU are not the same
        if self.ser and self.ser_2 and self.ser.port == self.ser_2.port:
            # Display error message for both labels
            self.label_12.setText("Port Error")
            self.label_9.setText("Port Error")

            # Close both serial ports to prevent communication errors
            if self.ser.is_open:
                self.ser.close()
            if self.ser_2.is_open:
                self.ser_2.close()
        else:
            # If the ports are different, clear the error messages
            self.label_12.setText("")
            self.label_9.setText("")



            
            
    def handle_manual(self):
        print("on screen 6")
        self.init_screen_6()


  

    def motor_forward_pressed(self):
        # Set the pressed icon when the button is clicked
        print("Motor forward pressed")
        self.button_13.setIcon(QIcon(base_path + "/rsc/forward_pressed.png"))  # Set forward pressed icon

        # Send the command to move forward
        cmd = "*2:2:0#"
        print(f"Sending command: {cmd}")
        self.tx_data(cmd, port='mcu')  # Send the command to the MCU

        # Receive and validate MCU feedback
        feedback = self.rx_data()
        if feedback == "*MAN:MOT#":
            print("Feedback received: Motor forward command successful")
        else:
            print(f"Unexpected feedback from MCU: {feedback}")
            self.label_23.setText("Error: Failed to start motor forward.")
            self.label_23.setStyleSheet("color:#FF0000;")

        # Use QTimer to set the normal forward icon after a short delay
        QTimer.singleShot(200, lambda: self.button_13.setIcon(QIcon(base_path + "/rsc/forward.png")))


    def motor_reverse_pressed(self):
        # Set the pressed icon when the button is clicked
        print("Motor reverse pressed")
        self.button_14.setIcon(QIcon(base_path + "/rsc/reverse_pressed.png"))  # Set reverse pressed icon

        # Send the command to reverse
        cmd = "*2:2:1#"
        print(f"Sending command: {cmd}")
        self.tx_data(cmd, port='mcu')  # Send the command to the MCU

        # Receive and validate MCU feedback
        feedback = self.rx_data()
        if feedback == "*MAN:MOT#":
            print("Feedback received: Motor reverse command successful")
        else:
            print(f"Unexpected feedback from MCU: {feedback}")
            self.label_23.setText("Error: Failed to start motor reverse.")
            self.label_23.setStyleSheet("color:#FF0000;")

        # Use QTimer to set the normal reverse icon after a short delay
        QTimer.singleShot(200, lambda: self.button_14.setIcon(QIcon(base_path + "/rsc/reverse.png")))









 #   def motor_left_pressed(self):
    #     print("motor pressed")
    #     cmd = "*2:2:0#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())


    # def motor_left_released(self):
    #     print("motor released")
    #     cmd = "*2:2:0#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())


    # def motor_right_pressed(self):
    #     print("motor pressed")
    #     cmd = "*2:2:1#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())

    # def motor_right_released(self):
    #     print("motor released")
    #     cmd = "*2:2:1#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())

    def handle_heater(self):
        self.heater = not self.heater  # Toggle the heater state
        if self.heater:
            cmd = "*2:1:1#"  # Command to turn the heater ON
            print(f"Sending command: {cmd}")
            self.tx_data(cmd, port='mcu')  # Send the command to the MCU
            
            time.sleep(0.1)  # Small delay to allow for feedback
            feedback = self.rx_data()  # Check for feedback
            print(f"Expected feedback: *MAN:HTR#")
            if feedback:
                print(f"Actual feedback: {feedback}")
            else:
                print("No feedback received.")
            
            # Update button state
            self.button_15.setText("")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater_pressed.png"))
        else:
            cmd = "*2:1:0#"  # Command to turn the heater OFF
            print(f"Sending command: {cmd}")
            self.tx_data(cmd, port='mcu')  # Send the command to the MCU
            
            time.sleep(0.1)  # Small delay to allow for feedback
            feedback = self.rx_data()  # Check for feedback
            print(f"Expected feedback: *MAN:HTR#")
            if feedback:
                print(f"Actual feedback: {feedback}")
            else:
                print("No feedback received.")
            
            # Update button state
            self.button_15.setText("")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))
        
        print("Heater state:", "ON" if self.heater else "OFF")



    # def valve_1_pressed(self):
    #     print("valve 1 pressed")
    #     cmd = "*MV1SR#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())
    
    # def valve_1_released(self):
    #     print("valve 1 relesead")
    #     cmd = "*MV1SP#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())

    # def valve_2_pressed(self):
    #     print("valve 2 pressed")
    #     cmd = "*MV2SR#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())
    
    # def valve_2_released(self):
    #     print("valve 2 relesead")
    #     cmd = "*MV2SP#"
    #     print(cmd)
    #     self.tx_data(cmd.encode())
    


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    # window.showFullScreen()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()