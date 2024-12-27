import sys
import csv
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize
from PyQt5.uic import loadUi

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Load UI file - Make sure this path is correct
        try:
            uic.loadUi('ui_cttm.ui', self)
        except Exception as e:
            print(f"Error loading .ui file: {e}")
            sys.exit(1)

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
        self.button_8.clicked.connect(self.pause_process)
        self.button_9.clicked.connect(self.stop_process)


        # Timer for updating real-time graph
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

        # Initialize data storage
        self.time_data = []
        self.force_data = []
        self.csv_file = "force_time_data.csv"

        # Set up initial screen
        self.handle_screen_change(1)  # Default to screen 1

    def handle_screen_change(self, value):
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

        elif(value == 3): # static graph screen
            self.screen = 3
            self.comboBox.show()
            self.comboBox.setDisabled(False)
            self.init_screen_3()
    
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

    def init_screen_1(self):
        """Initialize the first screen (e.g., main menu)."""
        layout = QVBoxLayout()
        button_2 = QPushButton("Go to Screen 2")
        button_3 = QPushButton("Go to Screen 3")
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
    
    def start_process(self):
        """Start or resume the process of plotting and storing real-time data."""
        if self.mode == "PAUSED":
            self.button_7.setText("RESUME")
            self.button_7.setDisabled(True)
            print("Resuming process.")
            
            # Restart timers for real-time updates
            self.timer.start(1)
            self.timer_process.start(1000)

            # Start a timer to update the graph in real-time
            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_graph)  # Update the graph
                self.update_timer.start(1000)  # Update every second

            return

        # Initialize for the first time if not paused
        self.timer.start(1)

        try:
            # Force and time values can come from labels or be dynamically entered
            self.force = float(self.label_30.text())  # Assuming label_30 holds the force value
            self.time_duration = float(self.label_31.text())  # Assuming label_31 holds the time duration
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

        # Display entered name on the label
        self.label_56.setText(entered_name)

        # Initialize data list
        self.data = []
        self.max_limit = 100  # Limit for CSV entries

        # Check if the file exists and create/write to it
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            fieldnames = ['Time', 'Force']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

        # Start the sound timer for continuous process tracking
        self.sound_timer.start(1000)
        self.timer2.start()

        # Start the main process timer
        self.process_start_time = QDateTime.currentDateTime()
        self.timer_process.start(1000)

        if self.mode == "READY":
            self.label_38.setText("PROCESSING")

            # Check if feed_graph layout exists; create if not
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

            # Set graph labels and grid
            self.ax.set(xlabel='Time (s)', ylabel='Force (N)')
            self.ax.grid()

            # Initialize the plot line for real-time graph
            self.line, = self.ax.plot([], [], color='blue', label='Force')
            self.t = 0
            self.time_data = []  # Real-time time data
            self.force_data = []  # Real-time force data

            # Draw the initial empty canvas
            self.canvas.draw()

        # Start a timer to continuously update the graph with real-time data
        if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_graph)
            self.update_timer.start(1000)  # Update graph every second

        # Store real-time data into the CSV file
        self.store_real_time_data(csv_file)
        self.display_plot()
    def pause_process(self):
        """Handle the pause/resume action for the real-time graph."""
        if self.is_paused:
            # Resume the graph by starting the timer again
            self.timer.start(1000)  # Update every second (or your preferred interval)
            self.button_7.setText("Pause")  # Change button text to "Pause"
            self.is_paused = False
        else:
            # Pause the graph by stopping the timer
            self.timer.stop()
            self.button_7.setText("Resume")  # Change button text to "Resume"
            self.is_paused = True
    
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
    def update_graph(self):
        """Update the graph with real-time force and time data."""
        # Increment time and force values
        self.t += 1  # Increase time by 1 second or adjust based on your data
        self.time_data.append(self.t)
        self.force_data.append(self.force)  # Update with real-time force data

        # Update the plot with new data
        self.line.set_xdata(self.time_data)
        self.line.set_ydata(self.force_data)

        # Adjust graph limits if data grows beyond the current axis
        self.ax.relim()
        self.ax.autoscale_view()

        # Redraw the canvas
        self.canvas.draw()

        # Update the horizontal scroll bar to match the data length
        self.scrollbar.setMaximum(len(self.time_data))

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
