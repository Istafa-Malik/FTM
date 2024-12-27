import matplotlib.pyplot as plt
import numpy as np

def plot_graph(time_data, amplitude_data, sound_count_data):
    plt.figure(figsize=(10, 5))
    
    # Plotting Amplitude (horizontal line)
    constant_amplitude = amplitude_data[0]  # Assuming amplitude is constant
    plt.plot(time_data, [constant_amplitude] * len(time_data), label='Amplitude', color='blue', linewidth=2)

    # Plotting Sound Count (peaks)
    plt.step(time_data, sound_count_data, label='Sound Count', where='post', color='orange')

    # Labels and Title
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.title('Amplitude and Sound Count over Time')
    plt.grid()
    plt.legend()

    # Example data
    time_data = np.arange(0, 10, 1)  # 0 to 9 seconds
    constant_amplitude = 5
    amplitude_data = [constant_amplitude] * len(time_data)  # Constant amplitude
    sound_count_data = [0, 1, 1, 2, 2, 3, 4, 5, 5, 6]  # Example sound count data

    plot_graph(time_data, amplitude_data, sound_count_data)

    plt.show()

