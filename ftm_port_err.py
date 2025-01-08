import serial
import time

def read_from_mcu(port):
    try:
        with serial.Serial(port, baudrate=115200, timeout=1) as ser:
            print(f"Connected to {port}")
            time.sleep(2)  # Wait for the connection to establish
            buffer = bytearray(24)  # Adjust size as needed
            collecting_data = False  # Flag to indicate if we are collecting data

            while True:
                if ser.in_waiting > 0:  # Check if there is data to read
                    data = ser.read(ser.in_waiting)  # Read all available data
                    buffer[:len(data)] = data  # Store data in buffer

                    # Print the raw incoming data in hexadecimal format
                    print("Raw Data Received:", ' '.join(f'{byte:02X}' for byte in data))

                    # Check for start command
                    if len(buffer) >= 9 and buffer[4] == 0X30 and buffer[5] == 0x00 and buffer[8] == 0x00:
                        high_byte = buffer[6]
                        low_byte = buffer[7]
                        value = (high_byte << 8) | low_byte  # Combine high and low byte
                        print("Start Command Received. Values:", value)
                        collecting_data = True  # Start collecting data

                    # Check for stop command
                    elif len(buffer) >= 9 and buffer[4] == 0x30 and buffer[5] == 0x00 and buffer[8] == 0x01:
                        print("Stop Command Received. Stopping data collection.")
                        collecting_data = False  # Stop collecting data
                        break  # Exit the loop to stop receiving data

                    # If collecting data, print the received data in hexadecimal format
                    if collecting_data:
                        print("Collected Data:", ' '.join(f'{byte:02X}' for byte in buffer))

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    port = 'COM4'  # Replace with your actual port
    read_from_mcu(port)