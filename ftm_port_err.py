import sys
import csv
from matplotlib import pyplot as plt
import serial
import time
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
        self.comboBox = self.findChild(QtWidgets.QComboBox, "comboBox")


        # Connect buttons to their respective handlers
        self.button_2.clicked.connect(lambda: self.handle_screen_change(2))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        self.button_4.clicked.connect(self.close)
        self.button_20.clicked.connect(self.load_csv_data)
        self.button_A.clicked.connect(self.handle_back_pressed)  # Example of button_A handler
        self.button_7.clicked.connect(self.start_process)
        # self.button_8.clicked.connect(self.pause_process)
        self.button_9.clicked.connect(self.stop_process)
        self.comboBox.currentIndexChanged.connect(self.handle_comboBox_change)
        

         # Add a horizontal scroll bar
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setMinimum(0)
        self.scrollbar.setMaximum(0)  # Initial range
        self.scrollbar.valueChanged.connect(self.scroll_graph)

        layout.addWidget(self.scrollbar)
        self.feed_graph.setLayout(layout)
        # Timer for updating real-time graph
        self.timer = QTimer()
        # self.timer.timeout.connect(self.update_graph)

        # Initialize data storage
        self.time_data = []
        self.force_data = []
        self.csv_file = "force_time_data.csv"


         # Connect signals for comboBox_2
        # self.comboBox.currentIndexChanged.connect(self.set_serial)
        # self.comboBox.currentIndexChanged.connect(self.handle_comboBox_change)
        

        # Set up initial screen
        self.handle_screen_change(1)  # Default to screen 1
    
    def load_comlist(self):
        self.comboBox.clear()
        com_ports_list = []
        com_ports = serial.tools.list_ports.comports()
        for port in com_ports:
            self.comboBox.addItem(f"{port.device}")
        self.showPopup2()

    def populate_com_ports(self):
        """Populate the QComboBox with available COM ports."""
        ports = self.get_com_ports()
        self.comboBox.clear()  # Clear any existing entries
        self.comboBox.addItems(ports)

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
        self.comboBox.setDisabled(True)
        self.comboBox.hide()
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
        # self.is_paused = False
        self.combBox.setDisabled(False)
        self.comboBox.show()
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
            # Ensure the MCU COM port is selected
            comPort = self.comboBox.currentText()
            if not comPort:
                QMessageBox.warning(self, 'Error', 'Please select a COM port for MCU.')
                return

            # Open the selected COM port if not already open
            if not self.ser or not self.ser.is_open or self.ser.port != comPort:
                self.ser = serial.Serial(port=comPort, baudrate=9600, timeout=1)
                print(f"MCU serial port opened: {self.ser.port}")

            # Wait for the "START" command from the MCU
            print("Waiting for START command from MCU...")
            while True:
                if self.ser.in_waiting > 0:
                    received_data = self.ser.readline().decode('utf-8').strip()
                    print(f"Data received from MCU: {received_data}")
                    if received_data == "START":
                        print("Start command received from MCU.")
                        break

            # Initialize the graph and data structures
            self.force_data = []
            self.time_data = []
            self.t = 0

            # Set up the graph layout if not already initialized
            if self.feed_graph.layout() is None:
                print("Creating layout for real-time graph.")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)
                self.feed_graph.setLayout(layout)

            # Configure the graph
            self.ax.set(xlabel='Time (s)', ylabel='Force (N)', title='Real-Time Force vs Time')
            self.ax.grid()
            self.line, = self.ax.plot([], [], color='blue', label='Force')
            self.ax.legend()
            self.canvas.draw()

            # Set mode to processing and update UI
            self.label_38.setText("PROCESSING")
            self.button_7.setText("START")
            self.button_7.setDisabled(True)

            # Start a timer to fetch and plot data from MCU
            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_graph_from_mcu)
                self.update_timer.start(100)  # Update graph every 100 ms

        except Exception as e:
            QMessageBox.critical(self, 'Error', f"An error occurred: {e}")
            print(f"Error: {e}")

    def update_graph_from_mcu(self):
        """Fetch and plot real-time data from the MCU."""
        try:
            if self.ser and self.ser.is_open:
                # Read a line of data from the MCU
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    # Parse the data assuming it is sent as "force,time"
                    try:
                        force, time_value = map(float, line.split(','))
                        self.force_data.append(force)
                        self.time_data.append(time_value)

                        # Update the graph with new data
                        self.line.set_xdata(self.time_data)
                        self.line.set_ydata(self.force_data)
                        self.ax.relim()
                        self.ax.autoscale_view()
                        self.canvas.draw()
                    except ValueError:
                        print(f"Invalid data format received: {line}")
        except Exception as e:
            print(f"Error while reading data: {e}")

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
    
    def stop_process(self):
        """Stop the real-time graph and reset data."""
        # Stop the timer to stop graph updates
        self.timer.stop()
        
        # Clear the data lists
        self.time_data.clear()
        self.force_data.clear()

        # Reset the graph
        self.ax.clear()
        self.ax.set(xlabel='Time (min)', ylabel='Force')
        self.ax.grid()
        self.canvas.draw()

        # Update the button text (if needed)
        self.button_7.setText("Pause")  # Reset pause button to "Pause"
        self.is_paused = False  # Ensure graph is not paused after stopping

        print("Graph stopped and data cleared.")

    def scroll_graph(self, value):
        """Adjust the graph view based on scrollbar value."""
        range_width = 10  # Define the width of the visible range
        start = value
        end = value + range_width
        self.ax.set_xlim(start, end)
        self.canvas.draw()

    def rx_data(self):
        """Receive and process data from the MCU."""
        feedback = None  # Initialize feedback variable
        try:
            # Ensure the serial connection is open
            if self.ser and self.ser.is_open:
                # Check if data is available in the serial buffer
                if self.ser.in_waiting > 0:
                    my_data = self.read_until_delimiter(self.ser)
                    print(f"Data received from MCU: {my_data}")

                    # Ensure there is sufficient data for processing
                    if len(my_data) > 8:
                        # Start Command Condition
                        if my_data[4] == 0x20 and my_data[5] == 0x00 and my_data[8] == 0x00:
                            print("Start command received from MCU.")
                            self.start_real_time_plotting()  # Call the function to start real-time plotting

                        # Stop Command Condition
                        elif my_data[4] == 0x20 and my_data[5] == 0x00 and my_data[8] == 0x01:
                            print("Stop command received from MCU.")
                            self.stop_real_time_plotting()  # Call the function to stop real-time plotting

                        # Process Force Data (assuming force is in bytes 6 and 7)
                        if len(my_data) > 7:
                            high_byte = my_data[6]
                            low_byte = my_data[7]
                            force_value = (high_byte << 8) | low_byte  # Combine bytes to calculate force
                            print(f"Force value received: {force_value}")

                            # Store or process the force data as needed
                            self.force_data.append(force_value)  # Append force value to the data list
                            self.update_graph_with_force(force_value)  # Update the graph in real-time

                    # Store feedback data for further use
                    feedback = my_data

        except serial.SerialException as e:
            print(f"SerialException: {e}")
        except Exception as e:
            print(f"Error during data reception: {e}")

        return feedback  # Return the feedback data

    
    def start_real_time_plotting(self):
        """Start the real-time graph plotting."""
        self.is_plotting = True
        self.start_time = time.time()  # Capture the start time
        print("Real-time plotting started")
        self.force_data.clear()  # Clear previous data
        self.time_data.clear()  # Clear previous time data

        # You can initialize the timer here to update the plot every second (or as per your need)
        self.timer_process.start(1000)  # Example: Start a timer to update the graph every 1 second

    def stop_real_time_plotting(self):
        """Stop the real-time graph plotting."""
        self.is_plotting = False
        print("Real-time plotting stopped")
        if self.timer_process:
            self.timer_process.stop()  # Stop the timer for real-time updates


    # def update_graph(self):
    #     """Update the graph with real-time data."""
    #     if len(self.time_data) > 0:
    #         # Update plot data
    #         self.line.set_data(self.time_data, self.force_data)
    #         self.ax.relim()
    #         self.ax.autoscale_view()

    #         # Update scrollbar range
    #         max_time = self.time_data[-1]
    #         self.scrollbar.setMaximum(max(0, max_time - 10))  # Adjust scrollbar range

    #         # Redraw canvas
    #         self.canvas.draw()

    #         # Store the updated data in CSV file
    #         self.store_real_time_data(self.entered_name + "_data_log.csv")

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

    def load_comlist(self):
        self.comboBox.clear()  # Clear the previous list
        com_ports = serial.tools.list_ports.comports()
        for port in com_ports:
            self.comboBox.addItem(f"{port.device}")
        self.showPopup2()  # If this is a custom popup method

    

    def handle_comboBox_change(self):
        try:
            # Get the selected port from comboBox
            comPort = self.comboBox.currentText()

            # If no port is selected, close any open serial connection and exit
            if comPort == "":
                if self.ser and self.ser.is_open:
                    self.ser.close()
                    print("Serial port closed.")
                self.label_status.setText("No port selected.")
                return

            # Open the selected port if not already open
            if self.ser is None or not self.ser.is_open or self.ser.port != comPort:
                if self.ser and self.ser.is_open:
                    self.ser.close()  # Close any previously open port

                self.ser = serial.Serial(port=comPort, baudrate=9600, timeout=1)
                print(f"Serial port opened: {comPort}")
                self.label_status.setText("Waiting for MCU data...")

                # Start a QTimer to continuously read and plot data
                self.data_timer = QTimer()
                self.data_timer.timeout.connect(self.read_and_plot_data)
                self.data_timer.start(100)  # Read data every 100 ms

        except Exception as e:
            # Handle exceptions and display an error message
            self.label_status.setText(f"Error: {e}")

    def read_and_plot_data(self):
        try:
            if self.ser and self.ser.is_open:
                # Read a line of data from the serial port
                line = self.ser.readline().decode('utf-8').strip()
                
                # Check if the line contains valid data
                if line:
                    # Parse the data assuming it is sent as "force,time"
                    try:
                        force, time_value = map(float, line.split(','))
                        self.force_data.append(force)
                        self.time_data.append(time_value)

                        # Update the real-time graph
                        self.ax.clear()
                        self.ax.plot(self.time_data, self.force_data, label="Force vs Time")
                        self.ax.set_xlabel("Time (s)")
                        self.ax.set_ylabel("Force (N)")
                        self.ax.legend()
                        self.canvas.draw()
                    except ValueError:
                        print("Invalid data format received:", line)
        except Exception as e:
            print(f"Error reading data: {e}")


    def check_ports_and_error(self):
        try:
            # Check if the selected MCU port is the same as the power supply port (assuming you have another serial object for the power supply)
            if self.comboBox.currentText() == "" or self.comboBox.currentText() == "":
                self.label_12.setText("")  # Clear error messages if either port is empty
                self.label_9.setText("")
                return  # Exit the method as there's no conflict

            # Ensure the selected ports for power supply and MCU are not the same
            if self.ser and self.ser.port == self.power_supply_ser.port:
                self.label_12.setText("Port Error")
                self.label_9.setText("Port Error")

                if self.ser.is_open:
                    self.ser.close()
            else:
                self.label_12.setText("")  # Clear the error if there is no conflict
                self.label_9.setText("")

        except Exception as e:
            print(f"Error checking ports: {e}")
            self.label_12.setText("Error checking ports")
            self.label_9.setText("Error checking ports")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
