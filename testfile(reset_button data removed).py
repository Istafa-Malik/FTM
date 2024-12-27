import os, sys, csv, random
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QMessageBox,QLineEdit,QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QImage, QIntValidator, QDoubleValidator, QIcon,QFont
from PyQt5.QtCore import Qt, QTimer, QSize, QDateTime
from PyQt5.QtWidgets import QFileDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import make_interp_spline
from datetime import datetime
import serial.tools.list_ports
import serial 
import subprocess
import ctypes
from mainkb import VirtualKeyboard
from PIL import Image, ImageOps
import cv2
import numpy as np
import sounddevice as sd
import pandas as pd
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
#TX_COMPLETE="*1:1:0:{}:{}#"        #expected from PC
#RX_COMPLETE="*PRC:CP#"             # sent from PC
TX_PAUSE="*1:0:1:{}:{}:{}#"        #send from pc
RX_PAUSE="*PRC:SP#"                #expected from machine
TX_RESET="*1:0 :0:{}:{}:{}#"       #sent from pc
RX_RESET="*PRC:RR#"                #expected from machine
RX_READY="*PRS:RED#"                #expected from machine when ready
#----------------------VALUES----------------------
RX_TEMPERATURE="*TEP:xxx#"
RX_PRESSURE="*1:2:Pressure#"
#--------------------MANUAL PAGE-------------------
# TX_MOTOR_FORWARD_START="*2:4:1:1#"
# TX_MOTOR_FORWARD_STOP="*2:4:2:1#"
# TX_MOTOR_BACKWARD_START="*2:4:1:2#"
# TX_MOTOR_BACKWARD_STOP="*2:4:2:2#"
# TX_VALVE1_OPEN="*2:5:2#"
# TX_VALVE1_CLOSE="*2:5:1#"
# TX_VALVE2_OPEN="*2:6:1#"
# TX_VALVE2_CLOSE="*2:6:2#"
TX_PUMP_FILL="*2:2:0#"
TX_PUMP_EMPTY="*2:2:1#"
TX_HEATER_START="*2:1:1#"
TX_HEATER_STOP="*2:1:0#"
#=======================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui_ftm.ui', self)

        self.keyboard = None
        # self.keyboard_enabled = False
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
                # Initialization for first graph (feed_graph)
        # Initialization for first graph (feed_graph)
        self.feed_graph = self.findChild(QWidget, "feed_graph")  # Get the feed_graph widget
        self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.feed_graph.setLayout(layout)

        # Set up axis labels and grids for the first plot
        self.ax.set(xlabel='Time (min)', ylabel='Force')
        self.ax.grid()
        self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5))  # Placeholder for the amplitude line

        # Initialization for second graph (feed_graph_3)
        self.feed_graph_3 = self.findChild(QWidget, "feed_graph_3")  # Get the feed_graph_3 widget
        self.fig2, self.ax2 = plt.subplots(figsize=(4.25, 4.125), dpi=80)
        self.canvas2 = FigureCanvas(self.fig2)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.canvas2)
        self.feed_graph_3.setLayout(layout2)

        # Set up axis labels and grids for the second plot
        self.ax2.set(xlabel='Time (min)', ylabel='Force')
        self.ax2.grid()

        # Create a secondary y-axis for sound count using twinx() on the same graph
        # self.ax2_sound = self.ax2.twinx()  # Secondary y-axis for sound count
        # self.ax2_sound.set_ylabel('Sound Count')


        # Assuming you already have this QLabel for time display
        # self.label_41 is the QLabel in Qt Designer for displaying time
        # self.label_41.setText("0d 00:00:00")  # Initialize with default value
        # for widget in self.findChildren(QWidget):
        #     widget.setFont(font_12)
        #     widget.setFocusPolicy(Qt.NoFocus)
      
            # Connect textChanged signal to check_file_name
        #self.input_8.textChanged.connect(self.check_file_name)    
        self.input_1.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        # self.input_1.focusInEvent = self.create_focus_in_handler(self.input_1.focusInEvent)
        # self.input_2.focusInEvent = self.create_focus_in_handler(self.input_2.focusInEvent)
        self.input_2.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_3.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_4.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_5.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_6.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_7.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.input_8.setFocusPolicy(Qt.FocusPolicy.ClickFocus) #for entering file name
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
        self.t = 0
        self.int_validator = QIntValidator(self)
        self.process_config = []
        # self.time_data = []
        # self.pressure_data = []
        # self.rx_temperature = 0
        # self.rx_pressure = 0
        # self.ser = None
        # self.pump=False
        # self.heater=False
        # self.is_filling = True  # Initial state: filling the tank
        # #self.valve2=False
        # #self.disable_osk()
        # self.camera = cv2.VideoCapture(0)
        #  #Sound generation counter
        # self.sound_count = 0 # count for sound generation
        
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.display_cam)
        # # self.timer.timeout.connect(self.display_cam2)
        # self.timer2 = QTimer()
        # self.timer2.timeout.connect(self.rx_data)
        
        # self.button_1.clicked.connect(self.handle_verify_login)
        # self.button_A.pressed.connect(self.handle_button_A_pressed)
        self.button_A.clicked.connect(self.handle_back_pressed)
        self.button_2.clicked.connect(lambda: self.handle_screen_change(2))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        # self.button_4.clicked.connect(self.handle_create_config)
        # self.button_5.clicked.connect(lambda: self.handle_screen_change(5))
        # self.button_6.clicked.connect(self.populate_configlist)
        # self.button_7.clicked.connect(self.start_process)
        self.button_8.clicked.connect(self.pause_process)
        # self.button_9.clicked.connect(self.reset_process)
        # self.button_10.clicked.connect(self.handle_delete_configuration)
        # self.button_11.clicked.connect(self.handle_delete)
        # self.button_12.clicked.connect(self.handle_manual)
        # self.button_13.pressed.connect(self.motor_left_pressed) # motor left
        # self.button_13.released.connect(self.motor_left_released) # motor left
        # self.button_14.pressed.connect(self.motor_right_pressed)  # motor right
        # self.button_14.released.connect(self.motor_right_released)  # motor right
        # self.button_15.clicked.connect(self.handle_heater)  # heater on/off
        # self.button_16.clicked.connect(self.handle_pump)  # Pump   fill/empty
        #self.button_18.clicked.connect(self.complete_process)  # valve 2  on/off 
        #self.button_18.clicked.connect(self.open_csv_files)
        # self.button_19.clicked.connect(lambda: self.handle_screen_change(7))
        self.button_20.clicked.connect(self.load_csv_data)
        # self.configlist.itemClicked.connect(self.load_config)
        # self.input_4.setValidator(self.int_validator)
        # self.input_5.setValidator(self.int_validator)
        # self.input_6.setValidator(self.int_validator)
        # self.input_7.setValidator(self.int_validator)
        self.showPopup2 = self.comboBox.showPopup 
        self.comboBox.showPopup= self.load_comlist
        self.load_comlist()
        self.comboBox.currentIndexChanged.connect(self.set_serial)
       # self.closeButton.clicked.connect(self.close)
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

       # virtual keboard
    
    # def show_virtual_keyboard(self, input_field, event=None):
    #     # Check if the keyboard exists and is visible before proceeding
    #     if self.keyboard is None or not self.keyboard.isVisible():
    #         # If no keyboard is open, create a new one
    #         self.keyboard = VirtualKeyboard(input_field, self)
    #         self.keyboard.finished.connect(self.on_keyboard_closed)  # Reset the flag when the keyboard closes
    #         self.keyboard.show()
    #     else:
    #         # If a keyboard is already open, change the focused input field
    #         self.keyboard.input_field = input_field

    # def handle_focus_event(self, event):
    #     # Ensure that the keyboard opens only for the clicked input field
    #     self.show_virtual_keyboard(self.sender(), event)
    #     QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

    # def on_keyboard_closed(self):
    #     # Safely reset the keyboard reference when it's closed
    #     self.keyboard = None

    def handle_screen_change(self,value):

         # Close the virtual keyboard if it is open when changing screens
        # if self.keyboard is not None and self.keyboard.isVisible():
        #     self.keyboard.close_keyboard()

        for widget in self.findChildren(QtWidgets.QPushButton):
            widget.setFocusPolicy(Qt.NoFocus)

        if(value == 1): # Menu Screen
            self.screen = 1
            self.comboBox.hide()
            self.comboBox.setDisabled(True)
            self.button_A.hide()
            self.init_screen_1()
        elif(value == 2): # Process Screen
            self.screen = 2
            self.comboBox.hide()
            self.button_A.show()
            self.init_screen_2()
        # elif(value == 3): # Create Config Screen
        #     self.screen = 3
        #     self.comboBox.hide()
        #     self.init_screen_3()
        # elif(value == 4): # Load Config Screen
        #     self.screen = 4
        #     self.comboBox.show()
        #     self.comboBox.setDisabled(False)
        #     self.init_screen_4(delete=False)
        # elif(value == 5): # Process Screen
        #     self.screen = 5
        #     self.comboBox.show()
        #     self.comboBox.setDisabled(False)
        #     self.init_screen_5()
        # elif(value == 6): # Process Screen
        #     self.screen = 6
        #     self.comboBox.show()
        #     self.comboBox.setDisabled(False)
        #     self.button_A.show()
        #     self.button_A.setEnabled(True)
        #     self.init_screen_6()
        elif(value == 3): # static graph screen
            self.screen = 3
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_3()
            # button_A represents back button (<)
      

    def handle_button_A_pressed(self):
        self.button_A.setIconSize(QSize(36, 36))
# for displaying login screen only
    # def init_screen_1(self):
    #     self.screen = 1
    #     self.screen_2.hide()
    #     self.screen_3.hide()
    #     self.screen_4.hide()
    #     self.screen_5.hide()
    #     self.screen_6.hide()
    #     self.screen_7.hide()
    #     self.screen_1.show()
    #     self.setStyleSheet("background-color:rgb(250,250,250);")
    #     self.label_A.setPixmap(QPixmap(base_path+"/rsc/rsc2.png"))
    #     self.label_6.hide()

    #       # Connect input_1 and input_2 to trigger virtual keyboard when clicked
    #     self.input_1.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_1, event)
    #     self.input_2.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_2, event)
    
    # def handle_focus_event(self, event):
    #     self.show_virtual_keyboard(event)
    #     QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

# for displaying menu screen only   
    def init_screen_1(self):
        self.screen = 1
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap())
        self.label_A.setText("Main Menu")
        self.screen_1.hide()
        self.screen_3.hide()
        # self.screen_4.hide()
        # self.screen_5.hide()
        # self.screen_6.hide()
        # self.screen_7.hide()
        self.screen_1.show()
# for displaying create config screen only         
    # def init_screen_3(self):
    #     self.screen = 3
    #     self.label_A.setText("Create Configuration")
    #     self.screen_1.hide()
    #     self.screen_2.hide()
    #     self.screen_4.hide()
    #     self.screen_5.hide()
    #     self.screen_6.hide()
    #     self.screen_7.hide()
    #     self.screen_3.show()
    #     self.setStyleSheet("background-color:rgb(250,250,250);")
    #     self.label_23.setStyleSheet("color:#FF0000;")
    #     self.label_23.setText("")
    #     self.input_3.clear()
    #     self.input_4.clear()
    #     self.input_5.clear()
    #     self.input_6.clear()
    #     self.input_7.clear()

    #     self.input_3.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_3, event)
    #     self.input_4.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_4, event)
    #     self.input_5.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_5, event)
    #     self.input_6.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_6, event)
    #     self.input_7.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_7, event)
        
    # def handle_focus_event(self, event):
    #     self.show_virtual_keyboard(event)
    #     QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

# for the display of delete config screen  ,load config screen in which we will load data and press the auto button to go to screen_5
    # def init_screen_4(self,delete):
    #     self.screen = 4
    #     if(delete):
    #         self.label_A.setText("Delete Configuration")
    #         self.button_5.hide()
    #         self.button_12.hide()
    #         self.button_11.show()
    #         self.button_11.setEnabled(False)
    #     else:
    #         self.label_A.setText("Load Configuration")
    #         self.button_5.setEnabled(False)
    #         self.button_11.hide()
    #         self.button_12.show()
    #         self.button_5.show()

    #     self.screen_1.hide()
    #     self.screen_2.hide()
    #     self.screen_3.hide()
    #     self.screen_5.hide()
    #     self.screen_6.hide()
    #     self.screen_7.hide()
    #     self.screen_4.show()
    #     self.setStyleSheet("background-color:rgb(250,250,250);")
    #     self.configlist.hide()
    #     self.label_29.setText("")
    #     self.label_30.setText("")
    #     self.label_31.setText("")
    #     self.label_32.setText("")
    #     self.label_33.setText("")
    #     self.input_8.clear()

    #     self.input_8.focusInEvent = lambda event: self.show_virtual_keyboard(self.input_8, event)
    # def handle_focus_event(self, event):
    #     self.show_virtual_keyboard(event)
    #     QLineEdit.focusInEvent(self.sender(), event)  # Call the original focus event

    # # def closeEvent(self, event):
    # #     # Call the parent close event or add extra logic if needed
    # #     super().closeEvent(event)
    # def close_keyboard(self): 
    #         # Check if the virtual keyboard is open and close it
    #     if self.keyboard is not None and self.keyboard.isVisible():
    #         self.keyboard.close()
    #         print("Virtual keyboard closed")
    #for the display of creen_5 where we can see the real-time graph and webcam
    def init_screen_2(self):
        self.screen = 2
        
        # self.label_A.setText("Auto Operation")
        self.screen_1.hide()
        self.screen_2.hide()
        # self.screen_3.hide()
        # self.screen_4.hide()
        # self.screen_6.hide()
        # self.screen_7.hide()
        self.screen_2.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        # shadow1=QGraphicsDropShadowEffect()
        # shadow1.setBlurRadius(30)
        # shadow1.setOffset(0,5)
        # self.button_7.setGraphicsEffect(shadow1)
# for the siplay of screen_6 which appears when we press manual button on screen_4 it will take us to screen_6
    # def init_screen_6(self):
    #     self.screen = 6
    #     self.label_A.setText("Manual Operation")
    #     self.screen_1.hide()
    #     self.screen_2.hide()
    #     self.screen_3.hide()
    #     self.screen_4.hide()
    #     self.screen_5.hide()
    #     self.screen_7.hide()
    #     self.screen_6.show()
    #     # self.button_13.setStyleSheet('background-color:transparent;')
    #     # self.button_13.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))
    #     # self.button_13.setIconSize(QSize(100, 100)) 
    #     # self.button_14.setStyleSheet('background-color:transparent;')
    #     # self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
    #     # self.button_14.setIconSize(QSize(100, 100)) 
    #     self.button_15.setStyleSheet("background-color:transparent;")
    #     self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))
    #     self.button_15.setIconSize(QSize(100, 100)) 
    #     self.button_16.setStyleSheet("background-color:transparent;")
    #     self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
    #     self.button_16.setIconSize(QSize(100, 100)) 
    #     # self.button_17.setStyleSheet("background-color:transparent;")
    #     # self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
    #     # self.button_17.setIconSize(QSize(100, 100)) 
    #     # self.label_10.setText("Clamp 2 OFF")
    #     # self.label_7.setText("Clamp 1 OFF")
    #     self.setStyleSheet("background-color:rgb(250,250,250);")
    #     print("screen 6")
    #     self.timer.start()
    #     self.timer2.start()
    #     self.pump=False
    #     self.heater=False
        # self.valve1=False
        # self.valve2=False
# for the display of screen_7 which appears when the button "View Process Graph" is pressed that is present on screen_2
    def init_screen_3(self):
        self.screen = 3
        self.screen_1.hide()
        self.screen_2.hide()
        # self.screen_3.hide()
        # self.screen_4.hide()
        # self.screen_6.hide()
        # self.screen_5.hide()
        self.screen_3.show()
        print("screen 7")
       
    # Connect button_20 to the CSV loading function
        #self.button_20.clicked.connect(self.load_csv_data)

    # def close_keyboard(self):
    #      # Check if the virtual keyboard is open and close it
    #             if self.keyboard is not None and self.keyboard.isVisible():
    #                 self.keyboard.close()
    #                 print("Virtual keyboard closed")

#     def populate_configlist(self):
#         if self.configlist.isVisible():
#             self.configlist.hide()
#         else:
#             self.configlist.show()
#             self.configlist.clear()
#             if os.path.exists('ConfigFile.csv'):
#                 with open('ConfigFile.csv', 'r') as file:
#                     reader = csv.reader(file)
#                     next(reader, None) 
#                     for row in reader:
#                         if row: 
#                             self.configlist.addItem(row[0])  
#             list_height = (self.configlist.count()*42) + 2
#             if(list_height>350): list_height = 350
#             self.configlist.setFixedHeight(list_height)
# # Function to load the configuration in order to start the process
#     def load_config(self):
#         selected_items_list = self.configlist.selectedItems()
#         if selected_items_list:
#             selected_item = selected_items_list[0].text()
#             print(f"Selected item text: {selected_item}")
# # This will store the laoded configuration data
#             if os.path.exists('ConfigFile.csv'):
#                 with open('ConfigFile.csv', 'r') as file:
#                     reader = csv.reader(file)
#                     next(reader, None)
#                     for row in reader:
#                         if row[0] == selected_item:
#                             self.process_config = row
#                             break
#             print("Process Config:", self.process_config)
#             self.label_29.setText(self.process_config[0])
#             self.label_30.setText(self.process_config[1])
#             self.label_31.setText(self.process_config[2])
#             self.label_32.setText(self.process_config[3])
#             self.label_33.setText(self.process_config[4])
#             self.button_5.setEnabled(True)
#             self.button_11.setEnabled(True)
            
#     def handle_verify_login(self):
#         if(self.input_1.text() == "" and self.input_2.text() == ""): # within invereted commas use can enter login id or password
#             self.role = ""
#             self.button_3.show()
#             self.button_10.show()   
            
#             self.handle_screen_change(2)
            
#         elif(self.input_1.text() == "operator" and self.input_2.text() == "operator"):
#             self.role = "operator"
#             self.button_3.hide()
#             self.button_10.hide()
            
#             self.handle_screen_change(2)
#         else:
#             self.label_6.show()
#             self.label_6.setStyleSheet("color:rgb(255,0,0); background:white;")

#     def handle_create_config(self):
        
#         data = [
#             self.input_3.text(),
#             self.input_4.text(),
#             self.input_5.text(),
#             self.input_6.text(),
#             self.input_7.text()
#         ]

#         if any(not field for field in data):
#             self.label_23.setText("Error: All fields must be filled")
#             self.label_23.setStyleSheet("color:#FF0000;")
#             return
#         else:
#             file_exists = os.path.exists('ConfigFile.csv')
            
#             if file_exists:
#                 with open('ConfigFile.csv', 'r') as file:
#                     reader = csv.reader(file)
#                     next(reader, None)
#                     for row in reader:
#                         if self.input_3.text() == row[0]:  # Check if input_3 text exists in the first column
#                             self.label_23.setText("Error: Configuration Name already exists")
#                             self.label_23.setStyleSheet("color:#FF0000;")
#                             return
                        
#             with open('ConfigFile.csv', 'a', newline='') as file:
#                 writer = csv.writer(file)
#                 if not file_exists:
#                     writer.writerow(['ConfigName', 'Frequency', 'Time', 'Temperature', 'Amplitude'])  # Replace with appropriate header names
#                 writer.writerow(data)
#                 self.label_23.setText("Configuration has been saved successfully")
#                 self.label_23.setStyleSheet("color:#009900;")

#     def handle_delete_configuration(self):
#         self.init_screen_4(True)

#     def handle_delete(self):
#         reply=QMessageBox.question(self, 'Confirm', 'Are you sure you want to delete this?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
#         if reply == QMessageBox.Yes:
#             if os.path.exists('ConfigFile.csv'):
#                 with open('ConfigFile.csv', 'r') as file:
#                     reader = csv.reader(file)
#                     rows = list(reader)
#                 with open('ConfigFile.csv', 'w', newline='') as file:
#                     writer = csv.writer(file)
#                     for row in rows:
#                         if row[0] != self.process_config[0]:
#                             print(self.process_config)
#                             writer.writerow(row)
#                             self.init_screen_2()
#         else:
#             print("Action canceled")

#         print("delete pressed")

    # def start_process(self):
    #     self.timer.start(1)

    #     # Retrieve frequency, time, and amplitude from user input
    #     try:
    #         self.frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
    #         self.time_duration = float(self.label_31.text())  # Assuming label_31 holds time value
    #         self.amplitude = float(self.label_33.text())  # Assuming label_33 holds amplitude value
    #         print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
    #     except ValueError:
    #         print("Invalid frequency, time, or amplitude value")
    #         return

    #     # Retrieve the file name entered in input_8
    #     entered_name = self.input_8.text().strip()
        
    #     # Ensure the file name is not empty
    #     if not entered_name:
    #         QMessageBox.warning(self, 'Error', 'Please enter a file name.')
    #         return

    #     # Define the CSV file path based on entered file name
    #     self.entered_name = entered_name
    #     csv_file = f'{entered_name}_data_log.csv'

    #     # Check if the file already exists
    #     if os.path.isfile(csv_file):
    #         QMessageBox.warning(self, 'Error', 'This file name already exists. Please enter a unique name.')
    #         return

    #     # Set the label_56 to display the file name
    #     self.label_56.setText(entered_name)

    #     # Initialize an array to store data
    #     self.sound_data = []  # to store sound data temporarily
    #     self.max_limit = 100  # set the array size limit to 100

    #     # Open the CSV file for writing data
    #     file_exists = os.path.isfile(csv_file)
    #     with open(csv_file, mode='a', newline='') as file:
    #         fieldnames = ['Time', 'Amplitude', 'Sound Count']
    #         writer = csv.DictWriter(file, fieldnames=fieldnames)
    #         if not file_exists:
    #             writer.writeheader()  # Write header if it's a new file

    #     # Start the sound generation timer to repeat every 1 second
    #     self.sound_timer.start(1000)  # Start timer for every 1000 ms (1 second)
    #     self.generate_sound(self.frequency, self.amplitude)
    #     self.timer2.start()

    #     # Start the process timer
    #     self.process_start_time = QDateTime.currentDateTime()  # Record the current date and time
    #     self.timer_process.start(1000)  # Update every second

    #     if self.mode == "READY":
    #         self.label_38.setText("PROCESSING")
    #         if self.feed_graph.layout() is None:
    #             print("Creating new layout")
    #             self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
    #             self.canvas = FigureCanvas(self.fig)
    #             layout = QVBoxLayout()
    #             layout.addWidget(self.canvas)
    #             self.feed_graph.setLayout(layout)

    #         # Set the graph axis labels
    #         self.ax.set(xlabel='Time (s)', ylabel='Amplitude (m)')
    #         self.ax.grid()

    #         # Initialize an empty plot line for amplitude
    #         self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5), label='Amplitude')
            
    #         # Optionally, you can set a secondary y-axis for frequency
    #         self.ax_freq = self.ax.twinx()  # Create a secondary y-axis
    #         self.ax_freq.set_ylabel('Frequency (Hz)')  # Label for frequency
    #         self.ax_freq.set_ylim(0, self.frequency * 2)  # Adjust limits if needed

    #         # Set initial time
    #         self.t = 0

    #         # Initialize data lists
    #         self.time_data = []
    #         self.sine_data = []

    #         # Draw the initial empty canvas
    #         self.canvas.draw()
            
    #         # Start the update timer as usual for updating the plot
    #     if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
    #         self.update_timer = QTimer()
    #         self.update_timer.timeout.connect(self.display_plot)
    #         self.update_timer.start(1000)  # Update the plot every 1 second

    #         self.store_real_time_data(csv_file)
    #         self.display_plot()
    def start_process(self):
        if self.mode == "PAUSED":
            self.button_7.setText("RESUME")
            self.button_7.setDisabled(True)
            print("Resuming process.")
            self.timer.start(1)
            # self.sound_timer.start(1000)
            self.timer_process.start(1000)
            self.label_38.setText("PROCESSING")
            self.mode = "RUNNING"

            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.display_plot)
                self.update_timer.start(1000)

            return

        # Initialize for the first time
        self.timer.start(1)

        try:
            self.force = float(self.label_30.text())  # Assuming label_30 holds force value
            self.time_duration = float(self.label_31.text())
            print(f"Force: {self.force}, Time: {self.time_duration}")
        except ValueError:
            print("Invalid force or time value")
            return

        entered_name = self.input_8.text().strip()
        if not entered_name:
            QMessageBox.warning(self, 'Error', 'Please enter a file name.')
            return

        self.entered_name = entered_name
        csv_file = f'{entered_name}_data_log.csv'

        self.label_56.setText(entered_name)
        self.data = []  
        self.max_limit = 100  

        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            fieldnames = ['Time', 'Force']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

        self.sound_timer.start(1000)  
        self.timer2.start()

        self.process_start_time = QDateTime.currentDateTime()  
        self.timer_process.start(1000)  

        if self.mode == "READY":
            self.label_38.setText("PROCESSING")
            if self.feed_graph.layout() is None:
                print("Creating new layout")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)

                # Add a horizontal scroll bar
                self.scrollbar = QScrollBar()
                self.scrollbar.setOrientation(Qt.Horizontal)
                self.scrollbar.setMinimum(0)
                self.scrollbar.setMaximum(0)  # No scrolling initially
                self.scrollbar.valueChanged.connect(self.scroll_graph)

                layout.addWidget(self.scrollbar)
                self.feed_graph.setLayout(layout)

            self.ax.set(xlabel='Time (s)', ylabel='Force (N)')
            self.ax.grid()
            self.line, = self.ax.plot([], [], color='blue', label='Force')
            self.t = 0
            self.time_data = []
            self.force_data = []
            self.canvas.draw()

        if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.display_plot)
            self.update_timer.start(1000)

        self.store_real_time_data(csv_file)
        self.display_plot()


    # def start_process(self):
    #         #self.button_7.setText("START")
    #     if self.mode == "PAUSED":
    #         self.button_7.setText("RESUME")
    #         self.button_7.setDisabled(True) # once button_7 pessed once it will get disabled until the process won't get paused again
    #         # Resume the process from paused state
    #         print("Resuming process.")
    #         self.timer.start(1)
    #         self.sound_timer.start(1000)  # Resume sound generation
    #         self.timer_process.start(1000)  # Resume the process timer
    #         self.label_38.setText("PROCESSING")
    #         self.mode = "RUNNING"  # Set mode back to running
    #         # Change the text of button_7 to "RESUME"

    #         # Resume the plot update timer
    #         if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
    #             self.update_timer = QTimer()
    #             self.update_timer.timeout.connect(self.display_plot)
    #             self.update_timer.start(1000)

    #         return  # Skip the rest of the function, as we are resuming
    #      # If the process is not paused, it means we are starting it for the first time
    #             #self.button_7.setText("START")  # Set the button text to "START"
    #             #self.button_7.setDisabled(True)  # Disable button_7 after the process starts

    #     # If the process is not paused, it means we are starting it for the first time
    #     self.timer.start(1)

    #     # Retrieve frequency, time, and amplitude from user input
    #     try:
    #         self.frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
    #         self.time_duration = float(self.label_31.text())  # Assuming label_31 holds time value
    #         self.amplitude = float(self.label_33.text())  # Assuming label_33 holds amplitude value
    #         print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
    #     except ValueError:
    #         print("Invalid frequency, time, or amplitude value")
    #         return

    #     # Retrieve the file name entered in input_8
    #     entered_name = self.input_8.text().strip()

    #     # Ensure the file name is not empty
    #     if not entered_name:
    #         QMessageBox.warning(self, 'Error', 'Please enter a file name.')
    #         return

    #     # Define the CSV file path based on entered file name
    #     self.entered_name = entered_name
    #     csv_file = f'{entered_name}_data_log.csv'

    #     # Check if the file already exists
    #     # if os.path.isfile(csv_file):
    #     #      QMessageBox.warning(self, 'Error', 'This file name already exists. Please enter a unique name.')
    #     #      return

    #     # Set the label_56 to display the file name
    #     self.label_56.setText(entered_name)

    #     # Initialize an array to store data
    #     self.sound_data = []  # to store sound data temporarily
    #     self.max_limit = 100  # set the array size limit to 100

    #     # Open the CSV file for writing data
    #     file_exists = os.path.isfile(csv_file)
    #     with open(csv_file, mode='a', newline='') as file:
    #         fieldnames = ['Time', 'Amplitude', 'Sound Count']
    #         writer = csv.DictWriter(file, fieldnames=fieldnames)
    #         if not file_exists:
    #             writer.writeheader()  # Write header if it's a new file

    #     # Start the sound generation timer to repeat every 1 second
    #     self.sound_timer.start(1000)  # Start timer for every 1000 ms (1 second)
    #     self.generate_sound(self.frequency, self.amplitude)
    #     self.timer2.start()

    #     # Start the process timer
    #     self.process_start_time = QDateTime.currentDateTime()  # Record the current date and time
    #     self.timer_process.start(1000)  # Update every second

    #     # Initial setup when starting the process
    #     if self.mode == "READY":
    #         self.label_38.setText("PROCESSING")
    #         if self.feed_graph.layout() is None:
    #             print("Creating new layout")
    #             self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
    #             self.canvas = FigureCanvas(self.fig)
    #             layout = QVBoxLayout()
    #             layout.addWidget(self.canvas)
    #             self.feed_graph.setLayout(layout)

    #         # Set the graph axis labels
    #         self.ax.set(xlabel='Time (s)', ylabel='Amplitude (m)')
    #         self.ax.grid()

    #         # Initialize an empty plot line for amplitude
    #         self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5), label='Amplitude')

    #         # Optionally, you can set a secondary y-axis for frequency
    #         self.ax_freq = self.ax.twinx()  # Create a secondary y-axis
    #         self.ax_freq.set_ylabel('Frequency (Hz)')  # Label for frequency
    #         self.ax_freq.set_ylim(0, self.frequency * 2)  # Adjust limits if needed

    #         # Set initial time
    #         self.t = 0

    #         # Initialize data lists
    #         self.time_data = []
    #         self.sine_data = []

    #         # Draw the initial empty canvas
    #         self.canvas.draw()

    #         # Start the update timer as usual for updating the plot
    #     if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
    #         self.update_timer = QTimer()
    #         self.update_timer.timeout.connect(self.display_plot)
    #         self.update_timer.start(1000)  # Update the plot every 1 second

    #     # Store real-time data and display the plot
    #     self.store_real_time_data(csv_file)
    #     self.display_plot()


    # def start_process(self):
    #      self.timer.start(1)

    # #     # Retrieve frequency and amplitude from user input
    #     try:
    #        frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
    #        time = float(self.label_31.text())
    #        amplitude = float(self.label_33.text())  # Assuming label_31 holds amplitude value
    #     except ValueError:
    #          print("Invalid frequency or amplitude value")
    #          return

    #      # Generate and play the sound based on frequency and amplitude
    #       self.generate_sound(frequency, amplitude)
    #      self.timer2.start()

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
    # def check_file_name(self):
        # entered_name = self.input_8.text().strip()

        # # If no name is entered, return early
        # if not entered_name:
        #     return

        # # Define the CSV file path based on entered name
        # self.entered_name = entered_name
        # csv_file = f'{entered_name}_data_log.csv'

        # # Check if the file already exists
        # if os.path.isfile(csv_file):
        #     # Display a dialog box indicating the file exists
        #     QMessageBox.warning(self, 'File Name Exists', 'This file name already exists. Please choose a different name.')
    
#     def start_process(self):
#         self.timer.start(1)

#         # Retrieve frequency, time, and amplitude from user input
#         try:
#             self.frequency = float(self.label_30.text())  # Assuming label_30 holds frequency value
#             self.time_duration = float(self.label_31.text())  # Assuming label_31 holds time value
#             self.amplitude = float(self.label_33.text())  # Assuming label_33 holds amplitude value
#             print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
#         except ValueError:
#             print("Invalid frequency, time, or amplitude value")
#             return
#         # Retrieve the file name entered in input_8
#         # entered_name = self.input_8.text().strip()
        
#         # # Ensure the file name is not empty
#         # if not entered_name:
#         #     QMessageBox.warning(self, 'Error', 'Please enter a file name.')
#         #     return

#         # # Define the CSV file path based on entered file name
#         #   # Define the CSV file path based on entered file name
#         # self.entered_name = entered_name  # Store it as an instance variable
#         # csv_file = f'{self.entered_name}_data_log.csv'

#         # # Check if the file already exists
#         # # if os.path.isfile(csv_file):
#         # #     QMessageBox.warning(self, 'Error', 'This file name already exists. Please enter a unique name.')
#         # #     return

#         # # Set the label_56 to display the file name
#         # self.label_56.setText(entered_name)
#          # Create a unique file for each process based on some identifier (like the current time or config name)
#         # process_name = self.process_config[0]  # Using config name to identify the process
#         # csv_file = f'{process_name}_data_log.csv'
#         entered_name = self.input_8.text().strip()

#                 # If no name is entered, return early
#         if not entered_name:
#                     return

#                 # Define the CSV file path based on entered name
#         self.entered_name = entered_name
#         csv_file = f'{entered_name}_data_log.csv'

#                 # Check if the file already exists
#         if os.path.isfile(csv_file):
#                     # Display a dialog box indicating the file exists
#                     QMessageBox.warning(self, 'File Name Exists', 'This file name already exists. Please choose a different name.')
#         #Initialize an array to store data
#         self.sound_data=[] # to store sound data temporarily
#         self.max_limit = 100 # set the array size limit to 100

#     # Open the CSV file for writing data
#         file_exists = os.path.isfile(csv_file)
#         with open(csv_file, mode='a', newline='') as file:
#              fieldnames = ['Time', 'Amplitude', 'Sound Count']
#              writer = csv.DictWriter(file, fieldnames=fieldnames)
#              if not file_exists:
#                 writer.writeheader()  # Write header if it's a new file

# # Start the sound generation timer to repeat every 2 seconds
#         self.sound_timer.start(1000)  # Start timer for every 2000 ms (2 seconds)
#         # Generate and play the sound based on frequency and amplitude
#         self.generate_sound(self.frequency, self.amplitude)
#         self.timer2.start()

#         # Start the process timer
#         self.process_start_time = QDateTime.currentDateTime()  # Record the current date and time
#         self.timer_process.start(1000)  # Update every second

#         if self.mode == "READY":
#             self.label_38.setText("PROCESSING")
#             if self.feed_graph.layout() is None:
#                 print("Creating new layout")
#                 self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
#                 self.canvas = FigureCanvas(self.fig)
#                 layout = QVBoxLayout()
#                 layout.addWidget(self.canvas)
#                 self.feed_graph.setLayout(layout)

#             # Set the graph axis labels
#             self.ax.set(xlabel='Time (s)', ylabel='Amplitude (m)')
#             self.ax.grid()

#             # Initialize an empty plot line for amplitude
#             self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5), label='Amplitude')
            
#             # Optionally, you can set a secondary y-axis for frequency
#             self.ax_freq = self.ax.twinx()  # Create a secondary y-axis
#             self.ax_freq.set_ylabel('Frequency (Hz)')  # Label for frequency
#             self.ax_freq.set_ylim(0, self.frequency * 2)  # Adjust limits if needed

#             # Set initial time
#             self.t = 0

#             # Initialize data lists
#             self.time_data = []
#             self.sine_data = []

#             # Draw the initial empty canvas
#             self.canvas.draw()
            
#             # Start the update timer as usual for updating the plot
#         if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
#             self.update_timer = QTimer()
#             self.update_timer.timeout.connect(self.display_plot)
#             self.update_timer.start(1000)  # Update the plot every 1 second

#             self.store_real_time_data(csv_file)

#             self.display_plot()
def display_plot(self):
    """Updates the graph in real-time."""
    self.line.set_data(self.time_data, self.force_data)
    self.ax.relim()
    self.ax.autoscale_view()
    self.scrollbar.setMaximum(len(self.time_data))  # Update scrollbar range
    self.canvas.draw()
def scroll_graph(self, value):
    """Handles scrolling of the graph."""
    window_size = 50  # Number of data points to display
    start = max(0, value - window_size)
    end = value
    self.ax.set_xlim(self.time_data[start], self.time_data[end] if end < len(self.time_data) else self.time_data[-1])
    self.canvas.draw()

def store_real_time_data(self, csv_file):
    """Stores force vs. time data in CSV."""
    current_time = (QDateTime.currentDateTime() - self.process_start_time).toSecsSinceEpoch()
    force_value = self.force  # Simulate real-time force calculation
    self.time_data.append(current_time)
    self.force_data.append(force_value)
    self.data.append({'Time': current_time, 'Force': force_value})

    if len(self.data) > self.max_limit:
        self.data.pop(0)  # Maintain max size for performance

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Time', 'Force'])
        writer.writerow({'Time': current_time, 'Force': force_value})

    # def display_plot(self):
    #      # Fetch and convert values from labels
    #     try:
    #         self.frequency = float(self.label_30.text())
    #         self.time_duration = float(self.label_31.text())
    #         self.amplitude = float(self.label_33.text())
    #         print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}, Time: {self.time_duration}")
    #     except ValueError:
    #         print("Error: Please ensure that frequency, time, and amplitude are valid numbers.")
    #         return

    #     self.t += 1  # Increment time
    #     self.time_data.append(self.t)

    #     # Generate sine wave data based on the current time, frequency, and amplitude
    #     sine_value = self.amplitude * np.sin(2 * np.pi * self.frequency * self.t)
    #     self.sine_data.append(sine_value)

    #     # Check the length of data to determine how much to plot
    #     if len(self.time_data) > 25:
    #         t_data = self.time_data[-25:]
    #         sine_wave_data = self.sine_data[-25:]
    #     else:
    #         t_data = self.time_data
    #         sine_wave_data = self.sine_data

    #     # Update the plot with new sine wave data
    #     self.line.set_data(t_data, sine_wave_data)

    #     # Clear previous annotations before drawing new ones
    #     self.ax.cla()  # Clear the axis
    #     self.ax.grid()
    #     self.ax.set_xlabel('Time (s)')
    #     self.ax.set_ylabel('Amplitude (m)')
    #     self.ax.set_title('Sine Wave')

    #     # Redraw the line with updated data
    #     self.line, = self.ax.plot(t_data, sine_wave_data, color=(0, 0.5, 0.5))

    #     # Annotate points on the graph
    #     for x, y in zip(t_data, sine_wave_data):
    #         self.ax.annotate(f"{y:.2f}", xy=(x, y), textcoords="offset points", xytext=(0, 10), ha='center')

    #     # Adjust limits and redraw the canvas
    #     self.ax.relim()
    #     self.ax.autoscale_view()
    #     self.canvas.draw()

    #def display_plot_1(self, time_data, amplitude_data, sound_count_data):
        # Clear the previous graph for feed_graph_3
     #   self.ax2.clear()  # Clear the primary y-axis (Amplitude vs. Time)

        # Create a constant amplitude value from the loaded data (first value)
      #  constant_amplitude = amplitude_data.iloc[0]

        # Plot a constant amplitude line
       # self.ax2.plot(time_data, [constant_amplitude] * len(time_data), color=(0.5, 0, 0.5), label='Amplitude', linewidth=2)

        # Create a secondary y-axis for sound count vs. time
       # self.ax2_sound = self.ax2.twinx()  # Create a secondary y-axis sharing the same x-axis (Time)

        # Plot sound count vs. time using step function to create peaks
       # self.ax2_sound.step(time_data, sound_count_data, color=(0, 0.5, 0.5), label='Sound Count', where='post')

        # Set axis labels and legends
        #self.ax2.set_xlabel('Time (s)')
       # self.ax2.set_ylabel('Amplitude')
       # self.ax2.legend(loc='upper left')
       # self.ax2.grid()

       # self.ax2_sound.set_ylabel('Sound Count')
       # self.ax2_sound.legend(loc='upper right')

        # Set limits to make it clear
       # self.ax2.set_ylim(bottom=0)  # Adjust based on your amplitude range
       # self.ax2_sound.set_ylim(bottom=0)  # Adjust based on your sound count range

        # Refresh the canvas to display the updated graph
       # self.canvas2.draw()  # Assuming this is your canvas for feed_graph_3

        #print("Feed graph 3 updated with loaded data.")
    # def display_plot_1(self, time_data, amplitude_data, sound_count_data):
    #     # Ensure screen_7 and feed_graph_3 are properly set up for plotting
    #     self.feed_graph_3 = self.findChild(QWidget, "feed_graph_3")

    #     # Clear the previous graph on feed_graph_3
    #     self.ax2.clear()  # Clear the primary y-axis (Amplitude vs. Time)

    #     # Create a constant amplitude value from the loaded data (first value)
    #     constant_amplitude = amplitude_data.iloc[0]

    #     # Plot a constant amplitude line (horizontal line for amplitude)
    #     self.ax2.plot(time_data, [constant_amplitude] * len(time_data), color=(0.5, 0, 0.5), label='Amplitude', linewidth=2)

    #     # Create a secondary y-axis for sound count vs. time
    #     self.ax2_sound = self.ax2.twinx()  # Create a secondary y-axis sharing the same x-axis (Time)

    #     # Plot sound count vs. time using a step function to create peaks
    #     self.ax2_sound.step(time_data, sound_count_data, color=(0, 0.5, 0.5), label='Sound Count', where='post')

    #     # Set axis labels and legends
    #     self.ax2.set_xlabel('Time (min)')
    #     self.ax2.set_ylabel('Amplitude(m)')
    #     #self.ax2.legend(loc='upper left')
    #     self.ax2.grid()

    #     #self.ax2_sound.set_ylabel('Sound Count')
    #     #self.ax2_sound.legend(loc='upper right')

    #     # Set limits to make it clearer (optional, adjust based on data range)
    #     self.ax2.set_ylim(bottom=0)  # Adjust based on your amplitude range
    #     self.ax2_sound.set_ylim(bottom=0)  # Adjust based on your sound count range

    #     # Refresh the canvas to display the updated graph
    #     self.canvas2.draw()  # Use canvas2 that is linked to feed_graph_3 on screen_7

    #     print("Graph displayed on screen_7 (feed_graph_3).")

    # def store_real_time_data(self, csv_file):
    #     # Ensure sound_count is initialized
    #     if not hasattr(self, 'sound_count'):
    #         self.sound_count = 0

    #     # Ensure self.time_duration and self.amplitude are defined
    #     if not hasattr(self, 'time_duration') or not hasattr(self, 'amplitude'):
    #         print("Error: time_duration or amplitude is not defined.")
    #         return

    #     # Calculate elapsed time in seconds
    #     elapsed_seconds = self.process_start_time.secsTo(QDateTime.currentDateTime())

    #        # Convert elapsed time to minutes and round to 2 decimal places
    #     elapsed_minutes = int(elapsed_seconds // 60)

    #     # Debug: Print values before incrementing
    #     print(f"Before increment - Time: {elapsed_minutes:.2f} minutes, Amplitude: {self.amplitude}, Sound Count: {self.sound_count}")

    #     # Initialize sound_data array if it doesn't exist
    #     if not hasattr(self, 'sound_data'):
    #         self.sound_data = []
    
    #     # Append the current data only for a full minute
    #     if elapsed_seconds % 60 == 0:  # Store only when a full minute has passed
    #         self.sound_data.append({
    #             'Time': elapsed_minutes,  # Store full minutes only
    #             'Amplitude': self.amplitude,
    #             'Sound Count': self.sound_count,
    #         })

    #     # Append the current data to sound_data
    #     self.sound_data.append({
    #         'Time': elapsed_minutes,  # Storing time in minutes
    #         'Amplitude': self.amplitude,
    #         'Sound Count': self.sound_count,
    #         # 'Temperature': None,  # Replace with actual temperature if available
    #         # 'Pressure': None  # Replace with actual pressure if available
    #     })

    #     # Debug: Print current sound_data array
    #     print(f"After adding entry {self.sound_count}, current sound_data array:")
    #     for i, data in enumerate(self.sound_data, 1):
    #         print(f"Index {i} -> Time: {data['Time']} minutes, Amplitude: {data['Amplitude']}, Sound Count: {data['Sound Count']}")

    #     # Write the current data to the CSV
    #     self.append_to_csv(csv_file)

    #     # Increment the sound generation count after storing the current data
    #     self.sound_count += 1

    #     # Clear the sound_data array after writing
    #     self.sound_data = []
    # def store_real_time_data(self, csv_file):
    #     # Ensure sound_count is initialized
    #     if not hasattr(self, 'sound_count'):
    #         self.sound_count = 0

    #     # Ensure self.time_duration and self.amplitude are defined
    #     if not hasattr(self, 'time_duration') or not hasattr(self, 'amplitude'):
    #         print("Error: time_duration or amplitude is not defined.")
    #         return

    #     # Calculate elapsed time in days, hours, minutes, and seconds
    #     elapsed_seconds = self.process_start_time.secsTo(QDateTime.currentDateTime())
    #     days = elapsed_seconds // 86400
    #     hours = (elapsed_seconds % 86400) // 3600
    #     minutes = (elapsed_seconds % 3600) // 60
    #     seconds = elapsed_seconds % 60
    #     formatted_time = f"{days}d {hours:02}:{minutes:02}:{seconds:02}"

    #     # Debug: Print values before incrementing
    #     print(f"Before increment - Time: {formatted_time}, Amplitude: {self.amplitude}, Sound Count: {self.sound_count}")

    #     # Initialize sound_data array if it doesn't exist
    #     if not hasattr(self, 'sound_data'):
    #         self.sound_data = []

    #     # Append the current data to sound_data
    #     self.sound_data.append({
    #         'Time': formatted_time,
    #         'Amplitude': self.amplitude,
    #         'Sound Count': self.sound_count,
    #         #'Temperature': None,  # Replace with actual temperature if available
    #         #'Pressure': None  # Replace with actual pressure if available
    #     })

    #     # Debug: Print current sound_data array
    #     print(f"After adding entry {self.sound_count}, current sound_data array:")
    #     for i, data in enumerate(self.sound_data, 1):
    #         print(f"Index {i} -> Sound Count: {data['Sound Count']}")

    #     # Write the current data to the CSV
    #     self.append_to_csv(csv_file)

    #     # Increment the sound generation count after storing the current data
    #     self.sound_count += 1

    #     # Clear the sound_data array after writing
    #     self.sound_data = []

   # def store_real_time_data(self, csv_file): 
        # Ensure that sound_count is initialized
    #    if not hasattr(self, 'sound_count'):
    #        self.sound_count = 0  # Initialize sound_count if not already set

        # Ensure self.time_duration and self.amplitude are defined
    #    if not hasattr(self, 'time_duration') or not hasattr(self, 'amplitude'):
    #        print("Error: time_duration or amplitude is not defined.")                                   
    #        return

        # Debug: Print values before incrementing
    #    print(f"Before increment - Time: {self.time_duration}, Amplitude: {self.amplitude}, Sound Count: {self.sound_count}")

        # Initialize sound_data array if it doesn't exist
    #    if not hasattr(self, 'sound_data'):
    #        self.sound_data = []  # Create the array to store sound-related data

        # Append the current data (before increment) to the sound_data array
     #   self.sound_data.append({
    #        'Time': self.time_duration,
    #        'Amplitude': self.amplitude,
    #        'Sound Count': self.sound_count,  # Use current sound count before increment
    #        'Temperature': None,  # Replace with actual temperature if available
    #        'Pressure': None  # Replace with actual pressure if available
    #    })

        # Debug: Print current sound_data array
        
     #   print(f"After adding entry {self.sound_count}, current sound_data array:")
        
     #   for i, data in enumerate(self.sound_data, 1):
     #       print(f"Index {i} -> Sound Count: {data['Sound Count']}")

        # Write the current data to the CSV
    #    self.append_to_csv(csv_file)

        # Increment the sound generation count after storing the current data
       # self.sound_count += 0

        # Clear the sound_data array after writing to prevent duplicate entries
        #self.sound_data = []  # Reset the array after each write
# Function for appending the real-time data in CSV file
    def append_to_csv(self, csv_file):
        try:
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, mode='a', newline='') as file:
                fieldnames = ['Time', 'Amplitude', 'Sound Count']
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                # Write header if the file is new
                if not file_exists:
                    writer.writeheader()

                # Write the latest row from the sound_data array
                writer.writerow(self.sound_data[-1])

            print(f"Data successfully written to {csv_file}. Entry: {self.sound_data[-1]}")

        except Exception as e:
            print(f"Error writing to file: {e}")
    
   # function for loading CSV File data to generate a static graph that is displayed on screen_7  
    def load_csv_data(self):
       
        options = QFileDialog.Options()
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)

        if file_path:
            # Read the CSV file into a DataFrame
            data = pd.read_csv(file_path)

            # Assuming your CSV has columns 'Time', 'Amplitude', and 'Sound Count'
            time_data = data['Time']
            force_value_data = data['Force']
            sound_count_data = data['Sound Count']

            # Call the new display function for feed_graph_3
            self.display_plot_1(time_data, amplitude_data, sound_count_data)

            print(f"Loaded data from {file_path}")

            data = pd.read_csv(file_path, on_bad_lines='skip')  # Pandas will skip problematic lines

    #def store_real_time_data(self, csv_file):
    # Fetch temperature and pressure from the relevant labels (assumed here to be label_38 and label_47)
        #rx_temperature = float(self.label_38.text())  # Assuming label_38 holds temperature
        #rx_pressure = float(self.label_47.text())  # Assuming label_47 holds                 pressure 
      # Ensure self.time_duration is defined before being used

     #if not hasattr(self, 'time_duration'): 
      #  print("Error: time_duration is not defined.")
       # return
    # Increment the sound generation count
    # self.sound_count += 1

    # Write the real-time data to the CSV file
     #with open('ths_data_log.csv', mode='a', newline='') as file:
      #  writer = csv.DictWriter(file, fieldnames=['Time', 'Amplitude', 'Sound Count', 'Temperature', 'Pressure'])
       # writer.writerow({
        #    'Time': self.time_duration,
         #   'Amplitude': self.amplitude,
          #  'Sound Count': self.sound_count,
            #'Temperature': rx_temperature,
            #'Pressure': rx_pressure
       # })                                                                                                                   
# Function for generation of sound signal
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
# Function for playing sound again and again    
    def play_sound(self):
        """Play the sound based on the current frequency and amplitude."""
        audio_signal = self.generate_sound(self.frequency, self.amplitude)
        #sd.play(audio_signal, samplerate=44100)  # Play the generated sound
        sd.wait()  # Wait until the sound has finished playing
    # Increment the sound generation count
        self.sound_count += 1 

         #Log this event by storing the real-time data in the CSV
        #csv_file = f'{self.entered_name}_data_log.csv'  # Ensure you're writing to the correct file
        #self.store_real_time_data{self.entered_name}_data_log.csv
        #self.sound_count_label.setText(f"Sound Count: {self.sound_count}")  # Update sound count label
        print(f"Sound generated {self.sound_count} times.")  # Optional print statement

    #def complete_process(self):
        
     #   print("Complete button pressed.")

        # Assume csv_file holds the file path or name of the saved CSV file
      #  if hasattr(self, 'sound_data') and len(self.sound_data) > 0:
       #     csv_file = f'{self.process_config[0]}_data_log.csv'  # Ensure CSV filename
         #   print(f"Writing {len(self.sound_data)} entries to CSV before completing.")
          #  self.append_to_csv(csv_file)  # Save data to CSV
          #  self.sound_data = []  # Clear the array after writing

        # Add logic to complete the process
        #self.mode = "COMPLETE"
      #  self.label_38.setText("PROCESS COMPLETE")

        # Stop timers, finalize data processing, and clean up if needed
       # self.stop_process()

        # Stop the sound timer if applicable
        #if hasattr(self, 'sound_timer'):
         #   self.sound_timer.stop()

        # Create the dialog box and display the message along with the CSV file path
        #msg_box = QMessageBox()
        #msg_box.setIcon(QMessageBox.Information)
       # msg_box.setWindowTitle("Process Complete")
        
        # Customize the message to include the CSV file path or name
       # message = f"Process is complete and data is stored."
       # msg_box.setText(message)
        
        #msg_box.setStandardButtons(QMessageBox.Ok)
        #msg_box.exec_()
        
       # print("Process completed.")
# Function for the pause state       
    def pause_process(self):
#         # """
#     #Handles the "Pause" button press.
#     ## """
             print("Pause button pressed.")
        
#         # Check if there is data in the sound_data array and if the array has less than or equal to 100 entries
    #  if hasattr(self, 'sound_data') and len(self.sound_data) > 0:
     #        csv_file = f'{self.process_config[0]}_data_log.csv'  # Ensure CSV filename
      #       print(f"Writing {len(self.sound_data)} entries to CSV before pausing.")
       #      self.append_to_csv(csv_file)  # Save data to CSV
        #  self.sound_data = []  # Clear the array after writing

             self.timer.stop()
             self.mode = "PAUSED"
             self.label_38.setText("PAUSED")
             cmd = TX_PAUSE.format( self.label_30.text().zfill(3), self.label_31.text().zfill(3),self.label_32.text().zfill(3),self.label_33.text().zfill(3))
             cmd = "*PP:000:000:000:000#"
             print(cmd)
             self.tx_data(cmd)
             self.stop_process()
             # Stop the sound timer
             if hasattr(self, 'sound_timer'):
              self.sound_timer.stop()  # Stop the sound generation
     # Change the text of button_7 to "RESUME"
             self.button_7.setText("RESUME")
              # Re-enable button_7 when the pause button is pressed
             self.button_7.setDisabled(False)

# Function for the state of reset
    def reset_process(self):
        # """Resets the process to its initial state."""
        print("Reset button pressed.")
        
        # Show a confirmation dialog
        reply = QMessageBox.question(
            self, 
            'Confirm Reset', 
            "Are you sure? You want to delete the data.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        # If the user selects 'No', cancel the reset
        if reply == QMessageBox.No:
            print("Reset canceled by the user.")
            return
        
        # Proceed with reset if the user confirms
        print("Reset confirmed by the user.")
        
        self.mode = "RESET"
        self.label_38.setText("RESET")
        self.button_7.setText("START")
        self.button_7.setEnabled(True)
        self.button_A.setEnabled(True)
        self.stop_process()
        
        # Stop the sound timer
        if hasattr(self, 'sound_timer'):
            self.sound_timer.stop()  # Stop the sound generation

        # Clear the graph
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.canvas.draw()

        # Clear data arrays
        self.time_data = []
        self.sine_data = []
        self.pressure_data = []

        # Clear the camera feed
        self.feed_cam.setPixmap(QPixmap())

        # Send reset command
        cmd = TX_RESET.format(self.label_30.text().zfill(3), self.label_31.text().zfill(3), self.label_32.text().zfill(3), self.label_33.text().zfill(3))
        print(cmd)
        self.tx_data(cmd)

        # Clear the CSV file contents
        csv_file = f'{self.entered_name}_data_log.csv'
        with open(csv_file, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Time', 'Amplitude', 'Sound Count'])  # Write the header
        print(f"CSV file {csv_file} cleared, header retained.")

    # def reset_process(self):
    # # """Resets the process to its initial state."""
    #     print("Reset button pressed.")
    #     self.mode = "RESET"
    #     self.label_38.setText("RESET")

    #     self.stop_process()
        
    #     # Stop the sound timer
    #     if hasattr(self, 'sound_timer'):
    #         self.sound_timer.stop()  # Stop the sound generation

    #     # Clear the graph
    #     if hasattr(self, 'ax'):
    #         self.ax.clear()
    #         self.canvas.draw()

    #     # Clear data arrays
    #     self.time_data = []
    #     self.sine_data = []
    #     self.pressure_data = []

    #     # Clear the camera feed
    #     self.feed_cam.setPixmap(QPixmap())

    #     # Send reset command
    #     cmd = TX_RESET.format(self.label_30.text().zfill(3), self.label_31.text().zfill(3), self.label_32.text().zfill(3), self.label_33.text().zfill(3))
    #     print(cmd)
    #     self.tx_data(cmd)

    #     # Clear the CSV file contents
    #     csv_file = f'{self.entered_name}_data_log.csv'
    #     # Replace with the correct path to your CSV file
    #     #try:
    #     with open(csv_file, 'w', newline='') as csv_file:
    #             # Optionally, write the header if you want to keep it
    #          writer = csv.writer(csv_file)
    #          writer.writerow(['Time', 'Amplitude', 'Sound Count'])  # Replace with your actual header if necessary
    #             # This keeps the header and clears the rest of the data
    #     print(f"CSV file {csv_file} cleared, header retained.")
    #     #except Exception as e:
    #     #print(f"Error clearing CSV file: {e}")



    def stop_process(self):
    #"""Stops all timers and clears the plot."""
        for timer in [self.timer, self.timer2, self.timer_process, getattr(self, 'update_timer', None)]:
         if timer and timer.isActive():
            timer.stop()
        print("Timers stopped.")

    # def update_process_time(self):
    #     # Calculate elapsed time in seconds
    #     elapsed_seconds = self.process_start_time.secsTo(QDateTime.currentDateTime())

    #     # Calculate elapsed days, hours, minutes, and seconds
    #     days = elapsed_seconds // 86400
    #     hours = (elapsed_seconds % 86400) // 3600
    #     minutes = (elapsed_seconds % 3600) // 60
    #     seconds = elapsed_seconds % 60

    #     # Format the elapsed time as a string
    #     formatted_time = f"{days}d {hours:02}:{minutes:02}:{seconds:02}"

    #     # Print the formatted time for debugging
    #     print(f"{formatted_time}")

        # # Update the label_41 with the formatted time
        # self.label_41.setText(formatted_time)

        # # Store the real-time data, passing only the CSV file path as an argument
        # self.store_real_time_data(f'{self.entered_name}_data_log.csv')
    def update_process_time(self):
    # Example implementation: Update elapsed time in a QLabel
        current_time = QDateTime.currentDateTime()
        elapsed_time = self.process_start_time.secsTo(current_time)  # Calculate elapsed seconds
        elapsed_minutes = elapsed_time // 60
        elapsed_seconds = elapsed_time % 60
        self.label_41.setText(f"{elapsed_minutes}m {elapsed_seconds}s")  # Update time in QLabel


     # Function to update the timer label
    #def update_process_time(self):
        # Calculate elapsed time in seconds
     #   elapsed_seconds = self.process_start_time.secsTo(QDateTime.currentDateTime())

        # Calculate elapsed days, hours, minutes, and seconds
      #  days = elapsed_seconds // 86400
       # hours = (elapsed_seconds % 86400) // 3600
        #minutes = (elapsed_seconds % 3600) // 60
       # seconds = elapsed_seconds % 60

        # Convert days into years and months (assuming 30 days per month and 365 days per year)
       # years = days // 365
       # months = (days % 365) // 30
       # remaining_days = (days % 365) % 30
        # Print the calculated time values for debugging
       # print(f"{years}y {months}m {remaining_days}d {hours:02}:{minutes:02}:{seconds:02}")
        
        # Update QLabel 'label_41' with formatted time
       # self.label_41.setText(f"{years}y {months}m {remaining_days}d {hours:02}:{minutes:02}:{seconds:02}")
    
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

    # def open_csv_files(self):
    #     # Define the file pattern for real-time stored data files
    #     csv_file = f'{self.process_config[0]}_data_log.csv'# process_config should be dynamically replaced
    #     directory = 'path_to_your_directory'  # Replace with the actual directory where the CSV files are stored

    #     # Open a file dialog to select CSV files
    #     files, _ = QFileDialog.getOpenFileNames(self, "Select CSV File", directory, "CSV Files (*.csv)")

    #     if files:
    #         # Process the selected files
    #         for file in files:
    #             print(f"Selected file: {file}")
    #             # You can add your code here to read and display the file, or further process the file
    #             self.load_csv_file(file)

    # def load_csv_file(self, file_path):
    #     # Function to handle loading and processing the selected CSV file
    #     with open(file_path, 'r') as csv_file:
    #         reader = csv.reader(csv_file)
    #         for row in reader:
    #             print(row)  # Replace this with actual processing of the file data


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
        if self.screen == 7:
           self.screen = 2
        elif self.screen == 6:
            self.screen = 4
        elif self.screen == 4:
            self.screen = 2
           
        else:
                self.screen = self.screen - 1
        print(self.screen)
        self.handle_screen_change(self.screen)
        self.heater=False
        self.pump=False
       # self.valve2=False

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
                    #elif my_data==RX_COMPLETE:
                    #    self.mode="COMPLETE PROCESS"
                    elif my_data==RX_RESET:
                        self.mode="RESET"
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
            #self.button_A.setDisabled(True)
        elif self.mode == "PROCESSING":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            self.button_A.setDisabled(True)
            self.display_plot()
        elif self.mode == "PAUSED":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            self.button_A.setDisabled(True)
        # elif self.mode == "COMPLETE":
        #     self.button_7.setEnabled(True)
        #     self.button_8.setEnabled(True)
        #     self.button_9.setEnabled(True)
        #     self.button_A.setEnabled(True)
        elif self.mode == "RESET":
            self.button_7.setEnabled(True)
            self.button_8.setEnabled(True)
            self.button_9.setEnabled(True)
            # self.button_A.setEnabled(True)
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
        self.button_A.setEnabled(True)
    def handle_pump(self):
        self.button_A.setEnabled(True)
        if self.is_filling:
            print("Pump started to fill tank")
           
            self.button_16.setStyleSheet('background-color:transparent;')
            self.button_16.setIcon(QIcon(base_path + "/rsc/cttm_left_pressed.png"))
            self.label_7.setText("Pump Fill")
            #self.label_8.setText("Pump is filling the tank")
            self.tx_data(TX_PUMP_FILL)
        else:
            print("Pump is emptying the tank")
            self.button_16.setStyleSheet("background-color:transparent;")
            self.button_16.setIcon(QIcon(base_path + "/rsc/cttm_left.png"))
            self.label_7.setText("Pump Empty")
           # self.label_8.setText("Pump is emptying the tank")
            self.tx_data(TX_PUMP_EMPTY)
        
        # Toggle the state after each button press
        self.is_filling = not self.is_filling
    # def handle_pump(self):
    #     print("Pump started to fill tank")
    #     self.button_16.setStyleSheet('background-color:transparent;')
    #     self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_left_pressed.png"))
    #     self.label_7.setText("Pump Fill")
    #     self.tx_data(TX_PUMP_FILL)

    # def pump_empty(self):
    #     print("Pump is emptying the tank")
    #     self.button_16.setStyleSheet("background-color:transparent;")
    #     self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_left.png"))
    #     self.label_7.setText("Pump Empty")

    #     self.tx_data(TX_PUMP_EMPTY)

    # def motor_right_pressed(self):
    #     print("motor pressed")
    #     self.button_14.setStyleSheet("background-color:transparent;")
    #     self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right_pressed.png"))

    #     self.tx_data(TX_MOTOR_FORWARD_START)

    # def motor_right_released(self):
    #     print("motor released")
    #     self.button_14.setStyleSheet("background-color:transparent;")
    #     self.button_14.setIcon(QIcon(base_path+"/rsc/cttm_right.png"))
    #     self.tx_data(TX_MOTOR_FORWARD_STOP)

    def handle_heater(self):
        self.button_A.setEnabled(True)
        self.heater= not self.heater
        if(self.heater): 
            #heater on 
            self.label_8.setText("Heater ON")
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater_pressed.png"))

            self.tx_data(TX_HEATER_START)
        else: 
            #heater off
            self.tx_data(TX_HEATER_STOP)
            self.label_8.setText("Heater OFF")
            self.button_15.setStyleSheet("background-color:transparent;")
            self.button_15.setIcon(QIcon(base_path+"/rsc/cttm_heater.png"))

        #print("heater")

    # def handle_valve_1(self):
    #     self.valve1 = not self.valve1
    #     if (self.valve1):
    #         #valve on
    #         print("value 1 ON") 
    #         self.label_7.setText("Clamp 1 ON")
    #         self.button_16.setStyleSheet("background-color:transparent;")
    #         self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))
            
    #         self.tx_data(TX_VALVE1_OPEN)
    #     else:
    #         # valve off
    #         print("value 1 OFF")
    #         self.label_7.setText("Clamp 1 OFF")
    #         self.button_16.setStyleSheet("background-color:transparent;")
    #         self.button_16.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))
    #         self.tx_data(TX_VALVE1_CLOSE)

    # def handle_valve_2(self):
    #     print("hello from handle_valve_2")
    #     self.valve2 = not self.valve2
    #     if (self.valve2):
    #         #valve on
    #         print("value 2 ON")
    #         self.label_10.setText("Clamp 2 ON")
    #         self.button_17.setStyleSheet("background-color:transparent;")
    #         self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp_pressed.png"))

    #         self.tx_data(TX_VALVE1_OPEN)
    #     else:
    #         # valve off
    #         print("value 2 OFF")
    #         self.label_10.setText("Clamp 2 OFF")
    #         self.button_17.setStyleSheet("background-color:transparent;")
    #         self.button_17.setIcon(QIcon(base_path+"/rsc/cttm_clamp.png"))

    #         self.tx_data(TX_VALVE2_CLOSE)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    # window.showFullScreen()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()