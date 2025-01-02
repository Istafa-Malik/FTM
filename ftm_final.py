import os
import sys
import csv
import time
from matplotlib import pyplot as plt
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QScrollBar
from PyQt5.uic import loadUi
import serial
base_path = "."

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui_ftm.ui',self)


        # Initialize figures and canvas for graphs
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.fig2 = Figure()
        self.ax2 = self.fig2.add_subplot(111)

        # Initialize feed_graph and feed_graph_3 from the UI file
        self.feed_graph = self.findChild(QFrame, "feed_graph")
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.feed_graph.setLayout(layout)
        self.ax.set(xlabel='Time (min)', ylabel='Force')
        self.ax.grid()

        self.feed_graph_3 = self.findChild(QFrame, "feed_graph_3")
        self.canvas2 = FigureCanvas(self.fig2)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.canvas2)
        self.feed_graph_3.setLayout(layout2)
        self.ax2.set(xlabel='Time (min)', ylabel='Force')
        self.ax2.grid()

        # Initialize buttons and their handlers from the UI file
        # Initialize buttons and other widgets from the UI file
        self.button_2 = self.findChild(QPushButton, "button_2")
        self.button_3 = self.findChild(QPushButton, "button_3")
        self.button_4 = self.findChild(QPushButton, "button_4")
        self.button_20 = self.findChild(QPushButton, "button_20")
        self.button_A = self.findChild(QPushButton, "button_A")
        self.button_7 = self.findChild(QPushButton, "button_7")
        self.button_8 = self.findChild(QPushButton, "button_8")
        self.button_9 = self.findChild(QPushButton, "button_9")

        # Connect buttons to their respective handlers
        self.button_2.clicked.connect(lambda: self.handle_screen_change(2))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        self.button_4.clicked.connect(self.close)
        self.button_20.clicked.connect(self.load_csv_data)
        self.button_A.clicked.connect(self.handle_back_pressed)  # Example of button_A handler
        self.button_7.clicked.connect(self.start_process)
        # self.button_8.clicked.connect(self.pause_process)
        # self.button_9.clicked.connect(self.stop_process)
        self.comboBox = self.findChild(QtWidgets.QComboBox, "comboBox")  # Ensure you have this line to find the comboBox
        self.load_comlist()  # Load available COM ports into the comboBox
        self.comboBox.currentIndexChanged.connect(self.set_serial)


         # Add a horizontal scroll bar
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setMinimum(0)
        self.scrollbar.setMaximum(0)  # Initial range
        self.scrollbar.valueChanged.connect(self.scroll_graph)

        layout.addWidget(self.scrollbar)
        self.feed_graph.setLayout(layout)
        self.ser_2 = None
        self.t= 0

        # Timer for data reception
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.rx_data)

        # Timer for updating real-time graph
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

        # Initialize data storage
        self.time_data = []
        self.force_data = []
        self.csv_file = "force_time_data.csv"

        # Set up initial screen
        self.handle_screen_change(1)  # Default to screen 1
    

    def load_comlist(self):
        """Load available COM ports into the comboBox."""
        self.comboBox.clear()  # Clear existing items
        ports = serial.tools.list_ports.comports()  # Get list of available COM ports
        for port in ports:
            self.comboBox.addItem(port.device)  # Add each port to the comboBox


    def handle_screen_change(self, value):
         # Close the virtual keyboard if it is open when changing screens
        # if self.keyboard is not None and self.keyboard.isVisible():
        #     self.keyboard.close_keyboard()

        for widget in self.findChildren(QtWidgets.QPushButton):
            widget.setFocusPolicy(Qt.NoFocus)
        # for widget in self.findChildren(QtWidgets.QPushButton):  # QtWidgets.QPushButton should now work
        #     widget.setEnabled(False)

        if(value == 1): # Menu Screen
            self.screen = 1
            self.comboBox.hide()
            self.comboBox.setDisabled(True)
            self.screen_2.hide()
            self.screen_3.hide()
            self.button_A.hide()
            self.screen_1.show()
        elif(value == 2): # Real-time Graph Screen
            self.screen = 2
            self.screen_1.hide()
            self.screen_3.hide()
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.button_A.show()
            self.screen_2.show()

        elif(value == 3): # static graph screen
            self.screen = 3
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.screen_1.hide()
            self.screen_2.hide()
            self.button_A.show()
            self.screen_3.show()
    
    #  """Initialize the first screen (e.g., main menu)."""
    def handle_button_A_pressed(self):
        self.button_A.setIconSize(QSize(36, 36))

    def init_screen_1(self):
        self.screen = 1
        self.screen_2.hide()
        self.screen_3.hide()
        self.screen_1.show()
        self.setStyleSheet("background-color:rgb(250,250,250);")
        self.label_A.setPixmap(QPixmap(base_path+"/rsc/rsc2.png"))
        # self.label_6.hide()
        layout = QVBoxLayout()
        button_2 = QPushButton("screen_2")
        button_3 = QPushButton("screen_3")
        layout.addWidget(button_2)
        layout.addWidget(button_3)
        self.screen_1.setLayout(layout)

    def init_screen_2(self):
        """Initialize the real-time graph screen."""
        self.start_time = None
        self.is_paused = False
        self.time_data.clear()
        self.force_data.clear()
        # You don't need to set the layout again here, since it was already done in the UI

    def init_screen_3(self):
        """Initialize the static graph screen."""
        # You don't need to set the layout again here, since it was already done in the UI
        pass

    def handle_back_pressed(self):
        # Reset button icon size and clear the label
        self.button_A.setIconSize(QSize(40, 40))
        self.label_9.setText("")

        # Handle screen transitions based on current screen
        if self.screen == 2:  # If currently on screen 2
            self.screen = 1  # Go back to screen 1
        elif self.screen == 3:  # If currently on screen 3
            self.screen = 1  # Go back to screen 1
       
        else:
            self.screen = self.screen - 1  # Default behavior: decrement the screen number
        
        print(f"Navigating back to screen {self.screen}")
        
        # Change the screen and reset flags
        self.handle_screen_change(self.screen)
        # self.heater = False
        # self.pump = False
        # self.valve2 = False  # Uncomment this line if you need to reset valve2 as well   
    
    def start_process(self):
        """Start or resume the process of plotting and storing real-time data."""
        try:
            comPort2 = self.comboBox.currentText()
            if not comPort2:
                QMessageBox.warning(self, 'Error', 'Please select a COM port for MCU.')
                return

            if not self.ser_2 or not self.ser_2.is_open or self.ser_2.port != comPort2:
                self.ser_2 = serial.Serial(port=comPort2, baudrate=9600, timeout=1)
                print(f"MCU serial port opened: {self.ser_2.port}")
                print("The MCU connected successfully.")  # Indicate successful connection

            # Start the data reception timer
            self.data_timer.start(100)  # Check for data every 100 ms
            self.update_timer.start(1000)  # Update graph every second

        except Exception as e:
            QMessageBox.critical(self, 'Error', f"An error occurred: {e}")
            print(f"Error: {e}")

    def update_graph_from_mcu(self):
        """Fetch data from the MCU and update the graph."""
        try:
            if self.ser_2 and self.ser_2.is_open:
                while self.ser_2.in_waiting > 0:
                    my_data = self.ser_2.read(10)  # Read a fixed number of bytes

                    # Check if the received data matches the expected format
                    if len(my_data) >= 10:
                        print("Data received from MCU.")  # Indicate data reception

                        # Check for the stop command
                        if (my_data[4] == 0x30 and 
                            my_data[5] == 0x00 and 
                            my_data[8] == 0x01):
                            print("Stop command received from MCU.")
                            self.update_timer.stop()  # Stop the timer
                            self.ser_2.close()  # Close the serial port
                            self.label_38.setText("PROCESSING STOPPED")
                            return  # Exit the function

                        # Extract force value from the received data
                        high_byte = my_data[6]
                        low_byte = my_data[7]
                        force_value = (high_byte << 8) | low_byte  # Combine high and low byte to get the value
                        print(f"Force value received: {force_value}")

                        # Increment time for each data point
                        self.t += 1
                        self.time_data.append(self.t)
                        self.force_data.append(force_value)

                        # Update the graph with the new data
                        self.update_graph()

        except Exception as e:
            print(f"Error during data reception: {e}")
    # def pause_process(self):
    #     """Handle the pause/resume action for the real-time graph."""
    #     if self.is_paused:
    #         # Resume the graph by starting the timer again
    #         self.timer.start(1000)  # Update every second (or your preferred interval)
    #         self.button_7.setText("Pause")  # Change button text to "Pause"
    #         self.is_paused = False
    #     else:
    #         # Pause the graph by stopping the timer
    #         self.timer.stop()
    #         self.button_7.setText("Resume")  # Change button text to "Resume"
    #         self.is_paused = True
    
    # def stop_process(self):
    #     """Stop the real-time graph and reset data."""
    #     # Stop the timer to stop graph updates
    #     self.timer.stop()
        
    #     # Clear the data lists
    #     self.time_data.clear()
    #     self.force_data.clear()

    #     # Reset the graph
    #     self.ax.clear()
    #     self.ax.set(xlabel='Time (min)', ylabel='Force')
    #     self.ax.grid()
    #     self.canvas.draw()

    #     # Update the button text (if needed)
    #     self.button_7.setText("Pause")  # Reset pause button to "Pause"
    #     self.is_paused = False  # Ensure graph is not paused after stopping

    #     print("Graph stopped and data cleared.")

    def scroll_graph(self, value):
        """Adjust the graph view based on scrollbar value."""
        range_width = 10  # Define the width of the visible range
        start = value
        end = value + range_width
        self.ax.set_xlim(start, end)
        self.canvas.draw()

    def rx_data(self):
        """Receive data from the MCU."""
        try:
            if self.ser_2 and self.ser_2.is_open:
                while self.ser_2.in_waiting > 0:
                    my_data = self.ser_2.read(10)  # Read a fixed number of bytes
                    print(f"Data received from MCU: {my_data}")

                    # Check if the received data matches the expected format
                    if len(my_data) >= 10:
                        # Check for the start command
                        # Check for the start command
                        if (my_data[4] == 0x30 and my_data[5] == 0x00 and my_data[8] == 0x00):
                            print("Start command received from MCU.")
                            self.start_process()
                            self.t = 0  # Reset time counter
                            self.time_data.clear()
                            self.force_data.clear()
                            self.label_38.setText("PROCESSING")

                        # Check for the stop command
                        elif (my_data[4] == 0x30 and my_data[5] == 0x00 and my_data[8] == 0x01):
                            print("Stop command received from MCU.")
                            self.data_timer.stop()  # Stop the data reception timer
                            self.ser_2.close()  # Close the serial port
                            self.label_38.setText("PROCESSING STOPPED")
                            return  # Exit the function

                        # Extract force value from the received data
                        high_byte = my_data[6]
                        low_byte = my_data[7]
                        force_value = (high_byte << 8) | low_byte  # Combine high and low byte to get the value
                        print(f"Force value received: {force_value}")

                        # Increment time for each data point
                        self.t += 1
                        self.time_data.append(self.t)
                        self.force_data.append(force_value)

        except Exception as e:
            print(f"Error during data reception: {e}")


    def stop_real_time_plotting(self):
        """Stop the real-time graph plotting."""
        self.is_plotting = False
        print("Real-time plotting stopped")
        if self.timer_process:
            self.timer_process.stop()  # Stop the timer for real-time updates


    def update_graph(self):
        """Update the graph with real-time data."""
        if len(self.time_data) > 0:
            # Update plot data
            self.line.set_data(self.time_data, self.force_data)
            self.ax.relim()
            self.ax.autoscale_view()

            # Update scrollbar range
            max_time = self.time_data[-1]
            self.scrollbar.setMaximum(max(0, max_time - 10))  # Adjust scrollbar range

    def store_real_time_data(self, csv_file):
        """Store the real-time data (time and force) into a CSV file."""
        try:
            with open(csv_file, mode='a', newline='') as file:
                fieldnames = ['Time', 'Force']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                for t, force in zip(self.time_data, self.force_data):
                    writer.writerow({'Time': t, 'Force': force})
        except Exception as e:
            print(f"Error storing data: {e}")

    def load_csv_data(self):
        """Load and display CSV data in a static graph."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)

        if file_path:
            try:
                data = pd.read_csv(file_path)

                if 'Time' not in data.columns or 'Force' not in data.columns:
                    QMessageBox.warning(self, "Error", "The selected file does not contain 'Time' and 'Force' columns.")
                    return

                time_data = data['Time']
                force_data = data['Force']

                self.ax2.clear()
                self.ax2.plot(time_data, force_data, label="Force vs. Time")
                self.ax2.set(xlabel='Time (min)', ylabel='Force')
                self.ax2.legend()
                self.ax2.grid()
                self.canvas2.draw()

                print(f"Successfully loaded data from {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load the file. Error: {str(e)}")
    
    # def set_serial(self, index):
    #     """Handle serial port selection."""
    #     selected_port = self.comboBox.itemText(index)
    #     print(f"Selected COM port: {selected_port}")
    
    def set_serial(self):
        if self.ser != None:
            self.ser.close() 
        if self.comboBox.currentIndex() > -1:
            comPort= self.comboBox.currentText()
            self.ser = serial.Serial(comPort, baudrate=115200, timeout=1)

        # self.check_ports_and_error()

    def handle_comboBox_change(self):
        try:
            # Get the selected port from comboBox_2 (MCU)
            comPort2 = self.comboBox.currentText()

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

                self.ser_2 = serial.Serial(port=comPort2, baudrate=9600, timeout=1)  # Short timeout for real-time data
                print(f"MCU serial port opened: {self.ser_2.port}")
                self.label_9.setText("")
            else:
                self.label_9.setText("No port selected or already open for MCU")

            # Read data from MCU in real-time
            if self.ser_2 and self.ser_2.is_open:
                while True:  # Continuously check for incoming data
                    if self.ser_2.in_waiting > 0:
                        my_data = self.read_until_delimiter(self.ser_2)
                        print(f"Data received from MCU: {my_data}")

                        # Assuming force and time data are received in a certain format, for example:
                        # my_data[6] and my_data[7] contain force data, and my_data[8] and my_data[9] contain time data
                        if len(my_data) >= 10:
                            # Process force data (combine high and low byte)
                            high_byte_force = my_data[6]
                            low_byte_force = my_data[7]
                            force_value = (high_byte_force << 8) | low_byte_force  # Combine high and low byte
                            print(f"Force value received: {force_value}")

                            # Process time data (assuming it's 2 bytes for time, modify based on actual data format)
                            high_byte_time = my_data[8]
                            low_byte_time = my_data[9]
                            time_value = (high_byte_time << 8) | low_byte_time  # Combine high and low byte
                            print(f"Time value received: {time_value}")

                            # Store data for graph plotting
                            self.force_data.append(force_value)
                            self.time_data.append(time_value)

                            # Update real-time graph (Assuming you have a method to plot data)
                            self.update_real_time_graph(self.time_data, self.force_data)

            # Check for errors between the selected ports (power supply and MCU)
            self.check_ports_and_error()

        except Exception as e:
            # Handle any errors during serial port opening
            self.label_9.setText(f"Error: {e}")

    def check_ports_and_error(self):
        # Check if the power supply or MCU port is empty
        if self.comboBox.currentText() == "" or self.comboBox.currentText() == "":
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())