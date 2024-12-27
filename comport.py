import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, QDateTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize UI components
        #self.initUI()

        # Variables to store frequency, amplitude, and time
        self.frequency = 1  # Default frequency
        self.amplitude = 1  # Default amplitude
        self.t = 0  # Time variable
        self.time_data = []  # List to store time data
        self.pressure_data = []  # List to store sine wave data

        # Create figure for plotting
        self.fig, self.ax = plt.subplots(figsize=(4.25, 4.125), dpi=80)
        self.canvas = FigureCanvas(self.fig)
        self.ax.set(xlabel='Time (s)', ylabel='Amplitude', xlim=(0, 25), ylim=(-2, 2))
        self.ax.grid()
        self.line, = self.ax.plot([], [], color=(0, 0.5, 0.5))

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(QLabel('Frequency (Hz):', self))
        self.freq_input = QLineEdit(self)
        self.freq_input.setText("1")  # Default value
        layout.addWidget(self.freq_input)
        layout.addWidget(QLabel('Amplitude:', self))
        self.amp_input = QLineEdit(self)
        self.amp_input.setText("1")  # Default value
        layout.addWidget(self.amp_input)
        
        self.start_btn = QPushButton('Start Plotting', self)
        self.start_btn.clicked.connect(self.start_process)
        layout.addWidget(self.start_btn)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer to update the plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_plot)

    def start_process(self):
        self.t = 0  # Reset time variable
        self.time_data.clear()  # Clear previous data
        self.pressure_data.clear()  # Clear previous data
        self.timer.start(100)  # Update every 100 ms

    def display_plot(self):
        self.t += 0.1  # Increment time (0.1 seconds)
        
        # Get frequency and amplitude from input
        frequency = float(self.freq_input.text())
        amplitude = float(self.amp_input.text())

        # Generate sine wave data
        y_data = amplitude * np.sin(frequency * self.t)

        # Append the current time and y data
        self.time_data.append(self.t)
        self.pressure_data.append(y_data)

        # Limit to last 25 data points for plotting
        if len(self.time_data) > 25:
            t_data = self.time_data[-25:]
            p_data = self.pressure_data[-25:]        
            self.line.set_data(t_data, p_data)
        else:
            self.line.set_data(self.time_data, self.pressure_data)

        # Update the axes and redraw the canvas
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Sine Wave Plotter")
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
