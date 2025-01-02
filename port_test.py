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
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QScrollBar

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui_ftm.ui', self)

        # Initialize figures and canvas for graphs
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.feed_graph = self.findChild(QFrame, "feed_graph")
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.feed_graph.setLayout(layout)
        self.ax.set(xlabel='Time (s)', ylabel='Force (N)')
        self.ax.grid()

        # Initialize buttons and their handlers from the UI file
        self.button_7 = self.findChild(QPushButton, "button_7")
        self.comboBox = self.findChild(QtWidgets.QComboBox, "comboBox")
        self.load_comlist()  # Load available COM ports into the comboBox
        self.button_7.clicked.connect(self.start_process)

        # Initialize data storage
        self.time_data = []
        self.force_data = []
        self.t = 0
        self.ser_2 = None  # Initialize the serial port for MCU

        # Timer for data reception
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.rx_data)

        # Timer for updating the graph
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_graph)

        # Set up initial screen
        self.handle_screen_change(1)  # Default to screen 1

    def load_comlist(self):
        """Load available COM ports into the comboBox."""
        self.comboBox.clear()  # Clear existing items
        ports = serial.tools.list_ports.comports()  # Get list of available COM ports
        for port in ports:
            self.comboBox.addItem(port.device)  # Add each port to the comboBox

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

    def update_graph(self):
        """Update the graph with real-time data."""
        if len(self.time_data) > 0:
            self.ax.clear()
            self.ax.plot(self.time_data, self.force_data, label="Force vs. Time")
            self.ax.set(xlabel='Time (s)', ylabel='Force (N)')
            self.ax.grid()
            self.ax.legend()
            self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())