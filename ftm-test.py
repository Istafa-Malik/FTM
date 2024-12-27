import sys
import csv
import time
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QFileDialog, QScrollBar, QHBoxLayout, QDialog
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class RealTimeGraph(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

        # Initialize data
        self.force_data = []
        self.time_data = []
        self.start_time = time.time()
        self.is_paused = False
        self.max_display_time = 10  # Display range in seconds

        # Timer for real-time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph_data)
        self.timer.start(100)  # Update every 100ms

    def initUI(self):
        self.setWindowTitle("Real-Time Force-Time Graph")

        # Set up layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)

        # Add Matplotlib canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Force vs. Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Force (N)")
        self.ax.grid(True)

        main_layout.addWidget(self.canvas)

        # Add horizontal scrollbar
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setMinimum(0)
        self.scrollbar.valueChanged.connect(self.update_graph_scroll)
        main_layout.addWidget(self.scrollbar)

        # Add buttons
        button_layout = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_button)

        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Previous Data")
        self.load_button.clicked.connect(self.load_previous_data)
        button_layout.addWidget(self.load_button)

        main_layout.addLayout(button_layout)

    def update_graph_data(self):
        if not self.is_paused:
            elapsed_time = time.time() - self.start_time
            force = np.random.uniform(0, 10)  # Replace with real sensor data

            # Append data
            self.time_data.append(elapsed_time)
            self.force_data.append(force)

            # Update graph
            self.update_graph()

    def update_graph(self):
        self.ax.clear()
        self.ax.set_title("Force vs. Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Force (N)")
        self.ax.grid(True)

        # Determine display range
        max_time = max(self.time_data) if self.time_data else 0
        self.scrollbar.setMaximum(int(max_time) - self.max_display_time)
        scrollbar_value = self.scrollbar.value()
        start_time = scrollbar_value
        end_time = start_time + self.max_display_time

        # Plot data within range
        self.ax.plot(self.time_data, self.force_data, label="Real-Time Data", color="blue")
        self.ax.set_xlim(start_time, end_time)
        self.ax.legend()

        self.canvas.draw()

    def update_graph_scroll(self):
        if self.is_paused or self.scrollbar.isSliderDown():
            self.update_graph()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.setText("Resume" if self.is_paused else "Pause")

    def save_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data", "force_time_data.csv", "CSV Files (*.csv)")
        if file_name:
            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Time (s)", "Force (N)"])
                writer.writerows(zip(self.time_data, self.force_data))
            print(f"Data saved to {file_name}")

    def load_previous_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Data", "", "CSV Files (*.csv)")
        if file_name:
            data = pd.read_csv(file_name)
            time_data = data["Time (s)"].tolist()
            force_data = data["Force (N)"].tolist()

            # Display the saved data in a new dialog
            self.show_saved_data_graph(time_data, force_data)

    def show_saved_data_graph(self, time_data, force_data):
        dialog = QDialog(self)
        dialog.setWindowTitle("Saved Data Graph")

        # Set up layout
        layout = QVBoxLayout(dialog)

        # Add Matplotlib canvas
        figure = Figure()
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        ax.set_title("Saved Force vs. Time Data")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Force (N)")
        ax.grid(True)

        # Plot the data
        ax.plot(time_data, force_data, label="Saved Data", color="green")
        ax.legend()

        layout.addWidget(canvas)
        dialog.setLayout(layout)
        dialog.resize(800, 600)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RealTimeGraph()
    window.show()
    sys.exit(app.exec_())
