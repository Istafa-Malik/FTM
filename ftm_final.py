import sys
import csv
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer
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

        # Connect buttons to their respective handlers
        self.button_2.clicked.connect(lambda: self.handle_screen_change(2))
        self.button_3.clicked.connect(lambda: self.handle_screen_change(3))
        self.button_4.clicked.connect(self.close)
        self.button_20.clicked.connect(self.load_csv_data)
        self.button_A.clicked.connect(self.handle_back_pressed)  # Example of button_A handler
        self.button_7.clicked.connect(self.start_process)
        # self.button_8.clicked.connect(self.pause_process)
        self.button_9.clicked.connect(self.stop_process)

         # Add a horizontal scroll bar
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setMinimum(0)
        self.scrollbar.setMaximum(0)  # Initial range
        self.scrollbar.valueChanged.connect(self.scroll_graph)

        layout.addWidget(self.scrollbar)
        self.feed_graph.setLayout(layout)
        # Timer for updating real-time graph
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

        # Initialize data storage
        self.time_data = []
        self.force_data = []
        self.csv_file = "force_time_data.csv"


         # Connect signals for comboBox_2
        # self.comboBox.currentIndexChanged.connect(self.set_serial)
        self.comboBox.currentIndexChanged.connect(self.handle_comboBox_change)
        

        # Set up initial screen
        self.handle_screen_change(1)  # Default to screen 1
    


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
            # Ensure the MCU COM port is selected and open
            comPort2 = self.comboBox.currentText()
            if not comPort2:
                QMessageBox.warning(self, 'Error', 'Please select a COM port for MCU.')
                return

            if not self.ser or not self.ser.is_open or self.ser.port != comPort2:
                self.ser = serial.Serial(port=comPort2, baudrate=9600, timeout=1)
                print(f"MCU serial port opened: {self.ser.port}")

            # Wait for the "START" command from the MCU
            while True:
                if self.ser_2.in_waiting > 0:
                    received_data = self.ser_2.readline().decode('utf-8').strip()
                    print(f"Data received from MCU: {received_data}")
                    if received_data == "START":
                        print("Start command received from MCU.")
                        break

            # Resume process if paused
            if self.mode == "PAUSED":
                self.button_7.setText("RESUME")
                self.button_7.setDisabled(True)
                print("Resuming process.")
                self.timer.start(1)
                self.timer_process.start(1000)
                if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                    self.update_timer = QTimer()
                    self.update_timer.timeout.connect(self.update_graph)
                    self.update_timer.start(1000)
                return

            # Initialize process for the first time
            self.timer.start(1)
            self.label_38.setText("PROCESSING")

            # Ensure force and time are dynamically received from MCU
            self.force_data = []
            self.time_data = []
            self.t = 0

            # Initialize or create the graph layout
            if self.feed_graph.layout() is None:
                print("Creating new layout for real-time graph.")
                self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
                self.canvas = FigureCanvas(self.fig)
                layout = QVBoxLayout()
                layout.addWidget(self.canvas)
                self.feed_graph.setLayout(layout)

            # Set up the graph
            self.ax.set(xlabel='Time (s)', ylabel='Force (N)', title='Real-Time Force vs Time')
            self.ax.grid()
            self.line, = self.ax.plot([], [], color='blue', label='Force')
            self.ax.legend()
            self.canvas.draw()

            # Start a timer to fetch and plot data from MCU
            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_graph_from_mcu)
                self.update_timer.start(1000)  # Update graph every second

            # Initialize CSV for data storage
            entered_name = self.input_8.text().strip()
            if not entered_name:
                QMessageBox.warning(self, 'Error', 'Please enter a file name.')
                return

            self.entered_name = entered_name
            csv_file = f'{entered_name}_data_log.csv'
            self.label_56.setText(entered_name)
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, mode='a', newline='') as file:
                fieldnames = ['Time', 'Force']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()

            # Store data to the CSV in real-time
            self.store_real_time_data(csv_file)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f"An error occurred: {e}")
            print(f"Error: {e}")


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
                    
                    # Check if the received data matches the Start or Stop condition
                    if len(my_data) > 8:  # Ensure there is enough data to check the pattern
                        # Start Command Condition (buffer[4]=0x20, buffer[5]=0x00, buffer[8]=0x00)
                        if my_data[4] == 0x20 and my_data[5] == 0x00 and my_data[8] == 0x00:
                            print("Start command received from MCU")
                            self.start_real_time_plotting()  # Start real-time plotting function
                            
                        # Stop Command Condition (buffer[4]=0x20, buffer[5]=0x00, buffer[8]=0x01)
                        elif my_data[4] == 0x20 and my_data[5] == 0x00 and my_data[8] == 0x01:
                            print("Stop command received from MCU")
                            self.stop_real_time_plotting()  # Stop real-time plotting function

                        # Process force data (assuming values are in my_data[6] and my_data[7])
                        if len(my_data) > 7:
                            high_byte = my_data[6]
                            low_byte = my_data[7]
                            force_value = (high_byte << 8) | low_byte  # Combine high and low byte to get the value
                            print(f"Force value received: {force_value}")

                            # Optionally, store or process the force data as needed
                            self.rx_pressure = force_value  # Assuming pressure is used as force for this example

                    # Store feedback data from MCU
                    feedback = my_data

                    # Call the data processing function (optional, depending on your structure)
                    self.process_received_data(my_data, port='mcu')

        except serial.SerialException as e:
            print(f"SerialException: {e}")
        except Exception as e:
            print(f"Error during data reception: {e}")

        return feedback  # Return the received feedback
    
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

            # Redraw canvas
            self.canvas.draw()

            # Store the updated data in CSV file
            self.store_real_time_data(self.entered_name + "_data_log.csv")

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
